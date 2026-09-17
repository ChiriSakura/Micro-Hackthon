// Verilator testbench：用**真实的**逐 tile 行工作量，量出 PE 利用率随
// 队列深度怎么变。
//
// ## 它要替换掉的东西
//
// `fast/agents/codesign.py` 的 `pe_utilisation()`：
//
//     utilisation = 1 / (1 + (imbalance - 1) / (1 + queue_depth))
//
// 那是个一阶模型，函数注释自己写着「It is a model, not a measurement」。
// 而 `queue_depth` 是协同优化器的搜索维度。这个 bench 出来的数取代它。
//
// ## 判据是什么，不是什么
//
// 这里**不验证数据通路正确性**——那是 tb_attention_tile 的事，那边拿真实
// Q/K/V 和 PyTorch 对过。这里测的是**占用率**：每拍有几行在干活。所以列
// 索引本身随便填，行的忙闲才是被测量。
//
// 但有两个结构性判据必须过，否则测量本身是错的：
//
//   1. **总工作量守恒**：硬件计数器数出来的「PE·拍」忙碌数，必须精确等于
//      输入里保留列的总数。对不上就说明有工作被丢了或被重复发了，那么利用
//      率再好看也没意义。
//   2. **queue_depth=0 时利用率 ≈ 1/imbalance**。这是模型在 0 处的解析极限，
//      也是「严格锁步」的定义。硬件在这里对不上，说明队列语义和模型说的
//      不是同一件事，后面所有深度的数都不能拿去和模型比。
//
// ## 生产者策略
//
// 每行的工作按 tile 顺序入队，每拍每行最多入一趟，队列满就卡住——这就是
// 队列深度限制领先量的机制本身。消费侧每拍无条件发射（阵列一直准备好收）。
//
// 用法：tb_block_scheduler <workload.txt>
//   第一行： numRows peCountPerRow tileCount
//   之后每行： numRows 个整数，某个 tile 里各行的保留列数

#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <vector>

#include "VBlockScheduler.h"
#include "verilated.h"

// gen_ports.py 生成：kNumRows/kPeCount/kQueueDepth 和 enq_* 的下标访问。
// Chisel 把 Vec 展平成独立端口，32x4 就是 256 个 enq_cols。
#include "array_ports.h"

namespace {

struct Workload {
    int rows = 0;
    int pe = 0;
    std::vector<std::vector<int>> tiles;  // [tile][row] = 保留列数
};

Workload load(const char* path) {
    Workload w;
    FILE* f = std::fopen(path, "r");
    if (!f) { std::fprintf(stderr, "打不开 %s\n", path); std::exit(2); }
    int tileCount = 0;
    if (std::fscanf(f, "%d %d %d", &w.rows, &w.pe, &tileCount) != 3) {
        std::fprintf(stderr, "%s 的头部格式不对\n", path); std::exit(2);
    }
    w.tiles.resize(tileCount);
    for (int t = 0; t < tileCount; t++) {
        w.tiles[t].resize(w.rows);
        for (int r = 0; r < w.rows; r++) {
            if (std::fscanf(f, "%d", &w.tiles[t][r]) != 1) {
                std::fprintf(stderr, "%s 在 tile %d row %d 处截断\n", path, t, r);
                std::exit(2);
            }
        }
    }
    std::fclose(f);
    return w;
}

// 一行在一个 tile 里要几趟。最后一趟可能有空槽——空槽的 PE 空转，
// 要算进利用率损失，所以不能向下取整。
int passesFor(int kept, int pe) { return (kept + pe - 1) / pe; }

}  // namespace

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    if (argc < 2) { std::fprintf(stderr, "用法: %s <workload.txt>\n", argv[0]); return 2; }
    const Workload w = load(argv[1]);

    if (w.rows != kNumRows || w.pe != kPeCount) {
        std::fprintf(stderr,
            "工作量文件是 %dx%d，但 DUT 是 %dx%d——尺寸不匹配时测出来的利用率\n"
            "反映的是补零/截断，不是队列深度\n",
            w.rows, w.pe, kNumRows, kPeCount);
        return 2;
    }

    auto* dut = new VBlockScheduler;

    dut->reset = 1;
    dut->io_issue_en = 0;
    dut->io_perf_clear = 0;
    for (int r = 0; r < kNumRows; r++) { set_enq_valid(dut, r, 0); set_enq_last(dut, r, 0); }
    for (int i = 0; i < 8; i++) { dut->clock = 0; dut->eval(); dut->clock = 1; dut->eval(); }
    dut->reset = 0;
    dut->io_perf_clear = 1;
    dut->clock = 0; dut->eval(); dut->clock = 1; dut->eval();
    dut->io_perf_clear = 0;
    dut->io_issue_en = 1;

    // 每行的待入队工作：把所有 tile 展开成一串「趟」。
    std::vector<std::vector<int>> pending(kNumRows);   // 每趟的 active 槽数
    std::vector<std::vector<char>> lastOfTile(kNumRows);  // 该趟是不是本 tile 的最后一趟
    long long expected_pe_work = 0;
    for (const auto& tile : w.tiles) {
        for (int r = 0; r < kNumRows; r++) {
            const int kept = tile[r];
            expected_pe_work += kept;
            const int full = kept / w.pe, tail = kept % w.pe;
            const size_t before = pending[r].size();
            for (int p = 0; p < full; p++) { pending[r].push_back(w.pe); lastOfTile[r].push_back(0); }
            if (tail) { pending[r].push_back(tail); lastOfTile[r].push_back(0); }
            // 保留数为 0 的行也要发一趟**空趟**。
            //
            // tileIdx 靠 last 位计数，少发这一趟，它数的就是「本行有活干的
            // 第几个 tile」而不是真实 tile 序号——参与稀疏的行会和其它行
            // 错位，屏障拿两个不同的量相比。topk 上这个 bug 让利用率从
            // 0.609 掉到 0.394（它的空行最多）。
            //
            // 空趟也不是白发的：那一拍那一行本来就在空转，全 inactive 的
            // 趟如实反映了它，而且不算进 row_busy。
            if (pending[r].size() == before) {
                pending[r].push_back(0);
                lastOfTile[r].push_back(0);
            }
            lastOfTile[r].back() = 1;
        }
    }
    std::vector<size_t> cursor(kNumRows, 0);

    // 上限：全部工作串行走完也不会超过这个数，加上排空余量。
    long long total_passes = 0;
    for (const auto& p : pending) total_passes += (long long)p.size();
    const long long max_cycles = total_passes * 4 + 10000;
    // 停下之后空转这么多拍，验证计数器已经静止、drained 已经拉高。
    constexpr int kDrainMargin = 64;

    long long cycle = 0;
    bool done = false;
    bool drained_on_time = false;
    while (!done && cycle < max_cycles) {
        // ---- 组合阶段：按 enq_ready 决定这一拍每行能不能入队 ----
        dut->eval();
        const uint64_t ready = enq_ready_bits(dut);
        bool anyPending = false;
        for (int r = 0; r < kNumRows; r++) {
            const bool has = cursor[r] < pending[r].size();
            anyPending |= has;
            const bool go = has && ((ready >> r) & 1u);
            set_enq_valid(dut, r, go ? 1 : 0);
            if (go) {
                const int active = pending[r][cursor[r]];
                for (int p = 0; p < kPeCount; p++) {
                    set_enq_active(dut, r, p, p < active ? 1 : 0);
                    // 列索引在占用率测量里不参与判据，填 p 只是为了不留 X。
                    set_enq_col(dut, r, p, p);
                }
                set_enq_last(dut, r, lastOfTile[r][cursor[r]] ? 1 : 0);
            }
        }
        dut->eval();

        // 记录实际被接受的入队（enq_ready 是组合的，valid&&ready 才算数）。
        for (int r = 0; r < kNumRows; r++) {
            if (get_enq_valid(dut, r) && ((ready >> r) & 1u)) cursor[r]++;
        }

        const uint32_t expected_row_counter = dut->io_row_cycles_busy +
            (uint32_t)__builtin_popcountll(row_busy_bits(dut));
        const uint32_t expected_cycle_counter = dut->io_cycles_active +
            (dut->io_drained ? 0u : 1u);
        dut->clock = 0; dut->eval();
        dut->clock = 1; dut->eval();
        cycle++;
        if (dut->io_row_cycles_busy != expected_row_counter ||
            dut->io_cycles_active != expected_cycle_counter) {
            std::printf("FAIL counter cycle contract at cycle %lld: row=%u expected=%u "
                        "cycles=%u expected=%u\n", cycle,
                        dut->io_row_cycles_busy, expected_row_counter,
                        dut->io_cycles_active, expected_cycle_counter);
            delete dut;
            return 1;
        }

        // **停止条件不看 DUT 的 `drained`。**
        //
        // 原来是 `!anyPending && dut->io_drained`——于是 DUT 的一个输出信号
        // 控制着「什么时候采计数器」，模块改那个信号就能改判据。实测被这个
        // 洞放行过一次：LLM 把计数器打了一拍，为了让工作守恒仍然成立，顺手
        // 把 `io.drained` 也改成 `RegNext(...)`。它自己写的注释就说了原因。
        // prompt 明写「same cycle-level protocol」，门却接受了。
        //
        // 现在停在**testbench 自己的判据**上：入队全部完成，且硬件数到的
        // PE·拍达到了预期总量。`drained` 降级为一个**被检查的输出**（见下面
        // 的排空余量），它不再决定任何事。
        if (!anyPending && (long long)dut->io_pe_cycles_busy >= expected_pe_work) {
            done = true;
            // **drained 必须在这一拍就已经拉高。**
            //
            // 全部工作都已经计入、也没有待入队的了——队列这时就是空的，
            // 而 `drained` 的定义就是「所有队列都空」。晚一拍拉高说明它
            // 不再是这个组合条件，而是别的东西的延迟版本。
            //
            // 只检查「最后静止时 drained 为高」是不够的：那是**免疫**不是
            // **检测**——延后一拍照样满足。判据必须说清楚是哪一拍。
            drained_on_time = dut->io_drained != 0;
        }
    }

    for (int r = 0; r < kNumRows; r++) set_enq_valid(dut, r, 0);
    dut->eval();

    // ---- 排空余量：停下之后再空转一段，计数器必须稳定，drained 必须拉高 ----
    //
    // 这一段把两件事变成**被测量**而不是**控制量**：还在飞的工作会让计数器
    // 继续动（抓到「提前采样」），而 `drained` 到这时仍不拉高就是它自己错。
    const uint32_t settled_pe = dut->io_pe_cycles_busy;
    const uint32_t settled_row = dut->io_row_cycles_busy;
    const uint32_t settled_cycles = dut->io_cycles_active;
    bool counters_moved = false;
    for (int i = 0; i < kDrainMargin; i++) {
        dut->clock = 0; dut->eval();
        dut->clock = 1; dut->eval();
        if (dut->io_pe_cycles_busy != settled_pe ||
            dut->io_row_cycles_busy != settled_row ||
            dut->io_cycles_active != settled_cycles) {
            counters_moved = true;
        }
    }
    const bool drained_at_rest = dut->io_drained != 0;

    const uint32_t cycles_active = dut->io_cycles_active;
    const uint32_t row_busy = dut->io_row_cycles_busy;
    const uint32_t pe_busy = dut->io_pe_cycles_busy;

    int failures = 0;

    // ---- 判据 0：停下来之后必须真的静止 -----------------------------------
    if (counters_moved) {
        std::printf("FAIL 停止后计数器还在动（空转 %d 拍）——还有工作在飞，"
                    "采样时刻早了\n", kDrainMargin);
        failures++;
    }
    if (!drained_at_rest) {
        std::printf("FAIL 全部工作已计入、空转 %d 拍之后 drained 仍未拉高——"
                    "这个输出自己不对\n", kDrainMargin);
        failures++;
    }
    if (!drained_on_time && !counters_moved) {
        std::printf("FAIL drained 晚拉高了：全部工作计入、队列已空的那一拍它"
                    "还是 0（后来才拉高）。它的定义是「所有队列都空」的组合"
                    "条件，延迟版本改变了模块的周期级契约\n");
        failures++;
    }

    // ---- 判据 1：工作量守恒 ------------------------------------------------
    if ((long long)pe_busy != expected_pe_work) {
        std::printf("FAIL 工作量不守恒：硬件数到 %u 个 PE·拍，输入里有 %lld 个保留列\n",
                    pe_busy, expected_pe_work);
        failures++;
    }
    for (int r = 0; r < kNumRows; r++) {
        if (cursor[r] != pending[r].size()) {
            std::printf("FAIL 行 %d 有 %zu 趟没入队（共 %zu 趟）——仿真提前结束了\n",
                        r, pending[r].size() - cursor[r], pending[r].size());
            failures++;
            break;
        }
    }

    // ---- 测量结果 ----------------------------------------------------------
    const double row_util = cycles_active ? (double)row_busy / ((double)cycles_active * kNumRows) : 0.0;
    const double pe_util = cycles_active ? (double)pe_busy / ((double)cycles_active * kNumRows * kPeCount) : 0.0;

    // 参照：严格锁步下这批工作要花多少拍。
    //
    // **聚合方式必须是「总工作 / 总周期」，不是「每个 tile 的比值再平均」。**
    // 利用率本身就是一个比值之和；比值的平均会给短 tile 和长 tile 同样的
    // 权重，而长 tile 花的周期多得多。两者在实测数据上差 6 个百分点
    // （xm: 0.708 vs 0.666），足以让标定偏到错误的那一侧。
    long long lockstep_cycles = 0, total_passes_work = 0;
    for (const auto& tile : w.tiles) {
        int mx = 0;
        for (int r = 0; r < kNumRows; r++) {
            const int p = passesFor(tile[r], w.pe);
            mx = p > mx ? p : mx; total_passes_work += p;
        }
        lockstep_cycles += mx;
    }
    // 定义成「让 1/imbalance 恰好等于锁步利用率」的那个不均衡度，
    // 这样它和 pe_utilisation() 在 0 处的极限是同一个量。
    const double lockstep_util = lockstep_cycles
        ? (double)total_passes_work / ((double)lockstep_cycles * kNumRows) : 1.0;
    const double imbalance = lockstep_util > 0 ? 1.0 / lockstep_util : 1.0;

    std::printf("queue_depth=%d rows=%d pe=%d tiles=%zu\n",
                kQueueDepth, kNumRows, kPeCount, w.tiles.size());
    std::printf("  cycles_active=%u  row_utilisation=%.4f  pe_utilisation=%.4f\n",
                cycles_active, row_util, pe_util);
    std::printf("  pass_imbalance=%.4f  model_says=%.4f  measured_row=%.4f\n",
                imbalance, 1.0 / (1.0 + (imbalance - 1.0) / (1.0 + kQueueDepth)), row_util);
    // 机器可读的一行，给标定脚本抓。
    std::printf("MEASURE queue_depth=%d rows=%d pe=%d imbalance=%.6f "
                "row_util=%.6f pe_util=%.6f cycles=%u\n",
                kQueueDepth, kNumRows, kPeCount,
                imbalance, row_util, pe_util, cycles_active);

    // ---- 判据 2：深度 0 必须落在 1/imbalance 上 ----------------------------
    //
    // 这是「严格锁步」的定义，也是 pe_utilisation() 在 0 处的解析极限。
    // 硬件在这里对不上，说明队列语义和模型说的不是同一件事——那么后面所有
    // 深度的数都不能拿去和模型比，曲线再漂亮也是在比两个不同的量。
    //
    // 第一版实现正是栽在这里：行做成了完全独立的队列，深度 0 测出 0.921
    // 而不是 1/3.275=0.305，而且从 0 到 16 完全平坦。当时没有这条判据，
    // 那个错误是靠「曲线太平」被察觉的——那属于运气。
    if (kQueueDepth == 0) {
        const double expect = lockstep_util;
        const double err = std::fabs(row_util - expect) / expect;
        if (err > 0.05) {
            std::printf("FAIL 深度 0 的利用率 %.4f 偏离 1/imbalance=%.4f 达 %.1f%%\n"
                        "     （深度 0 应当是严格锁步；对不上说明屏障没起作用）\n",
                        row_util, expect, err * 100.0);
            failures++;
        }
    }

    if (cycle >= max_cycles) {
        std::printf("FAIL 达到周期上限 %lld，队列没排空\n", max_cycles);
        failures++;
    }

    std::printf("%s: %d 处判据失败\n", failures ? "FAILED" : "PASSED", failures);
    delete dut;
    return failures ? 1 : 0;
}

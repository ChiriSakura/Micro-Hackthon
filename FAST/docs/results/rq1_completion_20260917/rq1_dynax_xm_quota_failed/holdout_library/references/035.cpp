// Verilator testbench：真实稀疏索引流下的 bank 冲突代价。
//
// ## 它测的是周期模型里完全缺失的那一项
//
// `fast/agents/codesign.py` 的周期公式是
//
//     cycles = sparse_macs / (lanes * utilisation)
//
// **一项和访存有关的都没有**——等于假设带宽无限。于是 `sram_bytes`、
// `double_buffer`、bank 数这些维度对周期数的影响是零。
//
// 而带宽缺口是结构性的：`repe_row.scala:62` 每拍无条件 `reg_cols := regs_top`，
// 所以阵列每拍要 regWidth 个新 K 标量（DynaX-S 是 128 位/拍），上游的 SRAM
// 是单地址端口、每拍 64 位。
//
// ## 为什么必须用真实索引，不能用随机数
//
// 冲突率取决于索引的**分布**，不是保留的**个数**。实测的索引长这样：
//
//     xm      [0, 33,34,35,36, 38,39,40,41,42,43,44]   聚簇
//     topk    全局取大，分散
//
// `bank = col % bankCount` 下，连续索引完美散开而分散索引会撞。同样的稀疏
// 度，两者的冲突代价可以差很多倍。均匀随机数测出来的是「随机分布下的冲突
// 率」，那个数不对应任何真实工作负载。
//
// ## 三条判据
//
// 前两条是**测量自身**的正确性，不是被测对象的：
//
//   1. **取回的数据必须等于写进去的**。取数引擎可以在冲突时慢，但不能取错。
//      这一条一挂，后面的冲突计数就没有意义了——它数的是一个坏掉的东西。
//   2. **无冲突下界**：regWidth 个请求分散在 >= regWidth 个 bank 上时，
//      每组必须正好 2 拍（一拍发地址 + SyncReadMem 一拍延迟）。对不上说明
//      引擎本身有多余的握手开销，那个开销会被误记成冲突代价。
//   3. 冲突拍数 = 实际拍数 - 2*组数，且非负。
//
// 用法：tb_key_feeder <stimulus.txt>
//   第一行： regWidth bankCount totalCols groupCount
//   之后每行： regWidth 个列索引（-1 表示该槽不用）

#include <cstdio>
#include <cstdlib>
#include <vector>

#include "VKeyFeeder.h"
#include "verilated.h"

#include "array_ports.h"   // gen_ports.py 生成：req_cols/req_active/out_cols 的下标访问

namespace {

struct Stimulus {
    int reg_width = 0;
    int bank_count = 0;
    int total_cols = 0;
    std::vector<std::vector<int>> groups;   // -1 = 该槽不用
};

Stimulus load(const char* path) {
    Stimulus s;
    FILE* f = std::fopen(path, "r");
    if (!f) { std::fprintf(stderr, "打不开 %s\n", path); std::exit(2); }
    int groups = 0;
    if (std::fscanf(f, "%d %d %d %d", &s.reg_width, &s.bank_count,
                    &s.total_cols, &groups) != 4) {
        std::fprintf(stderr, "%s 头部格式不对\n", path); std::exit(2);
    }
    s.groups.resize(groups);
    for (int g = 0; g < groups; g++) {
        s.groups[g].resize(s.reg_width);
        for (int i = 0; i < s.reg_width; i++) {
            if (std::fscanf(f, "%d", &s.groups[g][i]) != 1) {
                std::fprintf(stderr, "%s 在第 %d 组第 %d 槽截断\n", path, g, i);
                std::exit(2);
            }
        }
    }
    std::fclose(f);
    return s;
}

void tick(VKeyFeeder* dut) {
    dut->clock = 0; dut->eval();
    dut->clock = 1; dut->eval();
}

// 写进 SRAM 的值，也是判据 1 的参照。用列号本身当数据，这样取错列会立刻
// 显形——用常数或随机数都会让「取错了但取回来了」看起来像成功。
int expected_for(int col) { return (col * 7 + 3) & 0xFFFF; }

}  // namespace

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    if (argc < 2) { std::fprintf(stderr, "用法: %s <stimulus.txt>\n", argv[0]); return 2; }
    const Stimulus stim = load(argv[1]);

    if (stim.reg_width != kRegWidth || stim.bank_count != kBankCount) {
        std::fprintf(stderr,
            "激励是 regWidth=%d bankCount=%d，DUT 是 %d/%d——尺寸不匹配时\n"
            "测出来的冲突反映的是截断，不是 bank 组织\n",
            stim.reg_width, stim.bank_count, kRegWidth, kBankCount);
        return 2;
    }

    auto* dut = new VKeyFeeder;
    dut->reset = 1;
    dut->io_req_valid = 0; dut->io_wr_en = 0; dut->io_perf_clear = 0;
    for (int i = 0; i < 8; i++) tick(dut);
    dut->reset = 0;

    // ---- 装载：每一列写一个由列号决定的值 ----------------------------------
    for (int col = 0; col < stim.total_cols; col++) {
        dut->io_wr_en = 1;
        dut->io_wr_col = col;
        dut->io_wr_data = expected_for(col);
        tick(dut);
    }
    dut->io_wr_en = 0;
    tick(dut);

    dut->io_perf_clear = 1; tick(dut); dut->io_perf_clear = 0;

    // ---- 服务每一组 --------------------------------------------------------
    int failures = 0;
    int mismatches = 0;
    long long cycles = 0;
    const long long max_cycles = (long long)stim.groups.size() * (stim.reg_width + 8) + 1000;

    for (size_t g = 0; g < stim.groups.size() && cycles < max_cycles; g++) {
        const auto& group = stim.groups[g];

        // 等 ready 再发。ready 低的那些拍就是上一组的冲突代价。
        while (!dut->io_req_ready && cycles < max_cycles) { tick(dut); cycles++; }

        dut->io_req_valid = 1;
        for (int i = 0; i < kRegWidth; i++) {
            const bool active = group[i] >= 0;
            set_req_active(dut, i, active ? 1 : 0);
            set_req_col(dut, i, active ? group[i] : 0);
        }
        tick(dut); cycles++;
        dut->io_req_valid = 0;

        // 等这一组齐。
        int spent = 0;
        while (!dut->io_out_valid && cycles < max_cycles) {
            tick(dut); cycles++; spent++;
        }
        if (!dut->io_out_valid) break;

        // ---- 判据 1：取回的必须是写进去的 ----------------------------------
        for (int i = 0; i < kRegWidth; i++) {
            if (group[i] < 0) continue;
            const int got = out_col(dut, i);
            const int want = expected_for(group[i]);
            if (got != want) {
                if (mismatches < 5) {
                    std::printf("FAIL 第 %zu 组槽 %d：列 %d 取到 0x%04X，应为 0x%04X\n",
                                g, i, group[i], got, want);
                }
                mismatches++;
            }
        }
        tick(dut); cycles++;
    }

    if (mismatches) {
        std::printf("FAIL 共 %d 处取数不符——冲突计数建立在一个坏掉的引擎上，无意义\n",
                    mismatches);
        failures++;
    }
    if (cycles >= max_cycles) {
        std::printf("FAIL 达到周期上限 %lld，还有组没服务完\n", max_cycles);
        failures++;
    }

    const uint32_t served = dut->io_groups_served;
    const uint32_t busy = dut->io_busy_cycles;
    const uint32_t conflict = dut->io_conflict_cycles;

    if (served != stim.groups.size()) {
        std::printf("FAIL 硬件数到 %u 组，激励里有 %zu 组\n", served, stim.groups.size());
        failures++;
    }

    const uint32_t requests = dut->io_requests_served;
    const double cycles_per_group = served ? (double)busy / served : 0.0;
    const double conflict_per_group = served ? (double)conflict / served : 0.0;
    // 无冲突下界：一拍发地址 + SyncReadMem 一拍延迟。
    const double ideal = 2.0;

    // ---- 判据 2：bank 数 >= regWidth 且索引各不相同时，必须打到下界 --------
    //
    // 这条只在激励确实无冲突时才有意义，所以先自己判一遍激励。
    bool conflict_free = kBankCount >= kRegWidth;
    if (conflict_free) {
        for (const auto& group : stim.groups) {
            std::vector<int> seen;
            for (int i = 0; i < kRegWidth && conflict_free; i++) {
                if (group[i] < 0) continue;
                const int bank = group[i] % kBankCount;
                for (int b : seen) if (b == bank) { conflict_free = false; break; }
                seen.push_back(bank);
            }
            if (!conflict_free) break;
        }
    }
    if (conflict_free && conflict_per_group > 0.01) {
        std::printf("FAIL 激励无 bank 冲突，但引擎每组多花 %.3f 拍——\n"
                    "     那是引擎自身的握手开销，会被误记成冲突代价\n",
                    conflict_per_group);
        failures++;
    }

    std::printf("bankCount=%d regWidth=%d groups=%u\n", kBankCount, kRegWidth, served);
    std::printf("  每组 %.3f 拍（无冲突下界 %.1f），其中冲突 %.3f 拍\n",
                cycles_per_group, ideal, conflict_per_group);
    std::printf("  相对下界的减速 %.3fx\n", ideal > 0 ? cycles_per_group / ideal : 0.0);
    // 每个保留列多少个串行步。**这才是能跨方法比较的量**：按组平均会把
    // 「索引散不散得开」和「组填不填得满」混在一起——只有 1 个请求的组必然
    // 零冲突，而 topk 的组大多是空的，它「看起来好」有一半是这个原因。
    //
    // 一个串行步在这个实现里是 2 拍（发地址 + SyncReadMem 延迟），因为它
    // 没有跨步流水。流水化之后每步 1 拍，所以能移植的量是**步数**不是拍数。
    const double steps = ideal > 0 ? (double)busy / ideal : 0.0;
    const double steps_per_request = requests ? steps / requests : 0.0;
    // 理想：regWidth 个请求散在 >= regWidth 个 bank 上，一步全发完。
    const double ideal_steps_per_request = kRegWidth > 0 ? 1.0 / kRegWidth : 1.0;

    std::printf("  %u 个有效请求，每个 %.4f 个串行步（理想 %.4f）-> 存储侧减速 %.3fx\n",
                requests, steps_per_request, ideal_steps_per_request,
                ideal_steps_per_request > 0 ? steps_per_request / ideal_steps_per_request : 0.0);
    std::printf("MEASURE banks=%d reg_width=%d groups=%u requests=%u cycles_per_group=%.6f "
                "conflict_per_group=%.6f slowdown=%.6f steps_per_request=%.6f "
                "mem_slowdown=%.6f\n",
                kBankCount, kRegWidth, served, requests, cycles_per_group, conflict_per_group,
                ideal > 0 ? cycles_per_group / ideal : 0.0, steps_per_request,
                ideal_steps_per_request > 0 ? steps_per_request / ideal_steps_per_request : 0.0);
    std::printf("%s: %d 处判据失败\n", failures ? "FAILED" : "PASSED", failures);

    delete dut;
    return failures ? 1 : 0;
}

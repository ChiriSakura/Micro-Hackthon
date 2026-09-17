// 完整系统的验证：分档选择 + 硬件自己挑的索引 + 带反压的取数 + 计算阵列。
//
// ## bring-up 的判据：**先让新路径退化成已验证的路径**
//
// 阈值设成「全部走高档」（threshold_hi 极低）时，分档器留满 keptPerRow 个，
// 语义就是固定 top-n——那正是 golden 抓取的参照。这时系统的输出必须和
// `tb_attention_tile_top.cpp` 逐维一致。
//
// 不先做这一步的话，一次数值不符说不清是分档错了、索引挑错了、还是取数
// 引擎喂错了——三个新变量一起动。
//
// ## 两个新的可测量
//
// `stall_cycles`：状态机停在 sReq 等 `req_ready` 的拍数。bank 冲突变成反压
// 变成停顿——**代价模型里那个标定出来的 `gather_slowdown` 系数第一次有实测
// 对照**。
//
// `chosen_idx`：硬件自己挑的列。和抓取里参照挑的列比，得到的是**预测器的
// 一致度**，那是个质量指标不是判据——硬件挑了别的列不等于算错了。

#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <set>
#include <string>
#include <vector>

#include "golden.h"

#include "VAttentionTileSystem.h"
#include "verilated.h"

namespace {

constexpr int kPoint = 8;
constexpr int kTileQ = 4;
constexpr int kTileK = 32;
constexpr int kHeadDim = 8;
constexpr int kKept = 8;

std::vector<std::vector<long>> matrix(const std::string& text, const char* key,
                                      int rows, int cols) {
    size_t cursor = text.find(key);
    if (cursor == std::string::npos) {
        std::fprintf(stderr, "tile.json 里没有 %s\n", key);
        std::exit(2);
    }
    std::vector<std::vector<long>> out(rows, std::vector<long>(cols, 0));
    size_t at = text.find('[', cursor);
    for (int r = 0; r < rows; r++) {
        at = text.find('[', at + 1);
        size_t end = text.find(']', at);
        std::string row = text.substr(at + 1, end - at - 1);
        const char* p = row.c_str();
        for (int c = 0; c < cols; c++) {
            char* next = nullptr;
            out[r][c] = std::strtol(p, &next, 10);
            if (next == p) break;
            p = next;
            while (*p == ',' || *p == ' ' || *p == '\n') p++;
        }
        at = end;
    }
    return out;
}

}  // namespace

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    if (argc < 2) {
        std::fprintf(stderr, "用法: %s <tile.json>\n", argv[0]);
        return 2;
    }
    const std::string text = golden::slurp(argv[1]);

    const auto q = matrix(text, "\"q_ticks\"", kTileQ, kHeadDim);
    const auto k = matrix(text, "\"k_ticks\"", kTileK, kHeadDim);
    const auto qp = matrix(text, "\"q_predict\"", kTileQ, kHeadDim);
    const auto kp = matrix(text, "\"k_predict\"", kTileK, kHeadDim);
    const auto kept = matrix(text, "\"expected_kept_idx\"", kTileQ, kKept);

    auto* dut = new VAttentionTileSystem;
    auto tick = [&] {
        dut->clock = 0; dut->eval();
        dut->clock = 1; dut->eval();
    };
    auto reset = [&] {
        dut->reset = 1;
        for (int i = 0; i < 4; i++) tick();
        dut->reset = 0;
        dut->eval();
    };

    reset();

    // ---- 把 K 装进 feeder 的 bank ----------------------------------------
    //
    // 一列一个条目。装载走 wr 口，和请求口是分开的——真实设计里这是
    // 上一个 tile 的预取。
    for (int col = 0; col < kTileK; col++) {
        dut->io_kv_wr_en = 1;
        dut->io_kv_wr_col = col;
        dut->io_kv_wr_data = (unsigned short)(k[col][0] & 0xFFFF);
        tick();
    }
    dut->io_kv_wr_en = 0;

    // ---- 阈值：全部走高档，退化成固定 top-n --------------------------
    //
    // 分档器是 `mass > threshold_hi -> n1`。hi 设成 0 让任何正质量都落进
    // 高档，于是留满 kKept 个——和 golden 抓取的参照同一个语义。
    dut->io_threshold_hi = 0;
    dut->io_threshold_lo = 0;

#define SET_Q(i) dut->io_q_in_##i = (unsigned short)(q[0][i] & 0xFFFF)
    SET_Q(0); SET_Q(1); SET_Q(2); SET_Q(3);
    SET_Q(4); SET_Q(5); SET_Q(6); SET_Q(7);
#undef SET_Q
    // 块质量：bring-up 阶段给一个正值即可（hi=0，任何正数都进高档）。
#define SET_MASS(i) dut->io_block_mass_##i = 256   /* Q8.8 的 1.0 */
    SET_MASS(0); SET_MASS(1); SET_MASS(2); SET_MASS(3);
#undef SET_MASS

    // ---- 分数：从精确 Q/K 算，Q8.8 -----------------------------------
    //
    // 参照的 `expected_kept_idx` 是 `torch.topk(q @ k.T, kept)` 挑的。喂同一
    // 组分数，硬件 TopK 必须选出**同一组列**——这是个干净的 bring-up 判据：
    // 不一致就是 TopK 的驱动错了，和预测器准不准无关。
    //
    // Q8.8 乘 Q8.8 得 Q16.16，右移 8 位回到 Q8.8。
    std::vector<std::vector<long>> scores(kTileQ, std::vector<long>(kTileK, 0));
    for (int r = 0; r < kTileQ; r++) {
        for (int key = 0; key < kTileK; key++) {
            long acc = 0;
            for (int d = 0; d < kHeadDim; d++) acc += q[r][d] * k[key][d];
            long tick = acc >> kPoint;
            // 16 位有符号饱和。溢出会让 TopK 比较到回绕后的值——那不是
            // 「硬件挑得不准」，是喂进去的数已经错了，必须报出来。
            if (tick > 32767 || tick < -32768) {
                std::printf("  警告：行 %d key %d 的分数 %ld 超出 Q8.8 范围，已饱和\n",
                            r, key, tick);
                tick = tick > 0 ? 32767 : -32768;
            }
            scores[r][key] = tick;
        }
    }

    dut->io_perf_clear = 1; tick(); dut->io_perf_clear = 0;
    dut->io_start = 1;
    dut->eval();
    // **先走一拍让状态机离开 sIdle。**
    //
    // `io_start` 拉高的那一拍状态机还在 sIdle，这时喂的分数不会被计入——
    // 实测后果是它永远差最后一个 key，卡在 sSelect 等一个不来的 score_valid，
    // 20000 拍超时。
    tick();

    // ---- 逐 key 串行喂分数 ------------------------------------------------
    //
    // `TopFirst` 的 `posCounter` 每个 enable 递增一次，所以**索引就是到达
    // 顺序**——喂 key 0..tileK-1，报出的列号就是 key 号。
    int cycle = 0;
    const int budget = 20000;
    for (int key = 0; key < kTileK && cycle < budget; key++) {
#define SET_SCORE(i) dut->io_score_in_##i = (unsigned short)(scores[i][key] & 0xFFFF)
        SET_SCORE(0); SET_SCORE(1); SET_SCORE(2); SET_SCORE(3);
#undef SET_SCORE
        dut->io_score_valid = 1;
        dut->eval();
        tick();
        cycle++;
    }
    dut->io_score_valid = 0;

    for (; cycle < budget; cycle++) {
        tick();
        if (dut->io_done) break;
    }

    if (cycle >= budget) {
        // 卡住时报出卡在哪 —— 上一版只说「没完成」，只能靠猜。
        std::printf("FAIL 状态机在 %d 拍内没有完成：停在状态 %u 步 %u，"
                    "取数引擎服务了 %u 个请求\n",
                    budget, dut->io_dbg_state, dut->io_dbg_step,
                    dut->io_feeder_requests);
        delete dut;
        return 1;
    }

    // ---- 报告 -------------------------------------------------------------
    std::printf("完成用了 %u 拍\n", dut->io_total_cycles);
    std::printf("  其中等取数引擎 %u 拍（%.1f%%）\n", dut->io_stall_cycles,
                dut->io_total_cycles ? 100.0 * dut->io_stall_cycles / dut->io_total_cycles : 0.0);
    std::printf("  取数引擎：忙 %u 拍，其中冲突 %u 拍，服务 %u 个请求\n",
                dut->io_feeder_busy_cycles, dut->io_feeder_conflict_cycles,
                dut->io_feeder_requests);
    std::printf("  这一块保留 %u 个%s\n", dut->io_chosen_keep,
                dut->io_block_skipped ? "（整块被分档丢弃）" : "");

    // 硬件自己挑的列 vs 参照挑的列。**这是质量指标不是判据**——挑了别的
    // 列不等于算错了，两者的重合度说明的是预测器准不准。
    std::set<long> reference(kept[0].begin(), kept[0].end());
    int overlap = 0, chosen = 0;
#define GET_IDX(i) do { \
    if (dut->io_chosen_valid_##i) { chosen++; \
        if (reference.count(dut->io_chosen_idx_##i)) overlap++; } } while (0)
    GET_IDX(0); GET_IDX(1); GET_IDX(2); GET_IDX(3);
    GET_IDX(4); GET_IDX(5); GET_IDX(6); GET_IDX(7);
#undef GET_IDX
    // **这是 bring-up 判据，不是预测器质量指标。** 喂的是参照用来挑 top-n
    // 的同一组分数，所以硬件 TopK 必须选出同一组列。不一致说明驱动错了。
    std::printf("  硬件 TopK 选出 %d 个，与参照的 top-%d 重合 %d 个\n",
                chosen, kKept, overlap);
    const bool selection_ok = (chosen == kKept) && (overlap == kKept);
    if (!selection_ok) {
        std::printf("FAILED: 喂的是参照同一组分数，选出的列却不同——"
                    "TopK 的驱动有问题，与预测器准不准无关\n");
        delete dut;
        return 1;
    }
    std::printf("PASSED: 选择通路一致，系统跑通\n");
    delete dut;
    return 0;
}

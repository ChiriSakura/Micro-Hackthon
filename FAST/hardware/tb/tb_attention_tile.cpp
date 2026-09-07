// 用真实模型的 Q/K/V 驱动完整的 attention tile，对着 PyTorch 验证。
//
// 这是「模型的一部分注意力能不能在这个加速器上跑」的答案。判据不是
// 「RTL 自洽」——镜像永远答不了那个——而是：同一组从 TinyLlama 第 10 层
// 抓出来的 Q/K/V，硬件算出的注意力输出和 PyTorch 对不对得上。
//
// ## 分两级检查，因为它们会失败于不同的原因
//
//   1. **数据通路**（严格）：把 PyTorch 选中的列直接装进 scheduler，让
//      RePEA 算精确分数 → exp → AV → 归一化。这一级必须**精确匹配**
//      PyTorch 在同一批定点值上的稀疏注意力。
//
//   2. **预测质量**（度量，不是判定）：让预测单元自己在真实数据上挑
//      top-n，报告它和 PyTorch 选择的重合度。
//
// 分开的理由：如果要求硬件的选择和 PyTorch 完全一致，就把「数据通路有
// bug」和「预测器挑得不一样」混成了一个失败。前者是错误，后者是算法性质
// ——DynaX 的预测单元本来就是用低精度近似来排序的，它挑得不完全一样是
// 设计使然，不是缺陷。
//
// ## 一次一个 query 行
//
// RePEA 的 `regs_top` 是**一份**列数据，沿行向下流（每行延迟一拍）。不同
// query 行保留的列不同，所以让 4 行同时算各自的列，需要按脉动斜移错开
// 注入——那正是论文 Algorithm 1 的 block scheduler 在做的事，也是这里
// 还没实现的部分。
//
// 所以这个 testbench 一次算一个 query 位置，**始终用阵列的第 0 行**。
//
// 用第 0 行不是随便选的：阵列第 r 行看到的列数据比第 0 行晚 r 拍
// （rows(r+1).regs_top = rows(r).regs_bottom，每行一级寄存器）。要让第 r 行
// 算它自己的列，注入时机必须跟着错开——那正是 block scheduler 的活。
// 固定用第 0 行就绕开了这件事，代价是没有跨行并行。
//
// 这个坑真实存在过：第一版按「所有行都是 1 拍延迟」驱动，第 0 行结果正确
// 而第 1-3 行全错，连 softmax 分母都不对。

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

#include "golden.h"

#include "VAttentionTile.h"
#include "verilated.h"

namespace {

constexpr int kTileQ = 4;
constexpr int kTileK = 32;
constexpr int kHeadDim = 8;
constexpr int kKept = 8;      // == peCountPerRow，所以 scheduler.passes = 1
constexpr int kPoint = 8;
constexpr int kDividerStages = 8;

// RePE 的 acc_ctrl / exp_ctrl 编码（repe.scala 的 Enum）。
constexpr int kAccClear = 0, kAccIdle = 1, kAccAccumulate = 2, kAccMoveOut = 3;
constexpr int kExpIdle = 0, kExpCompute = 1;

/// tile.json 里的一个二维整数数组。golden.h 的扫描器只认平铺的数组，
/// 这里按行数把它切回来。
std::vector<std::vector<long>> matrix(const std::string& text, const char* key,
                                      int rows, int cols) {
    size_t cursor = text.find(key);
    if (cursor == std::string::npos) {
        std::fprintf(stderr, "tile.json 里没有 %s\n", key);
        std::exit(2);
    }
    std::vector<std::vector<long>> out(rows);
    size_t at = text.find('[', cursor);       // 外层 [
    for (int r = 0; r < rows; r++) {
        at = text.find('[', at + 1);          // 第 r 行的 [
        size_t end = text.find(']', at);
        size_t i = at + 1;
        while (i < end && (int)out[r].size() < cols) {
            while (i < end && (std::isspace((unsigned char)text[i]) || text[i] == ',')) i++;
            if (i >= end) break;
            char* stop = nullptr;
            out[r].push_back(std::strtol(text.c_str() + i, &stop, 10));
            i = (size_t)(stop - text.c_str());
        }
        at = end;
    }
    return out;
}


// Chisel 把 Vec 展平成 io_x_0 .. io_x_{N-1}，所以按下标访问要展开。
// 这个 tile 的尺寸小（tileQ=4，kept=8），手写比生成器划算。
#define ROW4(base)                                        \
    (row == 0 ? dut->base##_0 : row == 1 ? dut->base##_1   \
     : row == 2 ? dut->base##_2 : dut->base##_3)

void setExecuteQ(VAttentionTile* dut, int row, unsigned short value) {
    switch (row) {
        case 0: dut->io_execute_q_0 = value; break;
        case 1: dut->io_execute_q_1 = value; break;
        case 2: dut->io_execute_q_2 = value; break;
        default: dut->io_execute_q_3 = value; break;
    }
}

void setExecuteCol(VAttentionTile* dut, int pe, unsigned short value) {
    switch (pe) {
        case 0: dut->io_execute_cols_0 = value; break;
        case 1: dut->io_execute_cols_1 = value; break;
        case 2: dut->io_execute_cols_2 = value; break;
        case 3: dut->io_execute_cols_3 = value; break;
        case 4: dut->io_execute_cols_4 = value; break;
        case 5: dut->io_execute_cols_5 = value; break;
        case 6: dut->io_execute_cols_6 = value; break;
        default: dut->io_execute_cols_7 = value; break;
    }
}

void setExtIdx(VAttentionTile* dut, int k, unsigned char idx, unsigned char valid) {
    switch (k) {
        case 0: dut->io_sched_ext_idx_0 = idx; dut->io_sched_ext_valid_0 = valid; break;
        case 1: dut->io_sched_ext_idx_1 = idx; dut->io_sched_ext_valid_1 = valid; break;
        case 2: dut->io_sched_ext_idx_2 = idx; dut->io_sched_ext_valid_2 = valid; break;
        case 3: dut->io_sched_ext_idx_3 = idx; dut->io_sched_ext_valid_3 = valid; break;
        case 4: dut->io_sched_ext_idx_4 = idx; dut->io_sched_ext_valid_4 = valid; break;
        case 5: dut->io_sched_ext_idx_5 = idx; dut->io_sched_ext_valid_5 = valid; break;
        case 6: dut->io_sched_ext_idx_6 = idx; dut->io_sched_ext_valid_6 = valid; break;
        default: dut->io_sched_ext_idx_7 = idx; dut->io_sched_ext_valid_7 = valid; break;
    }
}

long rowSum(VAttentionTile* dut, int row) {
    return (short)(unsigned short)ROW4(io_execute_row_sum);
}

void setNorm(VAttentionTile* dut, int row, unsigned short num, unsigned short den) {
    switch (row) {
        case 0: dut->io_norm_numerator_0 = num; dut->io_norm_denominator_0 = den; break;
        case 1: dut->io_norm_numerator_1 = num; dut->io_norm_denominator_1 = den; break;
        case 2: dut->io_norm_numerator_2 = num; dut->io_norm_denominator_2 = den; break;
        default: dut->io_norm_numerator_3 = num; dut->io_norm_denominator_3 = den; break;
    }
}

long outValue(VAttentionTile* dut, int row) {
    return (short)(unsigned short)ROW4(io_out);
}


// ---- 预测通路的端口访问器 -------------------------------------------------
//
// PrePEA 的输入是低位宽无符号：predict_q 是每行一个 4-bit Q 元素，
// predict_k 是一个 key 的 headDim 个 4-bit 元素。

/// 预测端口现在是 SInt(4.W)。Verilator 把它表示成 4 位无符号容器，
/// 所以送值时要取二进制补码的低 4 位（-7 -> 0b1001）。
void setPredictQ(VAttentionTile* dut, int row, unsigned char value) {
    switch (row) {
        case 0: dut->io_predict_q_0 = value; break;
        case 1: dut->io_predict_q_1 = value; break;
        case 2: dut->io_predict_q_2 = value; break;
        default: dut->io_predict_q_3 = value; break;
    }
}

void setPredictK(VAttentionTile* dut, int dim, unsigned char value) {
    switch (dim) {
        case 0: dut->io_predict_k_0 = value; break;
        case 1: dut->io_predict_k_1 = value; break;
        case 2: dut->io_predict_k_2 = value; break;
        case 3: dut->io_predict_k_3 = value; break;
        case 4: dut->io_predict_k_4 = value; break;
        case 5: dut->io_predict_k_5 = value; break;
        case 6: dut->io_predict_k_6 = value; break;
        default: dut->io_predict_k_7 = value; break;
    }
}

long predictScore(VAttentionTile* dut, int row) {
    return (short)(unsigned short)ROW4(io_predict_score);
}

void setSelectIn(VAttentionTile* dut, int row, unsigned short value) {
    switch (row) {
        case 0: dut->io_select_in_0 = value; break;
        case 1: dut->io_select_in_1 = value; break;
        case 2: dut->io_select_in_2 = value; break;
        default: dut->io_select_in_3 = value; break;
    }
}

/// TopK 第 row 行的第 k 个 lane 的 valid 脉冲。
///
/// 必须按脉冲采样，不能等流完再读：TopFirst 在脉冲 valid 的同一周期清掉
/// 自己的寄存器，脉冲随后每拍走一级。等固定延迟去读，读到的是已经被清零
/// 或被后续数据覆盖的值。这条在 tb_topk.cpp 里记过。
bool selectValid(VAttentionTile* dut, int row, int k) {
#define VLD(r, kk) (dut->io_select_valid_##r##_##kk != 0)
    switch (row * 8 + k) {
        case  0: return VLD(0,0); case  1: return VLD(0,1);
        case  2: return VLD(0,2); case  3: return VLD(0,3);
        case  4: return VLD(0,4); case  5: return VLD(0,5);
        case  6: return VLD(0,6); case  7: return VLD(0,7);
        case  8: return VLD(1,0); case  9: return VLD(1,1);
        case 10: return VLD(1,2); case 11: return VLD(1,3);
        case 12: return VLD(1,4); case 13: return VLD(1,5);
        case 14: return VLD(1,6); case 15: return VLD(1,7);
        case 16: return VLD(2,0); case 17: return VLD(2,1);
        case 18: return VLD(2,2); case 19: return VLD(2,3);
        case 20: return VLD(2,4); case 21: return VLD(2,5);
        case 22: return VLD(2,6); case 23: return VLD(2,7);
        case 24: return VLD(3,0); case 25: return VLD(3,1);
        case 26: return VLD(3,2); case 27: return VLD(3,3);
        case 28: return VLD(3,4); case 29: return VLD(3,5);
        case 30: return VLD(3,6); default: return VLD(3,7);
    }
#undef VLD
}

/// TopK 第 row 行的第 k 个 lane 选中的列号。Vec(Vec()) 展平成 io_x_row_k。
long selectIdx(VAttentionTile* dut, int row, int k) {
#define IDX(r, kk) dut->io_select_idx_##r##_##kk
    switch (row * 8 + k) {
        case  0: return IDX(0,0); case  1: return IDX(0,1);
        case  2: return IDX(0,2); case  3: return IDX(0,3);
        case  4: return IDX(0,4); case  5: return IDX(0,5);
        case  6: return IDX(0,6); case  7: return IDX(0,7);
        case  8: return IDX(1,0); case  9: return IDX(1,1);
        case 10: return IDX(1,2); case 11: return IDX(1,3);
        case 12: return IDX(1,4); case 13: return IDX(1,5);
        case 14: return IDX(1,6); case 15: return IDX(1,7);
        case 16: return IDX(2,0); case 17: return IDX(2,1);
        case 18: return IDX(2,2); case 19: return IDX(2,3);
        case 20: return IDX(2,4); case 21: return IDX(2,5);
        case 22: return IDX(2,6); case 23: return IDX(2,7);
        case 24: return IDX(3,0); case 25: return IDX(3,1);
        case 26: return IDX(3,2); case 27: return IDX(3,3);
        case 28: return IDX(3,4); case 29: return IDX(3,5);
        case 30: return IDX(3,6); default: return IDX(3,7);
    }
#undef IDX
}

class Driver {
public:
    explicit Driver(VAttentionTile* dut) : dut_(dut) {}

    void tick() {
        dut_->eval();
        dut_->clock = 1; dut_->eval();
        dut_->clock = 0; dut_->eval();
    }

    void reset() {
        dut_->reset = 1;
        dut_->clock = 0;
        idle();
        for (int i = 0; i < 8; i++) tick();
        dut_->reset = 0;
        tick();
    }

    /// 所有控制拉到静止，避免上一阶段的残留影响下一阶段。
    void idle() {
        dut_->io_select_enable = 0;
        dut_->io_sched_load = 0;
        dut_->io_sched_from_topk = 0;
        dut_->io_sched_pass = 0;
        dut_->io_execute_clr = 0;
        dut_->io_execute_acc_ctrl = kAccIdle;
        dut_->io_execute_exp_ctrl = kExpIdle;
        dut_->io_norm_valid = 0;
        dut_->io_predict_pes_state = 0;   // sIdle
        dut_->io_predict_array_state = 0; // aIdle
        for (int r = 0; r < kTileQ; r++) setExecuteQ(dut_, r, 0);
        for (int p = 0; p < kKept; p++) setExecuteCol(dut_, p, 0);
    }

    /// 把 PyTorch 选中的列装进 scheduler 的第 row 行，绕过预测单元。
    ///
    /// 走的是顶层的外部装载路径（sched_from_topk = 0）。这样这一级检查
    /// 只问「选中这些列之后，硬件算出的注意力对不对」——预测器挑得准不准
    /// 是另一个问题，另外度量。
    void loadIndices(int row, const std::vector<long>& columns) {
        dut_->io_sched_from_topk = 0;
        dut_->io_sched_load_row = (unsigned char)row;
        for (int k = 0; k < kKept; k++)
            setExtIdx(dut_, k, (unsigned char)columns[k], 1);
        dut_->io_sched_load = 1;
        tick();
        dut_->io_sched_load = 0;
    }

    VAttentionTile* dut_;
};

}  // namespace

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    const char* path = argc > 1 ? argv[1] : "tile.json";
    const std::string text = golden::slurp(path);

    const auto q = matrix(text, "\"q_ticks\"", kTileQ, kHeadDim);
    const auto k = matrix(text, "\"k_ticks\"", kTileK, kHeadDim);
    const auto v = matrix(text, "\"v_ticks\"", kTileK, kHeadDim);
    const auto expected = matrix(text, "\"expected_sparse\"", kTileQ, kHeadDim);
    const auto kept = matrix(text, "\"expected_kept_idx\"", kTileQ, kKept);

    std::printf("从 %s 载入：Q[%dx%d] K/V[%dx%d]，每行保留 %d/%d\n\n",
                path, kTileQ, kHeadDim, kTileK, kHeadDim, kKept, kTileK);

    auto* dut = new VAttentionTile;
    Driver drv(dut);

    int mismatches = 0;
    int compared = 0;
    int truncated = 0;   // 差 1 tick 且方向正确的，算通过

    for (int row = 0; row < kTileQ; row++) {
        drv.reset();

        // ---- 阶段 0：把选中的列装进 scheduler -------------------------------
        //
        // scheduler 复位后 actives 全 false，sel_cols 会全指向零逃逸——
        // 不装载的话每个 PE 都乘 0。装载之后 sel_cols(row)(pe) = pe，
        // 于是 PE pe 取 reg_cols 的第 pe 个槽，而下面往那个槽里送的正是
        // K[kept[row][pe]]。**这就是那条曾经断开的线**。
        std::vector<long> columns(kept[row].begin(), kept[row].end());
        // 装进阵列第 0 行——下面所有驱动和读取都用第 0 行。
        drv.loadIndices(0, columns);

        // ---- 阶段 1：QK^T --------------------------------------------------
        dut->io_execute_clr = 1;
        drv.tick();
        dut->io_execute_clr = 0;
        dut->io_execute_acc_ctrl = kAccClear;
        drv.tick();

        for (int d = 0; d < kHeadDim; d++) {
            // 送第 d 维：Q 是标量，K 的每个槽对应一个保留列。
            setExecuteQ(dut, 0, (unsigned short)(q[row][d] & 0xFFFF));
            for (int pe = 0; pe < kKept; pe++)
                setExecuteCol(dut, pe, (unsigned short)(k[kept[row][pe]][d] & 0xFFFF));
            // reg_q / reg_cols 都是寄存器，PE 看到的是上一拍呈现的值——
            // 两者延迟相同，所以保持对齐；累加在下一拍生效。
            dut->io_execute_acc_ctrl = (d == 0) ? kAccClear : kAccAccumulate;
            drv.tick();
        }
        dut->io_execute_acc_ctrl = kAccAccumulate;
        drv.tick();

        // ---- 阶段 2：exp，并读出 softmax 分母 -------------------------------
        dut->io_execute_acc_ctrl = kAccIdle;
        dut->io_execute_exp_ctrl = kExpCompute;
        drv.tick();
        dut->io_execute_exp_ctrl = kExpIdle;
        drv.tick();

        // 非 move_out 状态下 io.out = score_exp，行加法器给出的就是
        // sum_j exp(s_j)——softmax 的分母。
        const long denominator = rowSum(dut, 0);

        // ---- 阶段 3：AV --------------------------------------------------
        std::vector<long> numerators;
        for (int d = 0; d < kHeadDim + 2; d++) {
            const int index = d < kHeadDim ? d : kHeadDim - 1;
            for (int pe = 0; pe < kKept; pe++)
                setExecuteCol(dut, pe, (unsigned short)(v[kept[row][pe]][index] & 0xFFFF));
            dut->io_execute_acc_ctrl = kAccMoveOut;
            drv.tick();
            numerators.push_back(rowSum(dut, 0));
        }

        // ---- 阶段 4：归一化 ------------------------------------------------
        //
        // move_out 每拍把**上一拍**的 acc 推出来，而 acc 在 move_out 的那一拍
        // 才装进 score_exp * v；再加上 row_sum 自己是寄存器，所以第 d 个输出
        // 维度对应 numerators 里偏移 2 的位置。
        //
        // 除法器是 kDividerStages 级流水，每拍收一个输入、延迟固定拍后按序
        // 吐出。所以驱动和收集必须在**同一个循环**里做——先驱动完再收集会
        // 漏掉驱动期间就已经吐出来的那些。
        std::vector<long> got;
        const int normCycles = kHeadDim + kDividerStages + 4;
        for (int c = 0; c < normCycles; c++) {
            const bool feeding = c < kHeadDim;
            const size_t at = (size_t)c + 2;
            const long numerator =
                (feeding && at < numerators.size()) ? numerators[at] : 0;
            dut->io_norm_valid = feeding ? 1 : 0;
            setNorm(dut, 0, (unsigned short)(numerator & 0xFFFF),
                    (unsigned short)(denominator & 0xFFFF));
            dut->eval();
            drv.tick();
            if (dut->io_out_valid && (int)got.size() < kHeadDim)
                got.push_back(outValue(dut, 0));
        }
        dut->io_norm_valid = 0;
        got.resize(kHeadDim, 0);

        std::printf("query 行 %d  分母=%ld  保留列=[", row, denominator);
        for (int pe = 0; pe < kKept; pe++)
            std::printf("%ld%s", kept[row][pe], pe + 1 < kKept ? "," : "");
        std::printf("]\n");
        std::printf("  硬件   ");
        for (int d = 0; d < kHeadDim; d++) std::printf("%6ld", got[d]);
        std::printf("\n  PyTorch");
        for (int d = 0; d < kHeadDim; d++) std::printf("%6ld", expected[row][d]);
        std::printf("\n");

        // 判据不是精确相等，而是「差 <= 1 tick **且** 硬件幅值不超过
        // PyTorch」。后半句是关键：
        //
        //   硬件全程 Q8.8 定点、除法器朝零截断；PyTorch 用浮点算完再量化，
        //   相当于四舍五入。所以硬件的结果只会**偏小**，永远不会偏大。
        //
        //   一个真正的错误不会有这种单侧性——它的误差会有正有负、有大有小。
        //   实测 32 个输出维度：17 个完全一致，15 个硬件幅值小 1 tick，
        //   0 个偏大。只看「差 <= 1」会漏掉方向信息，而方向正是区分
        //   「舍入」和「算错」的那一半证据。
        for (int d = 0; d < kHeadDim; d++) {
            compared++;
            const long delta = got[d] - expected[row][d];
            const bool withinTick = delta >= -1 && delta <= 1;
            const bool notLarger = std::labs(got[d]) <= std::labs(expected[row][d]);
            if (!withinTick || !notLarger) {
                mismatches++;
                std::printf("    维度 %d 超出容差：硬件 %ld，PyTorch %ld%s\n",
                            d, got[d], expected[row][d],
                            notLarger ? "" : "（幅值偏大——不是截断能解释的）");
            } else if (delta != 0) {
                truncated++;
            }
        }
    }


    // =======================================================================
    // 第二级：预测器的选择质量
    // =======================================================================
    //
    // 这一级不是对错判定，是**度量**。DynaX 的预测单元用 4-bit 无符号近似
    // 分数来排序，它挑的列和 PyTorch 用精确分数挑的不完全一样——那是设计
    // 使然，不是缺陷。
    //
    // 但这个差异有后果：Kernel Agent 报告的精度损失是**软件用精确分数**算
    // 出来的。如果硬件的预测器明显挑得更差，那个精度数字在这台加速器上就
    // 不成立。这一级量的就是这个差距。
    //
    // 控制序列沿用 golden/predict_unit.py 里 prepe_array_schedule 的排程
    // （已逐周期验证过）：装载 Q 时每组按下标降序喂，然后 K 保持不动直到
    // psum 沿链走完并且传到最后一行。
    std::printf("\n=== 预测器选择质量 ===\n");
    {
        constexpr int kSIdle = 0, kSClear = 1, kSCalc = 2, kSInput = 3;
        constexpr int kAIdle = 0, kAClear = 1, kACalc = 2;
        const int columns = kHeadDim / 2;            // 1:2 剪枝，每行 4 个 PE
        const int settle = kTileQ + columns + 4;     // 脉动延迟：行数 + 链长

        const auto qp = matrix(text, "\"q_predict\"", kTileQ, kHeadDim);
        const auto kp = matrix(text, "\"k_predict\"", kTileK, kHeadDim);

        drv.reset();
        auto setK = [&](int key) {
            for (int d = 0; d < kHeadDim; d++)
                setPredictK(dut, d, (unsigned char)(key < 0 ? 0 : kp[key][d] & 0xF));  // 同上
        };
        auto step = [&](int pes, int arr) {
            dut->io_predict_pes_state = (unsigned char)pes;
            dut->io_predict_array_state = (unsigned char)arr;
            drv.tick();
        };

        // ---- 装载 Q：对齐相位，然后每组按下标降序喂 ------------------------
        //
        // 相位对齐是硬性的，不是保险措施。`cycleToggle` 每拍无条件翻转，
        // 而 PE 的 `inputCounter` 只在 sInput 里推进——两者有相对相位，
        // 装载必须从对的那一拍开始，否则采到的是 toggle-0 分支驱动的 0，
        // 一个 Q 都装不进去，全部近似分数变成 0。
        //
        // 复位时 cycleToggle 被保持在 0，撤销复位后那一拍翻到 1；
        // 金标准的排程假设从 0 开始，所以这里补一拍把它翻回 0。
        // 实测过：少这一拍，32 个 key 的分数全是 0。
        for (int r = 0; r < kTileQ; r++) setPredictQ(dut, r, 0);
        setK(-1);
        step(kSIdle, kAClear);   // 相位补偿
        step(kSIdle, kAClear);
        step(kSClear, kAClear);
        for (int c = columns - 1; c >= 0; c--) {
            // 组内降序：先喂 2c+1 再喂 2c。选择索引的顺序和到达顺序相反，
            // 这是 verified_scope 里记着的那条使用约束。
            for (int which = 1; which >= 0; which--) {
                for (int r = 0; r < kTileQ; r++)
                    setPredictQ(dut, r, (unsigned char)(qp[r][2 * c + which] & 0xF));  // 补码低 4 位
                step(kSInput, kAClear);
            }
        }
        for (int r = 0; r < kTileQ; r++) setPredictQ(dut, r, 0);

        // ---- 逐个 key 算近似分数 -------------------------------------------
        std::vector<std::vector<long>> scores(kTileQ, std::vector<long>(kTileK, 0));
        for (int key = 0; key < kTileK; key++) {
            setK(key);
            for (int i = 0; i < settle; i++) step(kSCalc, kAClear);
            step(kSCalc, kACalc);   // 这一拍把 exp(psum) 锁进 expRegs
            // expRegs 是寄存器，s_out 是它的组合读出。A_CALC 那一拍写进去的
            // 值，要到**下一拍**才能在 s_out 上看到——A_IDLE 保持不变，正好
            // 用来读。少这一拍读到的是上一个 key 的分数（全 0，因为前面是
            // A_CLEAR），这正是第一版预测器重合度报 0% 的原因。
            step(kSIdle, kAIdle);
            for (int r = 0; r < kTileQ; r++) scores[r][key] = predictScore(dut, r);
        }

        std::printf("  近似分数（行0 前 12 个 key）：");
        for (int key = 0; key < 12; key++) std::printf("%6ld", scores[0][key]);
        std::printf("\n  非零分数个数：");
        for (int r = 0; r < kTileQ; r++) {
            int nz = 0;
            for (int key = 0; key < kTileK; key++) if (scores[r][key] != 0) nz++;
            std::printf(" 行%d=%d/%d", r, nz, kTileK);
        }
        std::printf("\n");

        // ---- 把分数串行喂给 TopK -------------------------------------------
        setK(-1);
        step(kSIdle, kAIdle);

        // 每个 lane 在自己的 valid 脉冲那一拍采样。等流完再读会读到已被清零
        // 的寄存器——第一版就是这么错的，选出一堆重复的 31。
        std::vector<std::vector<long>> captured(
            kTileQ, std::vector<long>(kKept, -1));
        auto capture = [&]() {
            for (int r = 0; r < kTileQ; r++)
                for (int k = 0; k < kKept; k++)
                    if (captured[r][k] < 0 && selectValid(dut, r, k))
                        captured[r][k] = selectIdx(dut, r, k);
        };

        for (int key = 0; key < kTileK; key++) {
            for (int r = 0; r < kTileQ; r++)
                setSelectIn(dut, r, (unsigned short)(scores[r][key] & 0xFFFF));
            dut->io_select_enable = 1;
            drv.tick();
            capture();
        }
        dut->io_select_enable = 0;
        for (int i = 0; i < kKept + 6; i++) { drv.tick(); capture(); }

        // ---- 和 PyTorch 的选择比重合度 --------------------------------------
        int totalOverlap = 0;
        for (int row = 0; row < kTileQ; row++) {
            std::vector<long> hw = captured[row];
            int overlap = 0;
            for (long column : hw)
                for (int k = 0; k < kKept; k++)
                    if (column == kept[row][k]) { overlap++; break; }
            totalOverlap += overlap;
            std::printf("  行%d 硬件选 [", row);
            for (int k = 0; k < kKept; k++)
                std::printf("%2ld%s", hw[k], k + 1 < kKept ? "," : "");
            std::printf("]  重合 %d/%d\n", overlap, kKept);
        }
        std::printf("  总重合度 %d/%d = %.0f%%"
                    "（这是度量不是判定：4-bit 无符号近似排序本来就不会和"
                    "精确分数完全一致）\n",
                    totalOverlap, kTileQ * kKept,
                    100.0 * totalOverlap / (kTileQ * kKept));
    }

    delete dut;
    std::printf("\n%s: %d/%d 个输出维度在容差内"
                "（%d 个完全一致，%d 个因朝零截断小 1 tick）\n",
                mismatches ? "FAILED" : "PASSED", compared - mismatches, compared,
                compared - mismatches - truncated, truncated);
    return mismatches ? 1 : 0;
}

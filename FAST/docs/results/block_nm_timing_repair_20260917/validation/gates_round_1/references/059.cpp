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

// 尺寸常量与端口访问由 tb/gen_ports.py 生成。
//
// 手写的版本把 `setExtIdx` 展开到 8 个 case 加一个 `default`——kept=16 时
// 第 8-15 项会**全部写进端口 7**，而且不会有任何东西报错：索引装错了，
// 算出来的是另一组保留列的注意力，数字看起来完全正常。
// 论文尺寸 kept=16 / pe=4 必然踩到这个。
#include "tile_ports.h"

namespace {

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
        // 行数不够就在这里停住。**不 return 短的结果**：调用方拿着
        // out[r] 去索引 K，空的 vector 越界读出来是垃圾下标，表现为段
        // 错误——而段错误看起来像被测对象坏了，不像喂错了数据。
        // 这个坑真撞到过：作业 17222441 把 tileQ=4 的抓取喂给 tileQ=32
        // 的 testbench，rc=139，查的方向全错。
        if (at == std::string::npos) {
            // 不报「文件有几行」——扫描器数完本键的行之后会走进**下一个**
            // 键的方括号里，那个计数不是文件的行数。只说读到第几行读不下去。
            std::fprintf(stderr,
                         "%s 读到第 %d 行就没有了，testbench 要 %d 行——抓取的"
                         "形状和被测尺寸不匹配。用形状匹配的 tile.json 重跑。\n",
                         key, r, rows);
            std::exit(2);
        }
        size_t end = text.find(']', at);
        size_t i = at + 1;
        while (i < end && (int)out[r].size() < cols) {
            while (i < end && (std::isspace((unsigned char)text[i]) || text[i] == ',')) i++;
            if (i >= end) break;
            char* stop = nullptr;
            out[r].push_back(std::strtol(text.c_str() + i, &stop, 10));
            i = (size_t)(stop - text.c_str());
        }
        if ((int)out[r].size() != cols) {
            std::fprintf(stderr,
                         "%s 第 %d 行读出 %d 列，testbench 要 %d 列——抓取的"
                         "形状和被测尺寸不匹配。用形状匹配的 tile.json 重跑。\n",
                         key, r, (int)out[r].size(), cols);
            std::exit(2);
        }
        at = end;
    }
    return out;
}


// 定点格式的小数位数，和 `Elaborate.scala` 的 `Point` 一致。
constexpr int kPoint = 8;
// softmax 除法器的流水级数，和计划里的 dividerStages 一致——收集输出要按
// 这个延迟对齐。
constexpr int kDividerStages = 8;


// 预测通路的端口访问器同样由 gen_ports.py 生成——它们原来把
// 「行 * 8 + k」写死了，kept=16 时索引全错，而且是静默地读到另一个 lane。

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
        for (int p = 0; p < kPe; p++) setExecuteCol(dut_, p, 0);
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
    int lowByRounding = 0;   // 偏小且在容差内
    int highByRounding = 0;  // 偏大且在容差内——修好乘法舍入之后才会出现
    long deltaSum = 0;       // 有符号误差之和，用来报均值

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

        // ---- 逐趟：QK^T -> exp -> AV，然后**在外面把各趟加起来** -------
        //
        // 一趟只能算 kPe 个保留列。阵列没有跨趟累加器，所以分母和分子都
        // 由这里逐趟相加——这正是硬件缺的那层控制。
        long denominator = 0;
        std::vector<long> numerators;

        for (int pass = 0; pass < kPasses; pass++) {
            dut->io_sched_pass = pass;
            dut->eval();

            // 阶段 1：QK^T
            dut->io_execute_clr = 1;
            drv.tick();
            dut->io_execute_clr = 0;
            dut->io_execute_acc_ctrl = kAccClear;
            drv.tick();

            for (int d = 0; d < kHeadDim; d++) {
                setExecuteQ(dut, 0, (unsigned short)(q[row][d] & 0xFFFF));
                for (int pe = 0; pe < kPe; pe++) {
                    // 越界的槽喂 0：调度器已经把它的 sel_col 指向零逃逸，
                    // 但喂真实数据会让「零逃逸有没有生效」这件事测不出来。
                    const int slot = pass * kPe + pe;
                    const long value =
                        slot < kKept ? k[kept[row][slot]][d] : 0;
                    setExecuteCol(dut, pe, (unsigned short)(value & 0xFFFF));
                }
                // reg_q / reg_cols 都是寄存器，PE 看到的是上一拍呈现的值——
                // 两者延迟相同，所以保持对齐；累加在下一拍生效。
                dut->io_execute_acc_ctrl = (d == 0) ? kAccClear : kAccAccumulate;
                drv.tick();
            }
            dut->io_execute_acc_ctrl = kAccAccumulate;
            drv.tick();

            // 阶段 2：exp，读出这一趟的分母
            dut->io_execute_acc_ctrl = kAccIdle;
            dut->io_execute_exp_ctrl = kExpCompute;
            drv.tick();
            dut->io_execute_exp_ctrl = kExpIdle;
            drv.tick();
            denominator += rowSum(dut, 0);

            // 阶段 3：AV
            for (int d = 0; d < kHeadDim + 2; d++) {
                const int index = d < kHeadDim ? d : kHeadDim - 1;
                for (int pe = 0; pe < kPe; pe++) {
                    const int slot = pass * kPe + pe;
                    const long value =
                        slot < kKept ? v[kept[row][slot]][index] : 0;
                    setExecuteCol(dut, pe, (unsigned short)(value & 0xFFFF));
                }
                dut->io_execute_acc_ctrl = kAccMoveOut;
                drv.tick();
                const long partial = rowSum(dut, 0);
                if (pass == 0) numerators.push_back(partial);
                else numerators[d] += partial;
            }
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

        // 判据是「差 <= kPasses tick」，双侧。
        //
        //   曾经的判据多一条「硬件幅值不许超过 PyTorch」，而那条规则成立的
        //   前提已经被修掉了。上游 `repe.scala` 的 `mul := a * b` 是 floor
        //   （缺陷 6），乘积误差恒为负，于是硬件只会偏小，一个偏大的点就
        //   足以证明算错。打上舍入补丁之后乘积误差是双侧的——量化预测
        //   headDim=64 时偏差范围 [-5,+7]，实测 headDim=8 是 7 偏小 : 6 偏大。
        //   继续用单侧规则，等于拿旧数据通路的性质去判新数据通路。
        //
        //   **也不要退而求其次去卡「低侧必须占多数」**：我按 2048 个点的
        //   1074:4 拟过这么一条，它在 headDim=8 上立刻把一个每点都在容差内
        //   的运行判成失败——那个比例本来就随尺寸变，拿单个数据集拟出来的
        //   阈值不是判据。
        //
        //   方向信息没有丢，它下面照样报——**当作归因线索而不是判据**。
        //   缺陷 6 正是靠「1154 个失配全部偏小」定位的，但抓到它的是容差
        //   本身（894/2048 超窗），不是单侧性。
        for (int d = 0; d < kHeadDim; d++) {
            compared++;
            const long delta = got[d] - expected[row][d];
            // **容差有两项：每趟的截断，加上随 head_dim 累积的舍入噪声。**
            //
            //   每一趟都要读一次 row_sum、各自截断一次 -> kPasses 个 tick。
            //   这一项原来是全部，而它只对 floor 时代成立：那时乘积误差恒为
            //   负，逐点偏差由截断主导。缺陷 6 改成四舍五入之后，每个 MAC
            //   步引入 ±0.5 LSB 的**双侧**噪声，在 headDim 步上做随机游走，
            //   所以逐点偏差随 head_dim 增长——kPasses 这一项对它是盲的。
            //
            //   实测（补丁后）：
            //     headDim=8,  1 趟          32/32 全在 ±1
            //     headDim=64, 2 趟, 2048 维  全在 ±2，均值 +0.04
            //     headDim=64, 1 趟, 1024 维  1020 在 ±1，4 个在 ±2（三正一负），
            //                                均值 +0.06
            //   1 趟 headDim=64 的那 4 个点撑破了只有 kPasses 的窗口——不是
            //   缺陷（4/1024、双向、均值近零），是窗口漏了这一项。
            //
            //   sqrt(headDim)/8 是随机游走的形状（噪声按 sqrt(步数) 增长），
            //   系数取到**恰好不低于实测最大值**：headDim=8 和 64 都给 1。
            //   不用 0.5*sqrt(headDim)（headDim=64 会给 4）：那是分数上的
            //   标准差，而 softmax 的归一化把它衰减掉了大半，照抄会让窗口
            //   松一倍而白白丢掉鉴别力。
            //
            //   均值那一项才是「每步一点、同向累积」的探针，它不随尺寸稀释。
            const long rounding = (long)std::ceil(std::sqrt((double)kHeadDim) / 8.0);
            const long ticks = kPasses + rounding;
            deltaSum += delta;
            if (delta < -ticks || delta > ticks) {
                mismatches++;
                std::printf("    维度 %d 超出容差：硬件 %ld，PyTorch %ld（差 %+ld tick，"
                            "上限 %ld）\n", d, got[d], expected[row][d], delta, ticks);
            } else if (delta < 0) {
                lowByRounding++;
            } else if (delta > 0) {
                highByRounding++;
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
    // 方向分布**只报不判**（理由见上面判据处）。它是归因线索：全部偏小
    // 指向某一级的截断，两侧均衡指向舍入噪声。均值是这条线索里最有用的
    // 一个数，因为它**与尺寸无关**：逐维度的容差随趟数放宽却不随 head_dim
    // 放宽，所以每步一点的截断偏差在小尺寸上藏得住（缺陷 6 在 headDim=8
    // 只偏约 -4 tick，32/32 全过），到 headDim=64 才炸。均值不会——同一个
    // 缺陷 floor 下是 -29.8 tick，补丁后是 +0.04。
    // 说「小 1 tick」是错的：容差随趟数放宽，两趟时确实出现过 2 tick 的
    // 偏差。报告写死一个数会让人以为偏差比实际小。
    std::printf("\n%s: %d/%d 个输出维度在容差内"
                "（%d 个完全一致，%d 个偏小，%d 个偏大，平均 %+.2f tick，"
                "上限 %d tick = %d 趟 + %d 舍入）\n",
                mismatches ? "FAILED" : "PASSED",
                compared - mismatches, compared,
                compared - mismatches - lowByRounding - highByRounding,
                lowByRounding, highByRounding,
                compared ? (double)deltaSum / compared : 0.0,
                kPasses + (long)std::ceil(std::sqrt((double)kHeadDim) / 8.0),
                kPasses, (long)std::ceil(std::sqrt((double)kHeadDim) / 8.0));
    return mismatches ? 1 : 0;
}

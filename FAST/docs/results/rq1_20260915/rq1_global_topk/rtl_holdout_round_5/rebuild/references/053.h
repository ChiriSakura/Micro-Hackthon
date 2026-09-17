// DynaX 各单元的驱动时序，做成可复用的驱动器而不是散在注释里的知识。
//
// ## 为什么需要这个文件
//
// 这些模块的控制时序有几处**反直觉且不写在源码里**的性质。它们此前以散文
// 形式记录在各个 golden 模型和 testbench 的注释里——然后在写下一个
// testbench 时被重新踩了一遍。三次：
//
//   1. `s_out` 是寄存器，A_CALC 写进去的值要**下一拍**才读得到
//      （记在 PrePEArrayModel 里，在 tb_attention_tile 里重踩）
//   2. `cycleToggle` 每拍无条件翻转，装载必须从对的相位开始
//      （记在 prepe_array_schedule 的 docstring 里，重踩）
//   3. TopK 必须按每个 lane 自己的 `idxValid` 脉冲采样，不能等固定延迟
//      （记在 tb_topk.cpp 里，重踩）
//
// **知识以注释形式存在，防不住下一个使用者。** 所以这里把它变成代码：
// 调用 `PredictDriver::loadQuery()` 就自动带上相位补偿，调用
// `TopKCapture::sample()` 就自动按脉冲采样，用错的方式反而更麻烦。
//
// ## 边界
//
// 这里只封装**时序**，不封装数据。每个 testbench 仍然自己决定送什么值、
// 和什么参照比——那才是它要验证的东西。

#pragma once

#include <vector>

namespace dynax {

// ---------------------------------------------------------------------------
// 控制编码。取自 RTL 的 Enum 定义，改 RTL 时这里要跟着改。
// ---------------------------------------------------------------------------

// repe.scala：Enum(4) 给累加器，Enum(2) 给指数单元
enum AccCtrl { kAccClear = 0, kAccIdle = 1, kAccAccumulate = 2, kAccMoveOut = 3 };
enum ExpCtrl { kExpIdle = 0, kExpCompute = 1 };

// prepe_1_2.scala / prepe_1_4.scala：Enum(4) 给 PE，Enum(3) 给阵列
enum PeState { kSIdle = 0, kSClear = 1, kSCalc = 2, kSInput = 3 };
enum ArrayState { kAIdle = 0, kAClear = 1, kACalc = 2 };

/// 复位后 `cycleToggle` 的值。
///
/// 它是 RegInit(0)，复位期间被按在 0；撤销复位后的第一拍把它翻到 1。
/// 而金标准的装载排程假设从 0 开始——所以装载前要补一拍。
///
/// 少这一拍的后果不是「差一点」，是**一个 Q 都装不进去**：PE 采到的是
/// toggle-0 分支驱动的 0，全部近似分数变成 0。实测过。
constexpr int kToggleAfterReset = 1;

/// 预测阵列的沉降时间：脉动延迟本身。
///
/// K 每拍下移一行，所以第 (height-1) 行要等 height-1 拍才看到它；
/// psum 每拍右移一个 PE，所以还要 columns 拍走到链尾。
///
/// 小实例会掩盖这一点——height=2 时留 columns+4 也能对，height=32 时
/// 前几行正确、后面逐行衰减到 0。
inline int predictSettleCycles(int height, int columns) {
    return height + columns + 4;
}

// ---------------------------------------------------------------------------
// TopK：按 valid 脉冲采样
// ---------------------------------------------------------------------------

/// TopK 每个 lane 的索引必须在**它自己的 idxValid 拉高那一拍**采样。
///
/// TopFirst 在脉冲 valid 的同一周期清掉自己的寄存器，脉冲随后每拍走一级。
/// 等流完再读，读到的是已被清零或被后续数据覆盖的值——表现为选出一堆
/// 重复的最后一个下标。
///
/// 用法：每拍 tick 之后调一次 sample()，最后取 result()。
template <int kRows, int kLanes>
class TopKCapture {
public:
    TopKCapture() {
        for (int r = 0; r < kRows; r++)
            for (int k = 0; k < kLanes; k++) captured_[r][k] = -1;
    }

    /// `valid(row, lane)` 和 `index(row, lane)` 由调用方提供——端口名随
    /// 顶层不同而不同，这里不猜。
    template <typename ValidFn, typename IndexFn>
    void sample(ValidFn valid, IndexFn index) {
        for (int r = 0; r < kRows; r++)
            for (int k = 0; k < kLanes; k++)
                if (captured_[r][k] < 0 && valid(r, k))
                    captured_[r][k] = index(r, k);
    }

    std::vector<long> row(int r) const {
        return std::vector<long>(captured_[r], captured_[r] + kLanes);
    }

    /// 有没有 lane 一直没等到脉冲。非零说明驱动的拍数不够，或者 enable
    /// 没有覆盖整个块——两者都会让结果偏少而不是报错。
    int missing() const {
        int count = 0;
        for (int r = 0; r < kRows; r++)
            for (int k = 0; k < kLanes; k++) if (captured_[r][k] < 0) count++;
        return count;
    }

private:
    long captured_[kRows][kLanes];
};

// ---------------------------------------------------------------------------
// 比对判据
// ---------------------------------------------------------------------------

/// 定点结果和浮点参照的比对：差 <= 1 tick **且**硬件幅值不超过参照。
///
/// 后半句是关键。硬件全程定点、除法器朝零截断；参照用浮点算完再量化，
/// 相当于四舍五入。所以硬件只会偏小，永远不会偏大——一个真正的错误不会
/// 有这种单侧性，它的误差有正有负。
///
/// 只看 |diff| <= 1 会丢掉方向信息，而方向正是区分「舍入」和「算错」的
/// 那一半证据。
inline bool withinTruncationTolerance(long measured, long reference, int ticks = 1) {
    const long delta = measured - reference;
    if (delta < -ticks || delta > ticks) return false;
    const long a = measured < 0 ? -measured : measured;
    const long b = reference < 0 ? -reference : reference;
    // **单侧性才是判据的核心**，容差只是范围。
    //
    // 硬件全程定点、除法器朝零截断，所以它的结果只会偏小、永远不会偏大。
    // 一个真正的错误不会有这种单侧性——它的误差有正有负、有大有小。
    // 放宽 ticks 的同时必须保住这一条，否则容差就退化成「差不多就行」。
    return a <= b;
}

/// 多趟累加下允许几个 tick。
///
/// **截断点随趟数增加。** 每一趟都要读一次 row_sum、各自截断一次，所以 N 趟
/// 的偏差上界是 N 个 tick 而不是 1 个。实测 2 趟时确实出现过 2 tick 的偏差
/// （硬件 4 / PyTorch 6），方向仍然是偏小——那是算术的结果，不是错误。
///
/// 写成函数而不是常数，是因为「容差为什么是这个数」必须能追到趟数上；
/// 直接写 2 的话，下次换成 4 趟时没人知道该不该改。
inline int truncationTicks(int passes) { return passes < 1 ? 1 : passes; }

}  // namespace dynax

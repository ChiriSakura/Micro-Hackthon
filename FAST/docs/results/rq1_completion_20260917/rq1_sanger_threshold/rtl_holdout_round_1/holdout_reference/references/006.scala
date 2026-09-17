// ============================================================================
//  NOT PART OF THE DYNAX RELEASE.  This module is a FAST addition.
// ============================================================================
//
//  为什么存在：实测发现 softmax 归一化器是整个系统的瓶颈。
//
//      RePEArray（执行阵列）   2.22 ns   450 MHz   43 级
//      PSumSoftmax（归一化）  14.83 ns    67 MHz  252 级，全在 divider/ 里
//
//  DynaX 的 `FixedPointDiv` 用 Chisel 的 `/` 算 (num << point) / den，综合出
//  一个纯组合的除法器——一拍出结果，但那一拍要 14.8 ns。执行阵列能跑 450 MHz
//  却被它拖到 67 MHz。
//
//  更要紧的是对协同优化的影响：搜索空间里有 9 个维度（tile、并行度、阵列
//  行列、寄存器宽度、队列深度……）**全都是阵列和调度的维度**，没有一个和
//  除法器有关。优化器在调阵列规模，而时钟由除法器决定——它不是优化得不够
//  好，是在优化一个不决定结果的变量。
//
//  这个模块把「除法器怎么实现」变成一个可搜索的维度：级数是参数，面积和
//  频率随之变化，协同优化器可以在这条曲线上取点。
//
//  算法：基 2 恢复除法。每次迭代产生一位商——
//
//      remainder = (remainder << 1) | dividend[i]
//      if remainder >= divisor: remainder -= divisor; quotient[i] = 1
//
//  `stages` 把这些迭代切成若干段，段之间插寄存器。所以：
//
//      stages = 1            退化成组合除法（和上游等价，但慢在同一处）
//      stages = iterations   每级一位，最快也最费寄存器
//
//  语义和上游一致：先取绝对值做无符号除法、最后套符号，**朝零截断**——
//  这正是 Chisel `/` 在 SInt 上的行为，所以两者对同一组输入给出同一个商。
//  除零返回 0，也和上游一致。
//
//  延迟从 0 变成 `stages` 拍，所以调用方需要 valid 信号。这不是接口噪音：
//  流水化除法器改变模块延迟，延迟改变调度——正是 Compiler 和 µArch 必须
//  一起决定的那类耦合。

package predict_unit

import chisel3._
import chisel3.util._
import chisel3.experimental.FixedPoint

class FixedPointDivPipelined(
    val bitWidth: Int,
    val point: Int,
    val stages: Int,
) extends Module {
  require(bitWidth > 0 && point >= 0, s"bad format: bitWidth=$bitWidth point=$point")
  require(stages >= 1, s"stages must be at least 1, got $stages")

  val fpType = FixedPoint(bitWidth.W, point.BP)
  val io = IO(new Bundle {
    val in_valid = Input(Bool())
    val numerator = Input(fpType)
    val denominator = Input(fpType)
    val out_valid = Output(Bool())
    val quotient = Output(fpType)
  })

  // 被除数是 |num| << point，所以比输入宽 point 位；商最多和它一样宽，
  // 每次迭代出一位，因此迭代次数等于被除数位宽。
  private val dividendWidth = bitWidth + point
  private val iterations = dividendWidth
  // 最后一段可能短一些；用 ceil 保证总迭代数不少于需要的。
  private val perStage = (iterations + stages - 1) / stages

  /** 一级流水线之间携带的全部状态。 */
  private class DivState extends Bundle {
    val remainder = UInt((bitWidth + 1).W) // 比较时可能进位，多一位
    val quotient = UInt(dividendWidth.W)
    val dividend = UInt(dividendWidth.W)
    val divisor = UInt(bitWidth.W)
    val negative = Bool()
    val divideByZero = Bool()
    val valid = Bool()
  }

  // ---- 输入级：取绝对值，记下符号 ---------------------------------------
  private val numeratorS = io.numerator.asSInt
  private val denominatorS = io.denominator.asSInt

  private val initial = Wire(new DivState)
  initial.remainder := 0.U
  initial.quotient := 0.U
  // `.abs` 在最负值上会溢出回自身，这是二进制补码的固有性质，和上游的
  // `/` 表现一致；这里不额外处理，以免两者对同一输入给出不同的商。
  initial.dividend := (numeratorS.abs.asUInt << point)(dividendWidth - 1, 0)
  initial.divisor := denominatorS.abs.asUInt(bitWidth - 1, 0)
  initial.negative := (numeratorS < 0.S) ^ (denominatorS < 0.S)
  initial.divideByZero := denominatorS === 0.S
  initial.valid := io.in_valid

  /** 一次基 2 恢复除法迭代：取被除数的最高位，试减。 */
  private def step(state: DivState): DivState = {
    val next = Wire(new DivState)
    next := state

    val shifted = Cat(state.remainder(bitWidth - 1, 0), state.dividend(dividendWidth - 1))
    val trial = shifted.asUInt -& state.divisor
    val fits = shifted.asUInt >= state.divisor

    next.remainder := Mux(fits, trial(bitWidth, 0), shifted.asUInt)
    next.quotient := Cat(state.quotient(dividendWidth - 2, 0), fits.asUInt)
    // 被除数左移，把下一位送到最高位。
    next.dividend := Cat(state.dividend(dividendWidth - 2, 0), 0.U(1.W))
    next
  }

  // ---- 流水线主体 --------------------------------------------------------
  private var carried = initial
  private var remaining = iterations
  for (_ <- 0 until stages) {
    val here = math.min(perStage, remaining)
    for (_ <- 0 until here) carried = step(carried)
    remaining -= here
    // 段与段之间插一级寄存器。valid 跟着数据一起走，所以调用方看到的
    // out_valid 正好在商有效的那一拍拉高。
    carried = RegNext(carried, 0.U.asTypeOf(new DivState))
  }
  require(remaining == 0, s"pipeline covered ${iterations - remaining}/$iterations iterations")

  // ---- 输出级：套符号，截断到输出宽度 ------------------------------------
  private val magnitude = carried.quotient
  private val signed = Mux(carried.negative, 0.S - magnitude.asSInt, magnitude.asSInt)
  private val result = Mux(carried.divideByZero, 0.S, signed)

  io.out_valid := carried.valid
  io.quotient := result(bitWidth - 1, 0).asFixedPoint(point.BP)
}

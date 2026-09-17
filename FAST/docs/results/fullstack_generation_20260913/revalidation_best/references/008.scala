package execute_unit

import chisel3._
import chisel3.util._
import chisel3.experimental.FixedPoint

import exp_unit.ExpUnitFixPoint

class RePE(
    bits: Int,
    point: Int,
    regWidth: Int, // number of column regs feeding this PE
    colSelectBits: Int,
    id: (Int, Int)
) extends Module {
  val fpType = FixedPoint(bits.W, point.BP)
  val io = IO(new Bundle {
    val q_in = Input(fpType)               // row input (from Q buffer / reg chain)
    val reg_cols = Input(Vec(regWidth, fpType)) // column register inputs
    val out = Output(fpType)

    val sel_col = Input(UInt(colSelectBits.W))
    val acc_ctrl = Input(UInt(2.W))
    val exp_ctrl = Input(UInt(2.W))
  })

  val acc_clear :: acc_idle :: acc_accumulate :: acc_move_out :: Nil = Enum(4)
  val exp_idle :: exp_compute :: Nil = Enum(2)

  val exp_unit = Module(new ExpUnitFixPoint(bits, point, 6, 4))

  val a = Wire(fpType)      // row source
  val b = Wire(fpType)      // selected column
  val mul = Wire(fpType)    // product
  val acc = Reg(fpType)
  val score_exp = Reg(fpType)

  io.out := score_exp

  a := io.q_in
  switch(io.acc_ctrl) {
    is(acc_move_out) { a := score_exp }
  }

  val col_vec = Wire(Vec(regWidth + 1, fpType))
  for (i <- 0 until regWidth) col_vec(i) := io.reg_cols(i)
  col_vec(regWidth) := FixedPoint(0, bits.W, point.BP)

  var selW = when(io.sel_col === 0.U) {
    b := col_vec(0)
  }
  for (i <- 1 until (regWidth + 1)) {
    selW = selW.elsewhen(io.sel_col === i.U) {
      b := col_vec(i)
    }
  }
  selW.otherwise {
    b := col_vec(regWidth)
  }

  // FAST patch（缺陷 6）：上游的 `mul := a * b` 是**截断**，不是舍入。
  // FixedPoint(bits,point) 相乘产生 FixedPoint(2*bits,2*point)，赋回 fpType
  // 丢掉低 `point` 位小数——补码下那是 **floor**，误差恒为负、期望 -0.5 LSB。
  // QK^T 在 headDim 步上累加这个乘积，偏差因此**随 head_dim 线性累积**：
  // headDim=8 约 -4 ticks（容差里看不出来），headDim=64 实测平均 -29.8 ticks
  // （范围 [-37,-22]），2048 个输出维度有 1154 个超容差且**全部偏小**。
  // 加半个 LSB 再截断（四舍五入）后平均偏差 +0.75 ticks（范围 [-5,+7]），
  // 不再随维度累积。golden/fixedpoint.py 的 fp_mul 必须同步改，否则
  // 模块级金标准会反过来把正确的 RTL 判成错的。
  if (point > 0) {
    val product = (a * b).asSInt                     // 标度 2^-(2*point)
    val half = (BigInt(1) << (point - 1)).S
    val rounded = (product +& half) >> point         // 标度 2^-point
    val narrowed = rounded.asUInt
    mul := narrowed(bits - 1, 0).asFixedPoint(point.BP)
  } else {
    mul := a * b
  }

  switch(io.acc_ctrl) {
    is(acc_clear) { acc := FixedPoint(0, bits.W, point.BP) }
    is(acc_idle)  { acc := acc }
    is(acc_accumulate) { acc := acc + mul }
    is(acc_move_out) {
      acc := mul
      io.out := acc
    }
  }

  exp_unit.io.in_value := FixedPoint(0, bits.W, point.BP)
  switch(io.exp_ctrl) {
    is(exp_idle) { score_exp := score_exp }
    is(exp_compute) {
      exp_unit.io.in_value := acc
      score_exp := exp_unit.io.out_exp
    }
  }
}
// ============================================================================
//  ★ FAST 改动：预测通路从无符号改为有符号
// ============================================================================
//
//  和 prepe_1_2.scala 完全相同的问题，同样的改法。上游这条通路整个无符号
//  （端口 UInt(6.W)），而 DynaX 自己的软件是有符号量化的
//  （quant_utils.py: calc_max_quant_value(6) = 2^5 - 1 = ±31）。
//
//  于是软件按 sum(q*k) 排序，RTL 按 sum(|q|*|k|) 排序。在 1:2 通路上实测过
//  这个差异的后果：top-8 选择和精确分数的重合度从 75% 掉到 31%，改成有符号
//  之后回到 72%。位宽没变——差的全是符号。
//
//  1:4 的选择块是三级移位加四路比较器，比 1:2 复杂，但病根一样：
//  `Mux(a > b, a, b)` 比幅值**也传幅值**。「选谁」和「乘什么」是两件事。
//
//  改动都在下面就地标了 ★，和 1:2 一一对应：
//    1. 数据端口 UInt -> SInt，乘法和部分和随之有符号
//    2. 四路比较按**幅值**（软件用 argmax(abs)），但传下去的是**带符号**的值
//    3. exp 输入改符号扩展；去掉 `psum == 0 -> 输出 0` 的特例

package predict_unit

import chisel3._
import chisel3.util._
import chisel3.experimental.FixedPoint
import exp_unit.ExpUnitFixPoint

class PrePE_1_4(outBits: Int) extends Module {
  val io = IO(new Bundle {
    val left_in = Input(SInt(6.W))          // ★ UInt -> SInt
    val sel_in = Input(UInt(2.W))
    val top_in0 = Input(SInt(6.W))          // ★
    val top_in1 = Input(SInt(6.W))          // ★
    val top_in2 = Input(SInt(6.W))          // ★
    val top_in3 = Input(SInt(6.W))          // ★

    val right_out = Output(SInt(6.W))       // ★
    val sel_out = Output(UInt(2.W))
    val bottom_out0 = Output(SInt(6.W))     // ★
    val bottom_out1 = Output(SInt(6.W))     // ★
    val bottom_out2 = Output(SInt(6.W))     // ★
    val bottom_out3 = Output(SInt(6.W))     // ★

    val psum_in = Input(SInt(outBits.W))    // ★
    val psum_out = Output(SInt(outBits.W))  // ★

    val state = Input(UInt(2.W))
  })

  val sIdle :: sClear :: sCalc :: sInput :: Nil = Enum(4)

  val topReg0 = Reg(SInt(6.W))            // ★
  val topReg1 = Reg(SInt(6.W))            // ★
  val topReg2 = Reg(SInt(6.W))            // ★
  val topReg3 = Reg(SInt(6.W))            // ★
  val leftReg = Reg(SInt(6.W))            // ★
  val selReg = Reg(UInt(2.W))
  val psumReg = Reg(SInt(outBits.W))      // ★

  val inputCounter = RegInit(0.U(2.W))

  io.bottom_out0 := topReg0
  io.bottom_out1 := topReg1
  io.bottom_out2 := topReg2
  io.bottom_out3 := topReg3
  io.right_out := leftReg
  io.sel_out := selReg
  io.psum_out := psumReg

  switch(io.state) {
    is(sIdle) {
      topReg0 := topReg0
      topReg1 := topReg1
      topReg2 := topReg2
      topReg3 := topReg3
      leftReg := leftReg
      selReg := selReg
      psumReg := psumReg
      inputCounter := inputCounter
    }
    is(sClear) {
      topReg0 := 0.S                      // ★
      topReg1 := 0.S                      // ★
      topReg2 := 0.S                      // ★
      topReg3 := 0.S                      // ★
      leftReg := 0.S                      // ★
      selReg := 0.U
      psumReg := 0.S                      // ★
      inputCounter := 0.U
    }
    is(sCalc) {
      topReg0 := io.top_in0
      topReg1 := io.top_in1
      topReg2 := io.top_in2
      topReg3 := io.top_in3
      leftReg := leftReg
      selReg := selReg
      // ★ 有符号乘累加，`+&` 保住进位再按二进制补码截断回 outBits。
      psumReg := MuxLookup(selReg, 0.S(outBits.W), Seq(
        0.U -> (topReg0 * leftReg +& io.psum_in)(outBits - 1, 0).asSInt,
        1.U -> (topReg1 * leftReg +& io.psum_in)(outBits - 1, 0).asSInt,
        2.U -> (topReg2 * leftReg +& io.psum_in)(outBits - 1, 0).asSInt,
        3.U -> (topReg3 * leftReg +& io.psum_in)(outBits - 1, 0).asSInt
      ))
    }
    is(sInput) {
      when(inputCounter === 3.U) {
        leftReg := io.left_in
        selReg := io.sel_in
      } .otherwise {
        leftReg := leftReg
        selReg := selReg
      }
      inputCounter := Mux(inputCounter === 3.U, 0.U, inputCounter + 1.U)
      topReg0 := 0.S                      // ★
      topReg1 := 0.S                      // ★
      topReg2 := 0.S                      // ★
      topReg3 := 0.S                      // ★
      psumReg := 0.S                      // ★
    }
  }
}

class PrePEArray_1_4(
    bits: Int,
    point: Int,
    append: Int,
    internalBits: Int,
    width: Int,
    height: Int
) extends Module {
  val fpType = FixedPoint(bits.W, point.BP)
  val io = IO(new Bundle {
    val left_in = Input(Vec(height, SInt(6.W)))   // ★
    val top_in = Input(Vec(width, SInt(6.W)))     // ★
    val s_out = Output(Vec(height, fpType))
    val exp_sum = Output(Vec(height, fpType))
    val exp_sum_m = Output(Vec(height, fpType))
    val valid = Output(Vec(height, Bool()))

    val pes_state = Input(UInt(2.W))
    val array_state = Input(UInt(2.W))
  })

  val aIdle :: aClear :: aCalc :: Nil = Enum(3)

  require(width % 4 == 0, "width must be multiple of 4 for 1_4 PE layout")

  val pes = (for (r <- 0 until height)
    yield for (c <- 0 until width / 4) yield Module(new PrePE_1_4(internalBits)))

  val l_first = RegInit(VecInit(Seq.fill(height)(0.S(6.W))))   // ★
  val l_second = RegInit(VecInit(Seq.fill(height)(0.S(6.W))))  // ★
  val l_third = RegInit(VecInit(Seq.fill(height)(0.S(6.W))))   // ★
  val cycleCount = RegInit(0.U(2.W))

  when(cycleCount === 3.U) {
    for (i <- 0 until height) {
      pes(i)(0).io.psum_in := 0.S      // ★
      val a = io.left_in(i)
      val b = l_first(i)
      val c = l_second(i)
      val d = l_third(i)

      // ★ 四路比较按**幅值**（软件用 argmax(abs)），但一路传下去的是
      // **带符号**的值。上游比幅值也传幅值，于是和 query 反相关的 key
      // 被当成最重要的——1:2 通路上实测这会让选择质量从 75% 掉到 31%。
      val firstWins01 = a.abs > b.abs
      val max01 = Mux(firstWins01, a, b)
      val idx01 = Mux(firstWins01, 0.U(2.W), 1.U(2.W))
      val firstWins23 = c.abs > d.abs
      val max23 = Mux(firstWins23, c, d)
      val idx23 = Mux(firstWins23, 2.U(2.W), 3.U(2.W))
      val topWins = max01.abs > max23.abs
      val maxAll = Mux(topWins, max01, max23)
      val idxAll = Mux(topWins, idx01, idx23)

      pes(i)(0).io.left_in := maxAll
      pes(i)(0).io.sel_in := idxAll
    }
    cycleCount := 0.U
    // rotate/clear shift regs after selection
    for (i <- 0 until height) {
      l_first(i) := 0.S                   // ★
      l_second(i) := 0.S                  // ★
      l_third(i) := 0.S                   // ★
    }
  } .otherwise {
    for (i <- 0 until height) {
      pes(i)(0).io.psum_in := 0.S      // ★
      pes(i)(0).io.left_in := 0.S      // ★
      pes(i)(0).io.sel_in := 0.U

      l_third(i) := l_second(i)
      l_second(i) := l_first(i)
      l_first(i) := io.left_in(i)
    }
    cycleCount := cycleCount + 1.U
  }

  for (c <- 0 until width / 4) {
    pes(0)(c).io.top_in0 := io.top_in(c * 4)
    pes(0)(c).io.top_in1 := io.top_in(c * 4 + 1)
    pes(0)(c).io.top_in2 := io.top_in(c * 4 + 2)
    pes(0)(c).io.top_in3 := io.top_in(c * 4 + 3)
  }

  for (r <- 0 until height) {
    for (c <- 1 until width / 4) {
      pes(r)(c).io.left_in := pes(r)(c - 1).io.right_out
      pes(r)(c).io.psum_in := pes(r)(c - 1).io.psum_out
      pes(r)(c).io.sel_in := pes(r)(c - 1).io.sel_out
    }
  }

  for (r <- 1 until height) {
    for (c <- 0 until width / 4) {
      pes(r)(c).io.top_in0 := pes(r - 1)(c).io.bottom_out0
      pes(r)(c).io.top_in1 := pes(r - 1)(c).io.bottom_out1
      pes(r)(c).io.top_in2 := pes(r - 1)(c).io.bottom_out2
      pes(r)(c).io.top_in3 := pes(r - 1)(c).io.bottom_out3
    }
  }

  for (r <- 0 until height; c <- 0 until width / 4) {
    pes(r)(c).io.state := io.pes_state
  }

  val exps = for (i <- 0 until height) yield Module(new ExpUnitFixPoint(bits, point, 6, 4))

  val sumRegs = Reg(Vec(height, fpType))
  val sumRegsM = Reg(Vec(height, fpType))
  val counts = RegInit(VecInit(Seq.fill(height)(0.U(5.W))))
  val validFlags = RegInit(VecInit(Seq.fill(height)(false.B)))
  val expRegs = Reg(Vec(height, fpType))

  io.s_out := expRegs
  io.exp_sum := sumRegs
  io.exp_sum_m := sumRegsM
  io.valid := validFlags

  for (i <- 0 until height) {
    val tail = pes(i)(width / 4 - 1).io.psum_out
    // ★ 零扩展改为**符号扩展**：psum 现在是 SInt，负分数必须保持为负，
    // 否则指数单元会把它当成一个很大的正数。`pad` 对 SInt 做符号扩展。
    exps(i).io.in_value := (tail << append).asSInt.pad(bits)(bits - 1, 0).asFixedPoint(point.BP)

    // ★ 去掉 `psum == 0 -> 输出 0` 的特例。有符号下 0 是正常的中间分数，
    // 强制归零会把它排到所有负分数之下（负分数的 exp 是正数），破坏 exp
    // 的单调性——而排序正是这个单元的全部作用。
    expRegs(i) := exps(i).io.out_exp
  }

  switch(io.array_state) {
    is(aIdle) {
      for (i <- 0 until height) {
        sumRegs(i) := sumRegs(i)
        sumRegsM(i) := sumRegsM(i)
        expRegs(i) := expRegs(i)
        counts(i) := counts(i)
        validFlags(i) := validFlags(i)
      }
    }
    is(aClear) {
      for (i <- 0 until height) {
        sumRegs(i) := 0.F(bits.W, point.BP)
        sumRegsM(i) := 0.F(bits.W, point.BP)
        expRegs(i) := 0.F(bits.W, point.BP)
        counts(i) := 0.U
        validFlags(i) := false.B
      }
    }
    is(aCalc) {
      for (i <- 0 until height) {
        sumRegs(i) := sumRegs(i) + expRegs(i)
        when(expRegs(i) > 0.F(bits.W, point.BP)) {
          counts(i) := counts(i) + 1.U
        }

        when(counts(i) === 31.U) {
          validFlags(i) := true.B
          sumRegsM(i) := sumRegsM(i) + expRegs(i)
        } .elsewhen(counts(i) === 0.U) {
          validFlags(i) := false.B
          sumRegsM(i) := 0.F(bits.W, point.BP) + expRegs(i)
        } .otherwise {
          validFlags(i) := false.B
          sumRegsM(i) := sumRegsM(i) + expRegs(i)
        }
      }
    }
  }
}
// ============================================================================
//  ★ FAST 改动：预测通路从无符号改为有符号
// ============================================================================
//
//  上游这条通路整个是无符号的（端口都是 UInt(4.W)），而 DynaX **自己的
//  软件**是有符号量化的：
//
//      quant_utils.py   calc_max_quant_value(bits) = 2^(bits-1) - 1   ->  ±7
//      prepe_1_2.scala  left_in = Input(UInt(4.W))                    ->  0..15
//
//  于是软件按 sum(q*k) 排序，RTL 按 sum(|q|*|k|) 排序。这不是精度差异，
//  是**方向错误**：一个和 query 反相关的 key，逐项乘积为负、总分很低，
//  softmax 里权重极小；取绝对值之后同一项从「最强的反对票」变成「最强的
//  赞成票」。
//
//  真实数据里的一例（TinyLlama 第 10 层第 0 头，query 行 0，key 24）：
//
//      维度 0：q = -0.281,  k = +5.590  ->  q*k = -1.572,  |q|*|k| = +1.572
//      合计：sum(q*k)     = -1.93  排名 32/32，不选
//            sum(|q|*|k|) = +2.39  排名  4/32，选中
//
//  实测后果，top-8 选择和精确分数的重合度：
//
//      DynaX 软件近似（有符号 4-bit）   24/32 = 75%
//      上游 RTL（无符号 4-bit）         10/32 = 31%
//
//  位宽一样，差的 44 个百分点全是符号造成的——「4-bit 太粗」不是原因。
//
//  改硬件而不是改软件：软件是规格，这个加速器存在的目的就是跑它，
//  论文报告的精度数字也来自它。
//
//  三处改动，都在下面就地标了 ★：
//    1. 数据端口 UInt -> SInt，乘法和部分和随之有符号
//    2. 1:2 选择仍按**幅值**比（软件用 argmax(abs)），但传下去的是**带符号**
//       的值——「选谁」和「乘什么」是两件事，上游把它们混在了一起
//    3. 去掉 `psum == 0 -> exp 输出 0` 的特例：无符号下它表示「没有任何
//       贡献」，有符号下 0 是正常的中间分数，强制归零会破坏 exp 的单调性，
//       也就破坏排序本身
//
//  注意：prepe_1_4.scala 有完全相同的问题（UInt(6.W)），尚未改。

package predict_unit

import chisel3._
import chisel3.util._
import chisel3.experimental.FixedPoint
import exp_unit.ExpUnitFixPoint

class PrePE_1_2(outBits: Int) extends Module {
  val io = IO(new Bundle {
    val left_in = Input(SInt(4.W))          // ★ UInt -> SInt
    val sel_in = Input(UInt(1.W))
    val top_in0 = Input(SInt(4.W))          // ★
    val top_in1 = Input(SInt(4.W))          // ★

    val right_out = Output(SInt(4.W))       // ★
    val sel_out = Output(UInt(1.W))
    val bottom_out0 = Output(SInt(4.W))     // ★
    val bottom_out1 = Output(SInt(4.W))     // ★

    val psum_in = Input(SInt(outBits.W))    // ★
    val psum_out = Output(SInt(outBits.W))  // ★

    val state = Input(UInt(2.W))
  })

  val sIdle :: sClear :: sCalc :: sInput :: Nil = Enum(4)

  val topReg0 = Reg(SInt(4.W))            // ★
  val topReg1 = Reg(SInt(4.W))            // ★
  val leftReg = Reg(SInt(4.W))            // ★
  val selReg = Reg(UInt(1.W))
  val psumReg = Reg(SInt(outBits.W))      // ★

  val inputCounter = RegInit(0.U(1.W))

  io.bottom_out0 := topReg0
  io.bottom_out1 := topReg1
  io.right_out := leftReg
  io.sel_out := selReg
  io.psum_out := psumReg

  switch(io.state) {
    is(sIdle) {
      topReg0 := topReg0
      topReg1 := topReg1
      leftReg := leftReg
      selReg := selReg
      psumReg := psumReg
    }
    is(sClear) {
      topReg0 := 0.S                        // ★
      topReg1 := 0.S                        // ★
      leftReg := 0.S                        // ★
      selReg := 0.U
      psumReg := 0.S                        // ★
      inputCounter := 0.U
    }
    is(sCalc) {
      topReg0 := io.top_in0
      topReg1 := io.top_in1
      leftReg := leftReg
      selReg := selReg
      // ★ 有符号乘累加。`+&` 保住进位再按二进制补码截断回 outBits——
      // 和上游的无符号截断是同一种窄化行为，只是保留了符号。
      psumReg := Mux(selReg === 0.U,
                     (topReg0 * leftReg +& io.psum_in)(outBits - 1, 0).asSInt,
                     (topReg1 * leftReg +& io.psum_in)(outBits - 1, 0).asSInt)
    }
    is(sInput) {
      when(inputCounter === 1.U) {
        leftReg := io.left_in
        selReg := io.sel_in
      }
      inputCounter := inputCounter + 1.U
      topReg0 := 0.S                        // ★
      topReg1 := 0.S                        // ★
      psumReg := 0.S                        // ★
    }
  }
}

class PrePEArray_1_2(
    bits: Int,
    point: Int,
    append: Int,
    internalBits: Int,
    width: Int,
    height: Int
) extends Module {
  val fpType = FixedPoint(bits.W, point.BP)
  val io = IO(new Bundle {
    val left_in = Input(Vec(height, SInt(4.W)))   // ★
    val top_in = Input(Vec(width, SInt(4.W)))     // ★
    val s_out = Output(Vec(height, fpType))
    val exp_sum = Output(Vec(height, fpType))
    val exp_sum_m = Output(Vec(height, fpType))
    val valid = Output(Vec(height, Bool()))

    val pes_state = Input(UInt(2.W))
    val array_state = Input(UInt(2.W))
  })

  val aIdle :: aClear :: aCalc :: Nil = Enum(3)

  val pes = (for (i <- 0 until height)
    yield for (j <- 0 until width / 2) yield Module(new PrePE_1_2(internalBits)))

  val leftFirstReg = Reg(Vec(height, SInt(4.W)))  // ★
  val cycleToggle = RegInit(0.U(1.W))

  when(cycleToggle === 0.U) {
    leftFirstReg := io.left_in
    for (i <- 0 until height) {
      pes(i)(0).io.psum_in := 0.S                 // ★
      pes(i)(0).io.left_in := 0.S                 // ★
      pes(i)(0).io.sel_in := 0.U
    }
    cycleToggle := 1.U
  } .otherwise {
    for (i <- 0 until height) {
      pes(i)(0).io.psum_in := 0.S
      // ★ 「选谁」和「乘什么」是两件事，上游把它们混在了一起：
      //   选谁   —— 按**幅值**比，和软件的 argmax(abs) 一致
      //   乘什么 —— 传**带符号**的那个值，这样乘积保留方向
      // 上游比幅值也传幅值，于是反相关的 key 被当成最重要的。
      val firstWins = leftFirstReg(i).abs > io.left_in(i).abs
      pes(i)(0).io.left_in := Mux(firstWins, leftFirstReg(i), io.left_in(i))
      pes(i)(0).io.sel_in := Mux(firstWins, 1.U, 0.U)
    }
    cycleToggle := 0.U
  }

  for (j <- 0 until width / 2) {
    pes(0)(j).io.top_in0 := io.top_in(j * 2)
    pes(0)(j).io.top_in1 := io.top_in(j * 2 + 1)
  }

  for (r <- 0 until height) {
    for (c <- 1 until width / 2) {
      pes(r)(c).io.left_in := pes(r)(c - 1).io.right_out
      pes(r)(c).io.psum_in := pes(r)(c - 1).io.psum_out
      pes(r)(c).io.sel_in := pes(r)(c - 1).io.sel_out
    }
  }

  for (r <- 1 until height) {
    for (c <- 0 until width / 2) {
      pes(r)(c).io.top_in0 := pes(r - 1)(c).io.bottom_out0
      pes(r)(c).io.top_in1 := pes(r - 1)(c).io.bottom_out1
    }
  }

  for (r <- 0 until height; c <- 0 until width / 2) {
    pes(r)(c).io.state := io.pes_state
  }

  val exps = for (i <- 0 until height) yield Module(new ExpUnitFixPoint(bits, point, 6, 4))

  val sumRegs = Reg(Vec(height, fpType))
  val sumRegsM = Reg(Vec(height, fpType))
  val counts = Reg(Vec(height, UInt(5.W)))
  val validFlags = Reg(Vec(height, Bool()))
  val expRegs = Reg(Vec(height, fpType))

  io.s_out := expRegs
  io.exp_sum := sumRegs
  io.exp_sum_m := sumRegsM
  io.valid := validFlags

  for (i <- 0 until height) {
    val tail = pes(i)(width / 2 - 1).io.psum_out
    // ★ 零扩展改为**符号扩展**：psum 现在是 SInt，负分数必须保持为负，
    // 否则指数单元会把它当成一个很大的正数。`pad` 对 SInt 做符号扩展。
    exps(i).io.in_value := (tail << append).asSInt.pad(bits)(bits - 1, 0).asFixedPoint(point.BP)

    // ★ 去掉 `psum == 0 -> 输出 0` 的特例。
    //
    // 无符号下它是合理的：psum 为 0 意味着所有乘积都是 0，也就是「这个
    // key 没有任何贡献」，给它 exp(0)=1 的权重反而不对。
    //
    // 有符号下它是错的：0 是一个正常的中间分数，介于负分数和正分数之间。
    // 强制归零会把它排到**所有负分数之下**——而负分数的 exp 是正数。
    // 这破坏了 exp 的单调性，也就破坏了排序本身，而排序是这个单元的
    // 全部作用。
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
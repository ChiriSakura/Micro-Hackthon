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

/** 控制广播的寄存器树：把一个信号扇出到 N 个负载，每级扇出有上界。
  *
  * ## 为什么需要
  *
  * `pes_state` 是一个 2 位控制信号，从**单个输入端口直接驱动**全部
  * height x width/2 个 PE 的 state 端口——计划尺寸下是 1024-2048 个负载，
  * 中间没有任何缓冲。
  *
  * 这个项目已经量到过它的后果：`PrePEArray_1_4` 里一个 NOR2_X1 报出
  * **196 ns**（Nangate45 的真实单元延迟约 0.02 ns，差 4000 倍），起点正是
  * 广播给 512 个 PE 的 `io_array_state`。时序适配器因此有一道
  * `timing_credible` 守卫，把这类结果整个丢掉——**于是预测阵列的时序从来
  * 没有可用的数**。
  *
  * ## 为什么是均匀深度
  *
  * 所有 PE 必须在**同一拍**看到同一个状态，否则阵列自己就失步了。所以树的
  * 每条路径深度相同：整体延迟 `stages` 拍，但彼此同步。
  *
  * `pes_state` 和 `array_state` 必须走**同样的深度**——前者驱动 PE、后者
  * 驱动行累加器，而累加器消费的正是 PE 产出的 expRegs。只延迟一个会让两者
  * 错拍。
  *
  * ## dontTouch 不是可选的
  *
  * yosys 的 `opt_merge` 会把这些寄存器识别成等价的并合并回一个——那样整棵树
  * 消失，扇出原样不动，而且**不会有任何报错**。
  */
object ControlBroadcast {
  /** 每个寄存器最多驱动多少个下级。16 是个保守取值：Nangate45 的
    * 反相器驱动十几个同类负载仍在正常延迟范围内。 */
  val MaxFanout = 16

  def apply(source: UInt, loads: Int, stages: Int): IndexedSeq[UInt] = {
    require(loads > 0)
    if (stages <= 0) return IndexedSeq.fill(loads)(source)
    var level: IndexedSeq[UInt] = IndexedSeq(source)
    var stageIndex = 0
    for (_ <- 0 until stages) {
      val width = math.min(loads, level.length * MaxFanout)
      val stage = stageIndex
      level = (0 until width).map { j =>
        val reg = RegNext(level(j * level.length / width), 0.U(source.getWidth.W))
        // **名字是给 yosys 用的。** Chisel 的 `dontTouch` 只管到 FIRRTL 那
        // 一层；到了 yosys，`opt_merge` 看见一堆功能等价的寄存器就会合并回
        // 一个——整棵树消失、扇出原样不动，**而且不报任何错**。
        //
        // 实测就是这样：加了两级树之后 STA 仍然报一个 DFF 驱动 516 个负载
        // （= 512 个 PE 的总数），到达时间 69.37 ns，比扁平的 62.68 还差。
        //
        // 所以综合脚本要按这个名字 `setattr -set keep 1`，而这个名字必须
        // 稳定。
        reg.suggestName(s"ctrl_bcast_s${stage}_$j")
        chisel3.dontTouch(reg)
        reg
      }
      stageIndex += 1
    }
    val leaves = level
    (0 until loads).map(k => leaves(k * leaves.length / loads))
  }
}

class PrePEArray_1_2(
    bits: Int,
    point: Int,
    append: Int,
    internalBits: Int,
    width: Int,
    height: Int,
    /** 控制广播树的级数。0 = 原来的扁平广播（保持既有行为和测试）。
      *
      * 大于 0 时 `pes_state` / `array_state` 经过这么多级寄存器才到达负载，
      * 每级扇出不超过 `ControlBroadcast.MaxFanout`。**整个预测流水因此
      * 相对外部控制器延后 stages 拍**，驱动方必须把每个相位多保持这么久。
      */
    broadcastStages: Int = 0
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

  // **控制广播走寄存器树，不再从一个端口直连上千个负载。**
  // 两个状态信号走同样的深度：`pes_state` 驱动 PE，`array_state` 驱动行
  // 累加器，而累加器消费的正是 PE 产出的 expRegs——只延迟一个会让两者错拍。
  private val peLoads = height * (width / 2)
  private val pesStateFanned = ControlBroadcast(io.pes_state, peLoads, broadcastStages)
  private val arrayStateFanned =
    ControlBroadcast(io.array_state, height, broadcastStages)

  for (r <- 0 until height; c <- 0 until width / 2) {
    pes(r)(c).io.state := pesStateFanned(r * (width / 2) + c)
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

  // 每行用自己的那片叶子：行累加器有 height 个实例，扁平广播时
  // `io.array_state` 直连全部——这正是实测报出 196 ns 那条路径的起点。
  // **每行用自己的那片叶子。** 把 switch 拆进每行的循环，语义不变（所有
  // 叶子在同一拍携带同一个值），但译码后的控制信号只驱动这一行的寄存器。
  //
  // 写成 `switch(arrayStateFanned(0))` 再在里面循环全部行是不够的：那样
  // 树只是多了几级寄存器，译码出来的 enable 仍然扇出到所有行——扇出没被
  // 约束，而看上去像是修好了。
  for (i <- 0 until height) {
    switch(arrayStateFanned(i)) {
      is(aIdle) {
        sumRegs(i) := sumRegs(i)
        sumRegsM(i) := sumRegsM(i)
        expRegs(i) := expRegs(i)
        counts(i) := counts(i)
        validFlags(i) := validFlags(i)
      }
      is(aClear) {
        sumRegs(i) := 0.F(bits.W, point.BP)
        sumRegsM(i) := 0.F(bits.W, point.BP)
        expRegs(i) := 0.F(bits.W, point.BP)
        counts(i) := 0.U
        validFlags(i) := false.B
      }
      is(aCalc) {
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
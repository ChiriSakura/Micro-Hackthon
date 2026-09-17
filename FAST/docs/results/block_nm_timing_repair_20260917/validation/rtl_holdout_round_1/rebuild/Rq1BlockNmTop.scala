import chisel3._
import chisel3.util._

class Rq1BlockNmTop extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val start = IO(Input(Bool()))
  val q = IO(Input(UInt(8.W)))
  val k = IO(Input(UInt(128.W)))
  val v = IO(Input(UInt(128.W)))
  val done = IO(Output(Bool()))
  val result = IO(Output(SInt(16.W)))
  val keep_mask = IO(Output(UInt(16.W)))

  // Instantiate child modules
  val find_min_lo = Module(new FindMin8)
  val find_min_hi = Module(new FindMin8)
  val divider = Module(new DividerWrapper)

  divider.clock := clock
  divider.reset := reset

  withClockAndReset(clock, reset) {
    // FSM state definitions
    val sIdle :: sCalcScores :: sPipeS1Max :: sPipeS2Mask :: sPipeS3Exp :: sAccumulate :: sDivStart :: sDivWait :: sDonePulse :: Nil = Enum(9)
    val state = RegInit(sIdle)

    // Registers for inputs and intermediate values
    val q_reg = Reg(UInt(8.W))
    val k_reg = Reg(UInt(128.W))
    val v_reg = Reg(UInt(128.W))

    val cycle_counter = Reg(UInt(4.W)) // 4 bits for up to 16 cycles

    val scores_reg = Reg(Vec(16, SInt(9.W)))
    val h_reg = Reg(SInt(9.W))
    val keep_mask_reg = Reg(UInt(16.W))
    val exp_vals_reg = Reg(Vec(16, UInt(16.W)))
    
    val n_acc = Reg(SInt(28.W))
    val d_acc = Reg(UInt(20.W))

    // Output registers
    val result_reg = Reg(SInt(16.W))
    val keep_mask_out_reg = Reg(UInt(16.W))

    // Exponential lookup table (ROM)
    val exp_rom = VecInit(Seq(
      65535.U(16.W), 61564.U(16.W), 57834.U(16.W), 54330.U(16.W), 51039.U(16.W), 47946.U(16.W), 45042.U(16.W), 42313.U(16.W),
      39749.U(16.W), 37341.U(16.W), 35078.U(16.W), 32953.U(16.W), 30957.U(16.W), 29081.U(16.W), 27319.U(16.W), 25664.U(16.W),
      24109.U(16.W), 22648.U(16.W), 21276.U(16.W), 19987.U(16.W), 18776.U(16.W), 17639.U(16.W), 16570.U(16.W), 15566.U(16.W),
      14623.U(16.W), 13737.U(16.W), 12905.U(16.W), 12123.U(16.W), 11388.U(16.W), 10698.U(16.W), 10050.U(16.W), 9441.U(16.W),
      8869.U(16.W), 8332.U(16.W), 7827.U(16.W), 7353.U(16.W), 6907.U(16.W), 6489.U(16.W), 6096.U(16.W), 5726.U(16.W),
      5379.U(16.W), 5054.U(16.W), 4747.U(16.W), 4460.U(16.W), 4190.U(16.W), 3936.U(16.W), 3697.U(16.W), 3473.U(16.W),
      3263.U(16.W), 3065.U(16.W), 2879.U(16.W), 2705.U(16.W), 2541.U(16.W), 2387.U(16.W), 2242.U(16.W), 2107.U(16.W),
      1979.U(16.W), 1859.U(16.W), 1746.U(16.W), 1641.U(16.W), 1541.U(16.W), 1448.U(16.W), 1360.U(16.W), 1278.U(16.W),
      1200.U(16.W), 1128.U(16.W), 1059.U(16.W), 995.U(16.W), 935.U(16.W), 878.U(16.W), 825.U(16.W), 775.U(16.W),
      728.U(16.W), 684.U(16.W), 642.U(16.W), 604.U(16.W), 567.U(16.W), 533.U(16.W), 500.U(16.W), 470.U(16.W),
      442.U(16.W), 415.U(16.W), 390.U(16.W), 366.U(16.W), 344.U(16.W), 323.U(16.W), 303.U(16.W), 285.U(16.W),
      268.U(16.W), 252.U(16.W), 236.U(16.W), 222.U(16.W), 209.U(16.W), 196.U(16.W), 184.U(16.W), 173.U(16.W),
      162.U(16.W), 153.U(16.W), 143.U(16.W), 135.U(16.W), 127.U(16.W), 119.U(16.W), 112.U(16.W), 105.U(16.W),
      99.U(16.W), 93.U(16.W), 87.U(16.W), 82.U(16.W), 77.U(16.W), 72.U(16.W), 68.U(16.W), 64.U(16.W),
      60.U(16.W), 56.U(16.W), 53.U(16.W), 50.U(16.W), 47.U(16.W), 44.U(16.W), 41.U(16.W), 39.U(16.W),
      36.U(16.W), 34.U(16.W), 32.U(16.W), 30.U(16.W), 28.U(16.W), 27.U(16.W), 25.U(16.W), 23.U(16.W),
      22.U(16.W), 21.U(16.W), 19.U(16.W), 18.U(16.W), 17.U(16.W), 16.U(16.W), 15.U(16.W), 14.U(16.W),
      13.U(16.W), 13.U(16.W), 12.U(16.W), 11.U(16.W), 10.U(16.W), 10.U(16.W), 9.U(16.W), 9.U(16.W),
      8.U(16.W), 8.U(16.W), 7.U(16.W), 7.U(16.W), 6.U(16.W), 6.U(16.W), 6.U(16.W), 5.U(16.W),
      5.U(16.W), 5.U(16.W), 4.U(16.W), 4.U(16.W), 4.U(16.W), 4.U(16.W), 3.U(16.W), 3.U(16.W),
      3.U(16.W), 3.U(16.W), 3.U(16.W), 2.U(16.W), 2.U(16.W), 2.U(16.W), 2.U(16.W), 2.U(16.W),
      2.U(16.W), 2.U(16.W), 2.U(16.W), 1.U(16.W), 1.U(16.W), 1.U(16.W), 1.U(16.W), 1.U(16.W),
      1.U(16.W), 1.U(16.W), 1.U(16.W), 1.U(16.W), 1.U(16.W), 1.U(16.W), 1.U(16.W), 1.U(16.W),
      1.U(16.W), 1.U(16.W), 1.U(16.W), 1.U(16.W), 1.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W),
      0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W),
      0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W),
      0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W),
      0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W),
      0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W),
      0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W),
      0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W),
      0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W), 0.U(16.W)
    ))

    // Default assignments
    done := false.B
    find_min_lo.scores_in := 0.U(72.W)
    find_min_hi.scores_in := 0.U(72.W)
    divider.valid_in := false.B
    divider.numer_in := 0.S(32.W)
    divider.denom_in := 0.U(20.W)

    def signedMax(a: SInt, b: SInt): SInt = Mux(a > b, a, b)

    // FSM logic
    switch(state) {
      is(sIdle) {
        when(start) {
          q_reg := q
          k_reg := k
          v_reg := v
          cycle_counter := 0.U
          state := sCalcScores
        }
      }

      is(sCalcScores) {
        val i = cycle_counter
        val q0 = q_reg(3, 0).asSInt
        val q1 = q_reg(7, 4).asSInt
        
        val base_k_idx = i << 3
        val k0 = (k_reg >> base_k_idx)(3, 0).asSInt
        val k1 = (k_reg >> (base_k_idx + 4.U))(3, 0).asSInt
        
        scores_reg(i) := (q0 * k0) +& (q1 * k1)

        cycle_counter := cycle_counter + 1.U
        when(i === 15.U) {
          state := sPipeS1Max
        }
      }

      is(sPipeS1Max) {
        // Balanced reduction tree to find the maximum score, fixing timing violation.
        // The previous implementation's use of .reduce() created a long serial chain.
        val l1_max = Seq.tabulate(8)(i => signedMax(scores_reg(2 * i), scores_reg(2 * i + 1)))
        val l2_max = Seq.tabulate(4)(i => signedMax(l1_max(2 * i), l1_max(2 * i + 1)))
        val l3_max = Seq.tabulate(2)(i => signedMax(l2_max(2 * i), l2_max(2 * i + 1)))
        val final_max = signedMax(l3_max(0), l3_max(1))

        h_reg := final_max
        state := sPipeS2Mask
      }

      is(sPipeS2Mask) {
        find_min_lo.scores_in := Cat(scores_reg.slice(0, 8).reverse.map(_.asUInt))
        find_min_hi.scores_in := Cat(scores_reg.slice(8, 16).reverse.map(_.asUInt))
        keep_mask_reg := Cat(find_min_hi.keep_mask_out, find_min_lo.keep_mask_out)
        state := sPipeS3Exp
      }

      is(sPipeS3Exp) {
        for (i <- 0 until 16) {
          val delta = (h_reg - scores_reg(i)).asUInt
          exp_vals_reg(i) := exp_rom(delta(7, 0))
        }
        cycle_counter := 0.U
        n_acc := 0.S
        d_acc := 0.U
        state := sAccumulate
      }

      is(sAccumulate) {
        val i = cycle_counter
        
        val current_e = exp_vals_reg(i)
        val base_v_idx = i << 3
        val current_v = (v_reg >> base_v_idx)(7, 0).asSInt
        val current_keep = keep_mask_reg(i)

        val product = Cat(0.U(1.W), current_e).asSInt * current_v

        when(current_keep) {
          d_acc := d_acc +& current_e
          n_acc := n_acc +& product
        }

        cycle_counter := cycle_counter + 1.U
        when(i === 15.U) {
          state := sDivStart
        }
      }

      is(sDivStart) {
        divider.valid_in := true.B
        when (d_acc === 0.U) {
          divider.numer_in := 0.S(32.W)
          divider.denom_in := 1.U(20.W)
        } .otherwise {
          divider.numer_in := (n_acc << 4)
          divider.denom_in := d_acc
        }
        
        keep_mask_out_reg := keep_mask_reg
        
        state := sDivWait
      }

      is(sDivWait) {
        when(divider.valid_out) {
          result_reg := divider.quotient_out
          state := sDonePulse
        }
      }

      is(sDonePulse) {
        done := true.B
        state := sIdle
      }
    }

    result := result_reg
    keep_mask := keep_mask_out_reg
  }
}

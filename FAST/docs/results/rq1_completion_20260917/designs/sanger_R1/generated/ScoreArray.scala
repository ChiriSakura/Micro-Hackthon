import chisel3._
import chisel3.util._

class ScoreArray extends RawModule {
  val clock = IO(Input(Clock()))
  val reset = IO(Input(Bool()))
  val valid_input = IO(Input(Bool()))
  val q_in = IO(Input(UInt(8.W)))
  val k_in = IO(Input(UInt(128.W)))
  val valid_output = IO(Output(Bool()))
  val scores_out = IO(Output(UInt(144.W)))

  // --- Combinational Logic ---

  // Extract 4-bit signed query components from q_in.
  // q[0] is in bits 3:0, q[1] is in bits 7:4.
  val q0 = q_in(3, 0).asSInt
  val q1 = q_in(7, 4).asSInt

  // Compute 16 scores in parallel.
  val scores_comb = Seq.tabulate(16) { i =>
    // Extract 4-bit signed key components for key vector 'i'.
    // Per the packing rule k[i][d] at 4*(2*i+d):
    // k[i][0] is at bit index 8*i
    // k[i][1] is at bit index 8*i + 4
    val k_i0 = k_in(8 * i + 3, 8 * i).asSInt
    val k_i1 = k_in(8 * i + 7, 8 * i + 4).asSInt

    // SInt(4) * SInt(4) -> SInt(8)
    val p0 = q0 * k_i0
    val p1 = q1 * k_i1

    // Use widening addition (+&) to prevent overflow, as specified.
    // SInt(8) +& SInt(8) -> SInt(9)
    p0 +& p1
  }

  // Concatenate the 16 9-bit signed scores into a single 144-bit UInt.
  // The .reverse is necessary because Cat(msb, ..., lsb) and the behavior
  // model's spack(width, lsb, ...) have opposite ordering conventions.
  val scores_cat = Cat(scores_comb.map(_.asUInt).reverse)

  // --- Pipelining Stage (1 cycle latency) ---

  // Register the combinational results to meet the 1-cycle latency requirement.
  // Use withClockAndReset for all register creation as per the compiler prompt.
  withClockAndReset(clock, reset) {
    scores_out := RegNext(scores_cat, 0.U(144.W))
    valid_output := RegNext(valid_input, false.B)
  }
}

import chisel3._

class ScoreCalculatorBank extends RawModule {
  val q_in = IO(Input(UInt(8.W)))
  val k_in = IO(Input(UInt(32.W)))
  val scores_out = IO(Output(UInt(36.W)))

  // Unpack q vector according to protocol: q[d] at bits 4*d +:4
  val q0 = q_in(3, 0)
  val q1 = q_in(7, 4)

  // Unpack k vectors according to protocol: k[i][d] at 4*(2*i+d) +:4
  // Lane 0
  val k00 = k_in(3, 0)
  val k01 = k_in(7, 4)
  // Lane 1
  val k10 = k_in(11, 8)
  val k11 = k_in(15, 12)
  // Lane 2
  val k20 = k_in(19, 16)
  val k21 = k_in(23, 20)
  // Lane 3
  val k30 = k_in(27, 24)
  val k31 = k_in(31, 28)

  // Calculate scores in parallel for each of the four lanes.
  // score[i] = (q0 * k[i][0]) + (q1 * k[i][1])
  // Each product of two 4-bit UInts is an 8-bit UInt.
  // The sum of two 8-bit UInts is a 9-bit UInt.
  val score0 = (q0 * k00) + (q1 * k01)
  val score1 = (q0 * k10) + (q1 * k11)
  val score2 = (q0 * k20) + (q1 * k21)
  val score3 = (q0 * k30) + (q1 * k31)

  // Concatenate the four 9-bit scores into the 36-bit output vector.
  // The ## operator concatenates with the left operand as the most significant bits.
  scores_out := score3 ## score2 ## score1 ## score0
}

// ============================================================================
//  NOT PART OF THE DYNAX RELEASE.  This module is a FAST reconstruction.
// ============================================================================
//
//  repe.scala, prepe_1_2.scala and prepe_1_4.scala all `import
//  exp_unit.ExpUnitFixPoint`, but no such file ships with DynaX.  Five of the
//  eight published Chisel sources therefore cannot elaborate as released.
//
//  This file supplies a module that satisfies that import.  Everything about
//  it except the call signature is inferred, so any number produced by RePEA
//  or PrePEA is a number about *this* exponential unit, not about DynaX's.
//  Keep that distinction in anything reported as a DynaX baseline.
//
//  What the call sites pin down:
//    - constructed as `new ExpUnitFixPoint(bits, point, 6, 4)`
//    - `io.in_value : FixedPoint(bits.W, point.BP)` driven combinationally
//    - `io.out_exp  : FixedPoint(bits.W, point.BP)` sampled into a Reg by the
//      caller in the same cycle, so the unit must be purely combinational
//      (repe.scala:73-78, prepe_1_2.scala:148-165)
//    - inputs are attention scores, so both signs occur: PrePEA feeds an
//      unsigned partial sum, RePEA feeds a signed accumulator.
//
//  The trailing (6, 4) are read here as (intBits, fracBits) of the internal
//  log-domain exponent.  That reading is what makes the pair meaningful: a
//  4-bit fraction indexes a 16-entry mantissa LUT, and 6 integer bits cover
//  every shift distance a 16-bit Q8 output can represent.
//
//  Algorithm -- the standard shift-and-LUT exponential:
//
//      e^x = 2^(x * log2 e) = 2^ki * 2^kf,  ki = floor(k), kf = k - ki
//
//  so the integer part becomes a barrel shift and only 2^kf (a value in
//  [1, 2)) needs a table.  One multiply, one 2^fracBits-entry ROM, one
//  shifter.  No iteration, no divider -- consistent with the exponential
//  sitting inside every PE.
//
//  Accuracy at (bits=16, point=8, fracBits=4), measured against math.exp over
//  every representable input:
//
//      e^x >= 1          worst relative error 2.65%
//      e^x in [1/64, 1)  worst relative error 20.8%
//
//  The second number is the Q8.8 output format, not the unit: at e^x = 4/256 a
//  one-LSB rounding is already 12.5%. Rounding `k` instead of truncating it
//  (the guard bits below) is what pulls the first number down from 6.08%;
//  widening fracBits past 4 buys almost nothing after that (2.36% at the
//  limit) while doubling the LUT each step.
//
//  gen_golden.py mirrors this integer datapath exactly, so the Verilator check
//  is bit-exact rather than tolerance-based.

package exp_unit

import chisel3._
import chisel3.util._
import chisel3.experimental.FixedPoint

class ExpUnitFixPoint(
    val bits: Int,
    val point: Int,
    val intBits: Int,
    val fracBits: Int
) extends Module {
  require(bits > point, s"need at least one integer bit: bits=$bits point=$point")
  require(point > 0, s"point must be positive, got $point")
  require(fracBits > 0, s"fracBits must be positive, got $fracBits")

  // Shift distances the output format can actually distinguish: anything above
  // `shiftHi` overflows the integer field, anything below `shiftLo` underflows
  // past the LSB. Saturating outside this window costs nothing in accuracy.
  private val shiftHi = bits - point - 1
  private val shiftLo = -(point + 1)
  require(
    intBits >= log2Ceil(math.max(shiftHi, -shiftLo) + 1) + 1,
    s"intBits=$intBits cannot hold exponents in [$shiftLo, $shiftHi]",
  )

  val fpType = FixedPoint(bits.W, point.BP)
  val io = IO(new Bundle {
    val in_value = Input(fpType)
    val out_exp = Output(fpType)
  })

  // log2(e) is held to fracBits+guardBits fractional bits so that k can be
  // rounded rather than truncated. Truncating biases every result low by up to
  // a full LUT step (2^(1/16) = 4.4%); the guard bits cost one adder and cut
  // the worst-case error from 6.08% to 2.65%.
  private val guardBits = 4
  private val log2eScaled =
    math.round(1.4426950408889634 * (1 << (fracBits + guardBits))).toInt

  // k = x * log2(e). `x` carries `point` fractional bits and the constant
  // carries fracBits+guardBits, so the product carries point+fracBits+guardBits;
  // shifting right by `point` leaves the guarded form.
  private val x = io.in_value.asSInt
  private val kProduct = x * log2eScaled.S((fracBits + guardBits + 2).W)
  private val kGuarded = (kProduct >> point).asSInt
  // Round to fracBits by adding half an LSB, then drop the guard. Both shifts
  // are arithmetic, so the floor they apply is toward -inf and the split below
  // sees a non-negative fraction for either sign of x.
  private val k = ((kGuarded + (1 << (guardBits - 1)).S) >> guardBits).asSInt

  private val ki = (k >> fracBits).asSInt // integer part, floored
  private val kf = k.asUInt(fracBits - 1, 0) // fractional part, always >= 0

  // 2^(kf / 2^fracBits) in Q(point). Entries span [1.0, 2.0), so the value
  // needs point+2 bits: one integer bit plus headroom for the top entry.
  private val mantissa = VecInit(Seq.tabulate(1 << fracBits) { j =>
    math
      .round(math.pow(2.0, j.toDouble / (1 << fracBits)) * (1 << point))
      .toInt
      .U((point + 2).W)
  })(kf)

  private val overflow = ki > shiftHi.S
  private val underflow = ki < shiftLo.S
  private val kiClamped = Mux(overflow, shiftHi.S, Mux(underflow, shiftLo.S, ki))

  // Pre-shift left by `bits` so the variable shift is right-only: with ki in
  // [shiftLo, shiftHi] the distance `bits - ki` stays within [point+1,
  // bits+point+1] and is never negative.
  private val widened = mantissa.asUInt << bits
  private val shifted = (widened >> (bits.S - kiClamped).asUInt).asUInt

  private val maxMagnitude = ((BigInt(1) << (bits - 1)) - 1).U(bits.W)
  io.out_exp := Mux(overflow, maxMagnitude, shifted(bits - 1, 0)).asFixedPoint(point.BP)
}

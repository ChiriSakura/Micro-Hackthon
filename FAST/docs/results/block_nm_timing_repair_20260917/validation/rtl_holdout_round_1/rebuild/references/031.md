# Native streaming TopK 8:7 timing probe

Unchanged FAST reference `hardware/chisel/src/main/scala/predict_unit/topk.scala`.

Verilator probe, source emitted with Scala 2.13.12 / Chisel 3.6.1; eight strictly positive unique input values, one input per edge, first capture edge numbered 1. Rank-valid pulses occur on edges **8, 9, 10, 11, 12, 13, 14**. All seven indices match independent sorting. The bare native module finishes at edge **m+n-1 = 14**, not 15. Extra input/output adapter registers must be counted separately. This probe does not establish II=1 for a wrapper around a serial core.

Native outputs have staggered idxValid lanes; capture each index on its own valid pulse. outData is the forwarded runner-up stream, not the retained sorted value. Max registers initialize to zero; arbitrary signed inputs and stable index ties are not established by this positive-unique probe.

A previous Agent diagnosis claimed a mandatory 15-cycle native latency without simulation; this probe refutes that claim. Numeric expectations must come from machine evaluation, not mental comparisons of long decimal encodings.

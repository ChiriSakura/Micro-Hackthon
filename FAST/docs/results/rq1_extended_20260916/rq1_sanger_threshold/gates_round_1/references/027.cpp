// Verilator testbench: check ExpUnitFixPoint against the datapath we specified.
//
// The unit is purely combinational -- repe.scala and prepe_*.scala both drive
// io.in_value and sample io.out_exp into a Reg in the same cycle -- so the bench
// applies an input, evaluates, and reads. The clock is toggled anyway to prove
// the output does not depend on it: a registered stage here would break both
// call sites, and this is the cheapest place to catch that.
//
// The reference is gen_golden.py's bit-exact mirror of the shift-and-LUT
// datapath, not math.exp. A tolerance against the true exponential would hide a
// wrong LUT entry or an off-by-one shift inside the tolerance; how close the
// datapath sits to math.exp is a separate question, answered in the header of
// exp_unit.scala.

#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#include "golden.h"

#include "VExpUnitFixPoint.h"
#include "verilated.h"

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    const char* golden_path = argc > 1 ? argv[1] : "golden.json";

    auto cases = golden::load_cases(golden_path);
    if (cases.empty()) { std::fprintf(stderr, "no golden cases in %s\n", golden_path); return 2; }

    auto* dut = new VExpUnitFixPoint;
    dut->reset = 0;
    dut->clock = 0;

    int failures = 0;
    int total = 0;

    for (const auto& item : cases) {
        int case_failures = 0;
        for (size_t i = 0; i < item.input_ticks.size(); i++) {
            const long in_ticks = item.input_ticks[i];
            dut->io_in_value = (unsigned short)(in_ticks & 0xFFFF);
            dut->eval();
            const long combinational = (unsigned short)dut->io_out_exp;

            // Same input across a clock edge must give the same output.
            dut->clock = 1; dut->eval();
            dut->clock = 0; dut->eval();
            const long after_edge = (unsigned short)dut->io_out_exp;

            const long want = item.expected_value_ticks[i];
            const bool ok = combinational == want && after_edge == want;
            total++;
            if (!ok) {
                if (case_failures < 3) {
                    std::printf("  MISMATCH %s[%zu]: in=%ld rtl=%ld (post-edge %ld) golden=%ld\n",
                                item.name.c_str(), i, in_ticks, combinational, after_edge, want);
                }
                case_failures++;
            }
        }
        std::printf("%-16s %s (%zu/%zu points matched)\n", item.name.c_str(),
                    case_failures ? "FAIL" : "pass",
                    item.input_ticks.size() - (size_t)case_failures,
                    item.input_ticks.size());
        failures += case_failures;
    }

    delete dut;
    std::printf("\n%s: %d mismatches across %d points in %zu cases\n",
                failures ? "FAILED" : "PASSED", failures, total, cases.size());
    return failures ? 1 : 0;
}

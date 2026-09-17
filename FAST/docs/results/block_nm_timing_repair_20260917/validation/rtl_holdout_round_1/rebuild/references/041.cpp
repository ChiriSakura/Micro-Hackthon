// Verilator testbench: check PSumSoftmax against a bit-exact model of itself.
//
// The module is purely combinational (no Reg anywhere in psum_softmax.scala),
// so the bench applies an input, evaluates, and reads. The clock is toggled to
// prove the output does not depend on it.
//
// The reference is gen_golden.py's mirror of the Chisel datapath *including its
// truncations*: `sum := add1 + add2` narrows bits+1 back to bits, and the
// quotient narrows bits+point+1 back to bits. Modelling those is what makes the
// overflow cases meaningful -- they record what the RTL does, which is wrap.

#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#include "golden.h"

#include "VPSumSoftmax.h"
#include "verilated.h"

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    const char* golden_path = argc > 1 ? argv[1] : "golden.json";

    auto cases = golden::load_cases(golden_path);
    if (cases.empty()) { std::fprintf(stderr, "no golden cases in %s\n", golden_path); return 2; }

    auto* dut = new VPSumSoftmax;
    dut->reset = 0;
    dut->clock = 0;

    int failures = 0;
    int total = 0;

    for (const auto& item : cases) {
        int case_failures = 0;
        const size_t points = item.input_ticks.size() / 4;
        for (size_t p = 0; p < points; p++) {
            const long add1 = item.input_ticks[4 * p + 0];
            const long add2 = item.input_ticks[4 * p + 1];
            const long exp = item.input_ticks[4 * p + 2];
            const long s = item.input_ticks[4 * p + 3];

            dut->io_add1 = (unsigned short)(add1 & 0xFFFF);
            dut->io_add2 = (unsigned short)(add2 & 0xFFFF);
            dut->io_exp = (unsigned short)(exp & 0xFFFF);
            dut->io_s = (unsigned char)(s & 1);
            dut->eval();
            dut->clock = 1; dut->eval();
            dut->clock = 0; dut->eval();

            const long got_out = (short)(unsigned short)dut->io_out;
            const long got_en = dut->io_en ? 1 : 0;
            const long want_out = item.expected_value_ticks[2 * p + 0];
            const long want_en = item.expected_value_ticks[2 * p + 1];

            total++;
            if (got_out != want_out || got_en != want_en) {
                if (case_failures < 3) {
                    std::printf("  MISMATCH %s[%zu]: add1=%ld add2=%ld exp=%ld s=%ld -> "
                                "rtl(out=%ld en=%ld) golden(out=%ld en=%ld)\n",
                                item.name.c_str(), p, add1, add2, exp, s,
                                got_out, got_en, want_out, want_en);
                }
                case_failures++;
            }
        }
        std::printf("%-22s %s (%zu/%zu points matched)\n", item.name.c_str(),
                    case_failures ? "FAIL" : "pass",
                    points - (size_t)case_failures, points);
        failures += case_failures;
    }

    delete dut;
    std::printf("\n%s: %d mismatches across %d points in %zu cases\n",
                failures ? "FAILED" : "PASSED", failures, total, cases.size());
    return failures ? 1 : 0;
}

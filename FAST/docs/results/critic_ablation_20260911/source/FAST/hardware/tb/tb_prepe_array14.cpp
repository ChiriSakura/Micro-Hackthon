// Verilator testbench: check PrePEArray_1_4 against DynaX's own Python.
//
// The 1:4 counterpart of tb_prepe_array.cpp, and it needs its own bench: the
// selection stage here is a three-deep shift register feeding a four-way
// comparator, not a single compare. The arbiter is the same and for the same
// reason -- quant_qk_matmul("1_4_6bit") in models/utils/sparse_attention.py is
// what this accelerator exists to run, and a mirror of the RTL could only ever
// confirm that the RTL equals itself.
//
// What that settled: at cycleCount==3 the comparator sees io.left_in as index
// 0, l_first as 1, l_second as 2 and l_third as 3, so the index order runs
// OPPOSITE to the arrival order. Each group of four must be presented in
// DESCENDING index order for a kept Q to meet its own K. That is the same
// convention the 1:2 array follows -- "odd element first" is this rule on a
// group of two -- stated in neither case.
//
// Measured over 200 random inputs: descending order agrees with the software
// 200/200, ascending 12/200.
//
// Two limits on the stimulus, both deliberate. Groups carry no ties, because on
// a tie the software keeps the lowest index while every comparison here is a
// strict `>`. And K is held to 3 bits while Q spans the full 6: the only
// observable output is exp(psum) in Q8.8, which saturates above e^7, and
// full-range operands drive the partial sum to about e^31 -- at which point a
// deliberately wrong feed order still "agrees" on 149 of 200 inputs because
// every case reads 32767.

#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#include "golden.h"

#include "VPrePEArray_1_4.h"
#include "verilated.h"

namespace {

// 尺寸常量与 drive()/score() 由 tb/gen_ports.py 按阵列尺寸生成。
#include "array_ports.h"

}  // namespace

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    const char* golden_path = argc > 1 ? argv[1] : "golden.json";

    auto cases = golden::load_cases(golden_path);
    if (cases.empty()) { std::fprintf(stderr, "no golden cases in %s\n", golden_path); return 2; }

    auto* dut = new VPrePEArray_1_4;
    int failures = 0;
    int total = 0;

    for (const auto& item : cases) {
        // cycleCount and the shift registers are RegInit and do reset, unlike
        // the PE registers, so a reset here really does put the array back on a
        // known phase - which matters, because the Q load only works on one of
        // the four.
        dut->reset = 1;
        dut->clock = 0; dut->eval();
        dut->clock = 1; dut->eval();
        dut->reset = 0;
        dut->clock = 0; dut->eval();

        int case_failures = 0;
        int case_checked = 0;
        const size_t cycles = item.input_ticks.size() / kFieldsPerCycle;
        for (size_t c = 0; c < cycles; c++) {
            drive(dut, &item.input_ticks[c * kFieldsPerCycle]);
            dut->eval();

            if (item.expected_idx[c]) {
                const long* want = &item.expected_value_ticks[c * kHeight];
                bool ok = true;
                for (int r = 0; r < kHeight && ok; r++) ok = score(dut, r) == want[r];
                total++;
                case_checked++;
                if (!ok) {
                    if (case_failures < 3) {
                        std::printf("  MISMATCH %s cycle %zu: rtl=[", item.name.c_str(), c);
                        for (int r = 0; r < kHeight; r++)
                            std::printf("%ld%s", score(dut, r), r + 1 < kHeight ? "," : "");
                        std::printf("] golden=[");
                        for (int r = 0; r < kHeight; r++)
                            std::printf("%ld%s", want[r], r + 1 < kHeight ? "," : "");
                        std::printf("]\n");
                    }
                    case_failures++;
                }
            }

            dut->clock = 1; dut->eval();
            dut->clock = 0; dut->eval();
        }
        std::printf("%-16s %s (%d/%d cycles matched)\n", item.name.c_str(),
                    case_failures ? "FAIL" : "pass",
                    case_checked - case_failures, case_checked);
        failures += case_failures;
    }

    delete dut;
    std::printf("\n%s: %d mismatches across %d cycles in %zu cases\n",
                failures ? "FAILED" : "PASSED", failures, total, cases.size());
    return failures ? 1 : 0;
}

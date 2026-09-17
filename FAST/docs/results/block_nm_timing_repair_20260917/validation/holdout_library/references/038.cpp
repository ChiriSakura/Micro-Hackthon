// Verilator testbench: check PrePEArray_1_2 against DynaX's own Python.
//
// This is the one module whose reference could not be a mirror of itself. The
// 1:2 pruning decision lives in the array -- cycleToggle latches one Q element,
// compares it with the next, and emits the larger plus a select bit -- and
// whether that select bit picks the right K element is precisely what a mirror
// cannot answer. The arbiter is the software the accelerator exists to run:
// quant_qk_matmul("1_2_4bit") in models/utils/sparse_attention.py, which keeps
// the larger-magnitude element of each adjacent pair and takes the dot product
// with K. gen_golden.py asserts the array reproduces it before writing a case.
//
// What that settled: the select bit is tied to "the first-latched element won"
// and selects top_in1, i.e. K[2c+1], so the ODD element of each pair has to be
// presented first. Fed even-element-first the array computes a different sum
// from the software on 5 of 6 random inputs. That is a usage constraint the
// sources never state, not a defect -- the RTL is self-consistent under it.
//
// Operands are non-negative 4-bit so torch.abs is a no-op and the RTL's
// unsigned compare means what the software's argmax(abs) means; pairs carry no
// internal ties, because on a tie the software keeps the first element and the
// RTL's strict `>` keeps the second.

#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#include "golden.h"

#include "VPrePEArray_1_2.h"
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

    auto* dut = new VPrePEArray_1_2;
    int failures = 0;
    int total = 0;

    for (const auto& item : cases) {
        // cycleToggle is a RegInit and does reset, unlike the PE registers, so
        // a reset here really does put the array back on a known phase - which
        // matters, because the Q load only works on one of the two.
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

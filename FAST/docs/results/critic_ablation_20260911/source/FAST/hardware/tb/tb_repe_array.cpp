// Verilator testbench: check RePEArray against a structural model of itself.
//
// What the array adds over a row is the column chain: rows(i+1).regs_top comes
// from rows(i).regs_bottom, which is a *registered* value, so a column vector
// reaches row i on cycle i. Control does not travel that way -- clr, acc_ctrl
// and exp_ctrl are broadcast to every row on the same cycle -- and the
// consequence is the point of `column_skew` and `per_row_queries`: row i
// accumulates during row 0's window while seeing data skewed by i cycles.
//
// The bench runs a 4x2 array with regWidth 4. The chain is homogeneous, so 4
// rows exercises the inter-row link that 64 rows would; the paper-sized
// configurations are covered by the elaboration sweep, which proves the same
// structure composes at 32x4 and 64x8.

#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#include "golden.h"

#include "VRePEArray.h"
#include "verilated.h"

namespace {

// 尺寸常量与 drive()/row_out() 由 tb/gen_ports.py 按阵列尺寸生成：
// DynaX-L 的 64x8 阵列光 sel_cols 就有 512 个端口，手写读不出问题。
#include "array_ports.h"

}  // namespace

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    const char* golden_path = argc > 1 ? argv[1] : "golden.json";

    auto cases = golden::load_cases(golden_path);
    if (cases.empty()) { std::fprintf(stderr, "no golden cases in %s\n", golden_path); return 2; }

    auto* dut = new VRePEArray;
    int failures = 0;
    int total = 0;

    for (const auto& item : cases) {
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
                const long* want = &item.expected_value_ticks[c * kNumRows];
                bool ok = true;
                for (int r = 0; r < kNumRows && ok; r++) ok = row_out(dut, r) == want[r];
                total++;
                case_checked++;
                if (!ok) {
                    if (case_failures < 3) {
                        std::printf("  MISMATCH %s cycle %zu: rtl=[", item.name.c_str(), c);
                        for (int r = 0; r < kNumRows; r++)
                            std::printf("%ld%s", row_out(dut, r), r + 1 < kNumRows ? "," : "");
                        std::printf("] golden=[");
                        for (int r = 0; r < kNumRows; r++)
                            std::printf("%ld%s", want[r], r + 1 < kNumRows ? "," : "");
                        std::printf("]\n");
                    }
                    case_failures++;
                }
            }

            dut->clock = 1; dut->eval();
            dut->clock = 0; dut->eval();
        }
        std::printf("%-24s %s (%d/%d cycles matched)\n", item.name.c_str(),
                    case_failures ? "FAIL" : "pass",
                    case_checked - case_failures, case_checked);
        failures += case_failures;
    }

    delete dut;
    std::printf("\n%s: %d mismatches across %d cycles in %zu cases\n",
                failures ? "FAILED" : "PASSED", failures, total, cases.size());
    return failures ? 1 : 0;
}

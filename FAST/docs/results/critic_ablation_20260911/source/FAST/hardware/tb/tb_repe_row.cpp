// Verilator testbench: check RePERow against a structural model of itself.
//
// The row adds two things to a bare PE, and both are timing, not arithmetic:
// it registers its inputs (so its PEs see data one cycle after presentation)
// and it registers the adder tree (so a sum appears one cycle after the PE
// outputs that formed it). Both outputs are therefore compared every cycle --
// adder_out and the whole regs_bottom vector -- because a model that only
// checked final values would accept a row that was right but late.
//
// Each case opens with the same known-state preamble as tb_repe.cpp: the PEs
// inside the row have unresettable score_exp registers.

#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#include "golden.h"

#include "VRePERow.h"
#include "verilated.h"

namespace {

constexpr int kPeCount = 8;
constexpr int kRegWidth = 8;
// q_left, clr, acc_ctrl, exp_ctrl, then regs_top[8] and sel_cols[8]
constexpr int kFieldsPerCycle = 4 + kRegWidth + kPeCount;
constexpr int kOutputsPerCycle = 1 + kRegWidth;  // adder_out, regs_bottom[8]

void drive(VRePERow* dut, const long* fields) {
    dut->io_q_left = (unsigned short)(fields[0] & 0xFFFF);
    dut->io_clr = (unsigned char)(fields[1] & 1);
    dut->io_acc_ctrl = (unsigned char)fields[2];
    dut->io_exp_ctrl = (unsigned char)fields[3];

    const long* tops = fields + 4;
    dut->io_regs_top_0 = (unsigned short)(tops[0] & 0xFFFF);
    dut->io_regs_top_1 = (unsigned short)(tops[1] & 0xFFFF);
    dut->io_regs_top_2 = (unsigned short)(tops[2] & 0xFFFF);
    dut->io_regs_top_3 = (unsigned short)(tops[3] & 0xFFFF);
    dut->io_regs_top_4 = (unsigned short)(tops[4] & 0xFFFF);
    dut->io_regs_top_5 = (unsigned short)(tops[5] & 0xFFFF);
    dut->io_regs_top_6 = (unsigned short)(tops[6] & 0xFFFF);
    dut->io_regs_top_7 = (unsigned short)(tops[7] & 0xFFFF);

    const long* sel = fields + 4 + kRegWidth;
    dut->io_sel_cols_0 = (unsigned char)sel[0];
    dut->io_sel_cols_1 = (unsigned char)sel[1];
    dut->io_sel_cols_2 = (unsigned char)sel[2];
    dut->io_sel_cols_3 = (unsigned char)sel[3];
    dut->io_sel_cols_4 = (unsigned char)sel[4];
    dut->io_sel_cols_5 = (unsigned char)sel[5];
    dut->io_sel_cols_6 = (unsigned char)sel[6];
    dut->io_sel_cols_7 = (unsigned char)sel[7];
}

long bottom(VRePERow* dut, int index) {
    switch (index) {
        case 0: return (short)(unsigned short)dut->io_regs_bottom_0;
        case 1: return (short)(unsigned short)dut->io_regs_bottom_1;
        case 2: return (short)(unsigned short)dut->io_regs_bottom_2;
        case 3: return (short)(unsigned short)dut->io_regs_bottom_3;
        case 4: return (short)(unsigned short)dut->io_regs_bottom_4;
        case 5: return (short)(unsigned short)dut->io_regs_bottom_5;
        case 6: return (short)(unsigned short)dut->io_regs_bottom_6;
        default: return (short)(unsigned short)dut->io_regs_bottom_7;
    }
}

}  // namespace

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    const char* golden_path = argc > 1 ? argv[1] : "golden.json";

    auto cases = golden::load_cases(golden_path);
    if (cases.empty()) { std::fprintf(stderr, "no golden cases in %s\n", golden_path); return 2; }

    auto* dut = new VRePERow;
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
                const long* want = &item.expected_value_ticks[c * kOutputsPerCycle];
                const long got_sum = (short)(unsigned short)dut->io_adder_out;
                bool ok = got_sum == want[0];
                for (int i = 0; i < kRegWidth && ok; i++) ok = bottom(dut, i) == want[1 + i];
                total++;
                case_checked++;
                if (!ok) {
                    if (case_failures < 3) {
                        std::printf("  MISMATCH %s cycle %zu: adder rtl=%ld golden=%ld;"
                                    " regs_bottom rtl=[", item.name.c_str(), c,
                                    got_sum, want[0]);
                        for (int i = 0; i < kRegWidth; i++)
                            std::printf("%ld%s", bottom(dut, i), i + 1 < kRegWidth ? "," : "");
                        std::printf("] golden=[");
                        for (int i = 0; i < kRegWidth; i++)
                            std::printf("%ld%s", want[1 + i], i + 1 < kRegWidth ? "," : "");
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

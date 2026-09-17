// Verilator testbench: check one RePE against a cycle-accurate model of its FSM.
//
// RePE has no documented control schedule -- neither the DynaX sources nor the
// paper state one -- so gen_golden.py's RePEModel is the schedule written down,
// and this bench is what decides whether the RTL agrees with it. Every cycle's
// io.out is compared, not just the end of a phase: the whole question is when
// each value appears, and a bench that only checked the final value would pass
// on a datapath that produced the right numbers a cycle early or late.
//
// io.out is dual-purpose, so both readings are exercised. In acc_move_out it
// carries the accumulator (the AV product being drained); in every other state
// it carries score_exp (whose sum across a row is the softmax denominator).
//
// Each case opens with a preamble that drives the module to a known state,
// because reset cannot: `acc` and `score_exp` are Reg rather than RegInit, and
// acc_clear clears only `acc`. expected_idx marks the preamble's own cycles as
// unchecked, since those outputs legitimately still show the previous case.

#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#include "golden.h"

#include "VRePE.h"
#include "verilated.h"

namespace {

// regWidth from Elaborate.scala's RePE entry. Chisel flattens the Vec input to
// io_reg_cols_0 .. io_reg_cols_7, so the bench addresses the generated names.
constexpr int kRegWidth = 8;
constexpr int kFieldsPerCycle = 4 + kRegWidth;  // q_in, sel_col, acc_ctrl, exp_ctrl

void drive_columns(VRePE* dut, const long* columns) {
    dut->io_reg_cols_0 = (unsigned short)(columns[0] & 0xFFFF);
    dut->io_reg_cols_1 = (unsigned short)(columns[1] & 0xFFFF);
    dut->io_reg_cols_2 = (unsigned short)(columns[2] & 0xFFFF);
    dut->io_reg_cols_3 = (unsigned short)(columns[3] & 0xFFFF);
    dut->io_reg_cols_4 = (unsigned short)(columns[4] & 0xFFFF);
    dut->io_reg_cols_5 = (unsigned short)(columns[5] & 0xFFFF);
    dut->io_reg_cols_6 = (unsigned short)(columns[6] & 0xFFFF);
    dut->io_reg_cols_7 = (unsigned short)(columns[7] & 0xFFFF);
}

const char* acc_name(long control) {
    switch (control) {
        case 0: return "clear";
        case 1: return "idle";
        case 2: return "accumulate";
        default: return "move_out";
    }
}

}  // namespace

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    const char* golden_path = argc > 1 ? argv[1] : "golden.json";

    auto cases = golden::load_cases(golden_path);
    if (cases.empty()) { std::fprintf(stderr, "no golden cases in %s\n", golden_path); return 2; }

    auto* dut = new VRePE;
    int failures = 0;
    int total = 0;

    for (const auto& item : cases) {
        // `acc` and `score_exp` are Reg, not RegInit, so reset does not clear
        // them; the model starts both at zero to match Verilator's own
        // initialisation, and every schedule opens with acc_clear anyway.
        dut->reset = 1;
        dut->clock = 0; dut->eval();
        dut->clock = 1; dut->eval();
        dut->reset = 0;
        dut->clock = 0; dut->eval();

        int case_failures = 0;
        int checked_in_case = 0;
        const size_t cycles = item.input_ticks.size() / kFieldsPerCycle;
        for (size_t c = 0; c < cycles; c++) {
            const long* fields = &item.input_ticks[c * kFieldsPerCycle];
            dut->io_q_in = (unsigned short)(fields[0] & 0xFFFF);
            dut->io_sel_col = (unsigned char)fields[1];
            dut->io_acc_ctrl = (unsigned char)fields[2];
            dut->io_exp_ctrl = (unsigned char)fields[3];
            drive_columns(dut, fields + 4);
            dut->eval();

            // io.out is combinational in this cycle's state (it is either the
            // registered score_exp or, under move_out, the registered acc), so
            // it is read before the edge that updates those registers.
            if (item.expected_idx[c]) {
                const long got = (short)(unsigned short)dut->io_out;
                const long want = item.expected_value_ticks[c];
                total++;
                checked_in_case++;
                if (got != want) {
                    if (case_failures < 3) {
                        std::printf("  MISMATCH %s cycle %zu [%s/%s sel=%ld q=%ld]: "
                                    "rtl=%ld golden=%ld\n",
                                    item.name.c_str(), c, acc_name(fields[2]),
                                    fields[3] ? "exp" : "-", fields[1],
                                    (long)(short)fields[0], got, want);
                    }
                    case_failures++;
                }
            }

            dut->clock = 1; dut->eval();
            dut->clock = 0; dut->eval();
        }
        std::printf("%-24s %s (%d/%d cycles matched)\n", item.name.c_str(),
                    case_failures ? "FAIL" : "pass",
                    checked_in_case - case_failures, checked_in_case);
        failures += case_failures;
    }

    delete dut;
    std::printf("\n%s: %d mismatches across %d cycles in %zu cases\n",
                failures ? "FAILED" : "PASSED", failures, total, cases.size());
    return failures ? 1 : 0;
}

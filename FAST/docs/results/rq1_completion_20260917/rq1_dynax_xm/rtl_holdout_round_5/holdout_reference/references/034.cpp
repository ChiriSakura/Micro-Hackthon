// Verilator testbench: check SRAM against a correct banked synchronous-read SRAM.
//
// The reference is deliberately NOT a mirror of this Verilog. SyncReadMem gives
// a read issued at cycle t its data at t+1, so a correct banked wrapper must
// select the output bank with the address that was presented at t -- and
// sram.scala selects with the address presented at t+1. The golden cases are
// built so that difference is isolated: `single_bank` and `repeat_read` never
// cross a bank boundary, `bank_switch` crosses on every read.
//
// A cycle following a write is skipped: read enable is tied to !writeEnable, so
// there is no defined data to compare. expected_idx carries that per-cycle flag.
//
// Sampling point matters here and is chosen deliberately. dataOut is read while
// cycle c's inputs are applied but BEFORE its clock edge, which is what a
// downstream consumer sees: it registers dataOut on the edge that ends cycle c,
// by which time io_addr already holds addr(c) even though the data in flight
// was requested at c-1. Sampling after the edge instead would hide the defect,
// because io_addr has not advanced yet at that instant.

#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#include "golden.h"

#include "VSRAM.h"
#include "verilated.h"

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    const char* golden_path = argc > 1 ? argv[1] : "golden.json";

    auto cases = golden::load_cases(golden_path);
    if (cases.empty()) { std::fprintf(stderr, "no golden cases in %s\n", golden_path); return 2; }

    auto* dut = new VSRAM;
    int failures = 0;
    int checked = 0;

    for (const auto& item : cases) {
        // Reset between cases. SyncReadMem contents survive reset, so each case
        // writes what it reads rather than assuming a cleared memory.
        dut->reset = 1;
        dut->io_writeEnable = 0;
        dut->io_addr = 0;
        dut->io_dataIn = 0;
        for (int i = 0; i < 4; i++) { dut->clock = 0; dut->eval(); dut->clock = 1; dut->eval(); }
        dut->reset = 0;

        int case_failures = 0;
        int case_checked = 0;
        const size_t cycles = item.input_ticks.size() / 3;
        for (size_t c = 0; c < cycles; c++) {
            dut->io_addr = (unsigned int)item.input_ticks[3 * c + 0];
            dut->io_dataIn = (unsigned long long)item.input_ticks[3 * c + 1];
            dut->io_writeEnable = (unsigned char)item.input_ticks[3 * c + 2];
            dut->clock = 0; dut->eval();

            // Read before the edge: the data in flight was requested at c-1,
            // while the bank multiplexer is already looking at addr(c).
            if (item.expected_idx[c]) {
                const long got = (long)(unsigned long long)dut->io_dataOut;
                const long want = item.expected_value_ticks[c];
                checked++;
                case_checked++;
                if (got != want) {
                    if (case_failures < 3) {
                        std::printf("  MISMATCH %s cycle %zu: read addr=%ld while addr=%ld "
                                    "is presented -> rtl=0x%lx golden=0x%lx\n",
                                    item.name.c_str(), c, item.input_ticks[3 * (c - 1)],
                                    item.input_ticks[3 * c], got, want);
                    }
                    case_failures++;
                }
            }

            dut->clock = 1; dut->eval();
        }
        std::printf("%-24s %s (%d/%d reads matched)\n", item.name.c_str(),
                    case_failures ? "FAIL" : "pass",
                    case_checked - case_failures, case_checked);
        failures += case_failures;
    }

    delete dut;
    std::printf("\n%s: %d mismatches across %d checked reads in %zu cases\n",
                failures ? "FAILED" : "PASSED", failures, checked, cases.size());
    return failures ? 1 : 0;
}

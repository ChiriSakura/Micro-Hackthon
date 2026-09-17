// Verilator testbench: drive TopK with golden vectors and compare exactly.
//
// TopK streams one value per cycle through TopFirst and n-1 TopStage modules,
// so a block of m values takes m cycles to load plus a few to settle. The bench
// therefore drives the whole block, then reads the parallel outputs.
//
// Comparison is exact, not approximate: the golden values were rounded onto the
// module's own fixed-point grid, so any difference is a real disagreement.

#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#include "golden.h"

#include "VTopK.h"
#include "verilated.h"

using golden::Case;
using golden::load_cases;

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    const char* golden_path = argc > 1 ? argv[1] : "golden.json";
    const int n = argc > 2 ? std::atoi(argv[2]) : 16;

    auto cases = load_cases(golden_path);
    if (cases.empty()) { std::fprintf(stderr, "no golden cases in %s\n", golden_path); return 2; }

    auto* dut = new VTopK;
    int failures = 0;

    // Chisel flattens `io.x` to `io_x`, and a Vec output to io_outData_0..n-1,
    // so the bench addresses the generated names rather than the Scala ones.
    auto tick = [&](int enable, long value) {
        dut->io_enable = enable;
        dut->io_inData = (unsigned int)(value & 0xFFFF);
        dut->clock = 0; dut->eval();
        dut->clock = 1; dut->eval();
    };

    // What the module exposes is not what the name suggests: io.outData(i) is
    // wired to each stage's runnerUpReg - the value being streamed downstream -
    // while the i-th largest value itself stays in that stage's maxReg and is
    // only observable through io.idx(i). So correctness is checked on the
    // indices, and the values are looked up in the stimulus.
    auto idx_lane = [&](int i) -> long {
        switch (i) {
            case  0: return dut->io_idx_0;  case  1: return dut->io_idx_1;
            case  2: return dut->io_idx_2;  case  3: return dut->io_idx_3;
            case  4: return dut->io_idx_4;  case  5: return dut->io_idx_5;
            case  6: return dut->io_idx_6;  case  7: return dut->io_idx_7;
            case  8: return dut->io_idx_8;  case  9: return dut->io_idx_9;
            case 10: return dut->io_idx_10; case 11: return dut->io_idx_11;
            case 12: return dut->io_idx_12; case 13: return dut->io_idx_13;
            case 14: return dut->io_idx_14; case 15: return dut->io_idx_15;
            default: return -1;
        }
    };

    auto valid_lane = [&](int i) -> bool {
        switch (i) {
            case  0: return dut->io_idxValid_0;  case  1: return dut->io_idxValid_1;
            case  2: return dut->io_idxValid_2;  case  3: return dut->io_idxValid_3;
            case  4: return dut->io_idxValid_4;  case  5: return dut->io_idxValid_5;
            case  6: return dut->io_idxValid_6;  case  7: return dut->io_idxValid_7;
            case  8: return dut->io_idxValid_8;  case  9: return dut->io_idxValid_9;
            case 10: return dut->io_idxValid_10; case 11: return dut->io_idxValid_11;
            case 12: return dut->io_idxValid_12; case 13: return dut->io_idxValid_13;
            case 14: return dut->io_idxValid_14; case 15: return dut->io_idxValid_15;
            default: return false;
        }
    };

    auto lane = [&](int i) -> long {
        switch (i) {
            case  0: return (short)dut->io_outData_0;  case  1: return (short)dut->io_outData_1;
            case  2: return (short)dut->io_outData_2;  case  3: return (short)dut->io_outData_3;
            case  4: return (short)dut->io_outData_4;  case  5: return (short)dut->io_outData_5;
            case  6: return (short)dut->io_outData_6;  case  7: return (short)dut->io_outData_7;
            case  8: return (short)dut->io_outData_8;  case  9: return (short)dut->io_outData_9;
            case 10: return (short)dut->io_outData_10; case 11: return (short)dut->io_outData_11;
            case 12: return (short)dut->io_outData_12; case 13: return (short)dut->io_outData_13;
            case 14: return (short)dut->io_outData_14; case 15: return (short)dut->io_outData_15;
            default: return 0;
        }
    };

    for (const auto& item : cases) {
        // Reset between cases so one block never leaks into the next.
        dut->reset = 1;
        for (int i = 0; i < 4; i++) tick(0, 0);
        dut->reset = 0;

        // TopFirst pulses valid on the last element of the block and clears its
        // registers in the same cycle; the pulse then walks one stage per cycle.
        // Each lane must therefore be sampled when its own valid is high, not
        // after a fixed settling delay - by then the register is already zero.
        std::vector<long> captured_idx(n, -1);
        auto capture = [&]() {
            for (int i = 0; i < n; i++) {
                if (captured_idx[i] < 0 && valid_lane(i)) captured_idx[i] = idx_lane(i);
            }
        };

        for (long value : item.input_ticks) { tick(1, value); capture(); }
        for (int i = 0; i < n + 4; i++) { tick(0, 0); capture(); }

        int case_failures = 0;
        for (int i = 0; i < n && i < (int)item.expected_idx.size(); i++) {
            long got = captured_idx[i];
            long want = item.expected_idx[i];
            // Equal values are a legitimate tie: the module may pick any index
            // holding the expected value, so compare the value it points at.
            bool ok = (got == want);
            if (!ok && got >= 0 && got < (long)item.input_ticks.size()) {
                ok = item.input_ticks[got] == item.input_ticks[want];
            }
            if (!ok) {
                if (case_failures < 3) {
                    std::printf("  MISMATCH %s[%d]: rtl_idx=%ld (value=%ld) golden_idx=%ld (value=%ld)\n",
                                item.name.c_str(), i, got,
                                got >= 0 ? item.input_ticks[got] : 0,
                                want, item.input_ticks[want]);
                }
                case_failures++;
            }
        }
        std::printf("%-12s %s (%d/%d lanes matched)\n", item.name.c_str(),
                    case_failures ? "FAIL" : "pass",
                    (int)item.expected_idx.size() - case_failures,
                    (int)item.expected_idx.size());
        failures += case_failures;
    }

    delete dut;
    std::printf("\n%s: %d mismatches across %zu cases\n",
                failures ? "FAILED" : "PASSED", failures, cases.size());
    return failures ? 1 : 0;
}

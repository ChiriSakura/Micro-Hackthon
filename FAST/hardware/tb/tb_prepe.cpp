// Verilator testbench: check PrePE_1_2 against a cycle-accurate model of itself.
//
// Every output of this PE is a register, so all five are compared every cycle:
// bottom_out0, bottom_out1, right_out, sel_out and psum_out. The multiply in
// sCalc uses the previously latched top values while latching the next pair, so
// a reference that used this cycle's inputs would be uniformly off by one and
// still pass on constant stimulus - the cases use ramps for that reason.
//
// Each case opens with one unchecked sClear cycle. These registers are Reg, not
// RegInit, so reset cannot separate the cases, and the clear itself lands on the
// edge that ends the cycle - during it, the outputs still show the case before.
//
// The stimulus also pins down the input counter, which samples left_in only on
// its second sInput cycle. That is the 1:2 pruning rate: PrePEArray_1_2 spends
// one cycle latching and one comparing, so a selected value arrives every two
// cycles and the q chain shifts at exactly that rate.

#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#include "golden.h"

#include "VPrePE_1_2.h"
#include "verilated.h"

namespace {

constexpr int kFieldsPerCycle = 6;   // left, sel, top0, top1, psum_in, state
constexpr int kOutputsPerCycle = 5;
constexpr int kPsumBits = 12;   // Elaborate.scala 的 PSumBitsS  // bottom0, bottom1, right, sel_out, psum_out

}  // namespace

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    const char* golden_path = argc > 1 ? argv[1] : "golden.json";

    auto cases = golden::load_cases(golden_path);
    if (cases.empty()) { std::fprintf(stderr, "no golden cases in %s\n", golden_path); return 2; }

    auto* dut = new VPrePE_1_2;
    int failures = 0;
    int total = 0;

    for (const auto& item : cases) {
        // Every register here is a plain Reg, so reset leaves them untouched;
        // each case opens with sClear, which is the only path that zeroes them.
        dut->reset = 1;
        dut->clock = 0; dut->eval();
        dut->clock = 1; dut->eval();
        dut->reset = 0;
        dut->clock = 0; dut->eval();

        int case_failures = 0;
        int case_checked = 0;
        const size_t cycles = item.input_ticks.size() / kFieldsPerCycle;
        for (size_t c = 0; c < cycles; c++) {
            const long* fields = &item.input_ticks[c * kFieldsPerCycle];
            // 端口现在是 SInt(4.W)：送二进制补码的低 4 位。
            dut->io_left_in = (unsigned char)(fields[0] & 0xF);
            dut->io_sel_in = (unsigned char)(fields[1] & 1);
            dut->io_top_in0 = (unsigned char)(fields[2] & 0xF);
            dut->io_top_in1 = (unsigned char)(fields[3] & 0xF);
            dut->io_psum_in = (unsigned int)fields[4];
            dut->io_state = (unsigned char)fields[5];
            dut->eval();

            if (item.expected_idx[c]) {
                const long* want = &item.expected_value_ticks[c * kOutputsPerCycle];
                // SInt 端口按位宽做符号扩展再比对——Verilator 用无符号容器
            // 存它们，直接读会把 -2 读成 14。
            auto s4 = [](unsigned v) { return (long)(int)((v & 0xF) ^ 0x8) - 8; };
            auto sN = [&](unsigned v) {
                    const unsigned sign = 1u << (kPsumBits - 1);
                    return (long)(int)((v & (2 * sign - 1)) ^ sign) - (long)sign;
                };
            const long got[kOutputsPerCycle] = {
                    s4(dut->io_bottom_out0), s4(dut->io_bottom_out1),
                    s4(dut->io_right_out), (long)dut->io_sel_out,
                    sN(dut->io_psum_out),
                };
                bool ok = true;
                for (int i = 0; i < kOutputsPerCycle; i++) ok = ok && got[i] == want[i];
                total++;
                case_checked++;
                if (!ok) {
                    if (case_failures < 3) {
                        std::printf("  MISMATCH %s cycle %zu [state=%ld]: "
                                    "rtl(b0=%ld b1=%ld r=%ld s=%ld psum=%ld) "
                                    "golden(b0=%ld b1=%ld r=%ld s=%ld psum=%ld)\n",
                                    item.name.c_str(), c, fields[5],
                                    got[0], got[1], got[2], got[3], got[4],
                                    want[0], want[1], want[2], want[3], want[4]);
                    }
                    case_failures++;
                }
            }

            dut->clock = 1; dut->eval();
            dut->clock = 0; dut->eval();
        }
        std::printf("%-20s %s (%d/%d cycles matched)\n", item.name.c_str(),
                    case_failures ? "FAIL" : "pass",
                    case_checked - case_failures, case_checked);
        failures += case_failures;
    }

    delete dut;
    std::printf("\n%s: %d mismatches across %d cycles in %zu cases\n",
                failures ? "FAILED" : "PASSED", failures, total, cases.size());
    return failures ? 1 : 0;
}

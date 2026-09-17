// Verilator testbench：流水化除法器 vs 上游 FixedPointDiv 的语义。
//
// 两者必须逐位一致，否则「换一个除法器实现」就不是在同一条面积/频率曲线上
// 取点，而是换了功能。参照因此不是「一个正确的除法」，而是**上游那个除法器
// 算出来的东西**：朝零截断、除零返回 0、商超宽时回绕。
//
// 驱动方式是流式而不是「送一个等一个」：输入背靠背连续送入，输出按
// out_valid 顺序收集。这样同时测两件事——
//
//   * 算得对不对
//   * 流水线保不保序、能不能每拍接收（组合除法器一拍一个，流水化之后如果
//     只能每 stages 拍接收一个，那就不是流水线，吞吐反而更差）
//
// 后一点是这个模块存在的理由所在：它换来的是频率，如果吞吐掉了 stages 倍，
// 那笔交易就不划算，而只送一个输入的 testbench 看不出来。

#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#include "golden.h"

#include "VFixedPointDivPipelined.h"
#include "verilated.h"

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    const char* golden_path = argc > 1 ? argv[1] : "golden.json";

    auto cases = golden::load_cases(golden_path);
    if (cases.empty()) { std::fprintf(stderr, "no golden cases in %s\n", golden_path); return 2; }

    auto* dut = new VFixedPointDivPipelined;
    int failures = 0;
    int total = 0;

    for (const auto& item : cases) {
        // 每个用例的 expected_idx[0] 存的是流水线级数，也就是输出延迟。
        const int latency = item.expected_idx.empty() ? 8 : (int)item.expected_idx[0];
        const size_t points = item.input_ticks.size() / 2;

        dut->reset = 1;
        dut->io_in_valid = 0;
        for (int i = 0; i < latency + 4; i++) {
            dut->clock = 0; dut->eval(); dut->clock = 1; dut->eval();
        }
        dut->reset = 0;
        dut->clock = 0; dut->eval();

        std::vector<long> collected;
        // 送完全部输入还要再空转 latency+2 拍把流水线排空。
        const size_t cycles = points + (size_t)latency + 2;
        for (size_t c = 0; c < cycles; c++) {
            const bool feeding = c < points;
            dut->io_in_valid = feeding ? 1 : 0;
            dut->io_numerator =
                (unsigned short)(feeding ? item.input_ticks[2 * c] & 0xFFFF : 0);
            dut->io_denominator =
                (unsigned short)(feeding ? item.input_ticks[2 * c + 1] & 0xFFFF : 0);
            dut->eval();

            // out_valid 跟着数据一起穿过流水线，所以它高的那一拍就是商有效
            // 的那一拍——不需要外部数拍子。
            if (dut->io_out_valid) {
                collected.push_back((short)(unsigned short)dut->io_quotient);
            }

            dut->clock = 1; dut->eval();
            dut->clock = 0; dut->eval();
        }

        int case_failures = 0;
        // 收到的个数必须等于送进去的个数：少了说明流水线吞了数据，多了说明
        // out_valid 有毛刺。两者都是错误，不能只比对齐的那一段。
        if (collected.size() != points) {
            std::printf("  MISMATCH %s: 送入 %zu 个，收到 %zu 个（流水线未保序或吞吐不足）\n",
                        item.name.c_str(), points, collected.size());
            case_failures++;
        }

        const size_t comparable = std::min(collected.size(), points);
        for (size_t i = 0; i < comparable; i++) {
            const long want = item.expected_value_ticks[i];
            total++;
            if (collected[i] != want) {
                if (case_failures < 3) {
                    std::printf("  MISMATCH %s[%zu]: %ld / %ld -> rtl=%ld golden=%ld\n",
                                item.name.c_str(), i,
                                (long)(short)item.input_ticks[2 * i],
                                (long)(short)item.input_ticks[2 * i + 1],
                                collected[i], want);
                }
                case_failures++;
            }
        }
        std::printf("%-18s %s (%zu/%zu 点匹配，延迟 %d 拍)\n", item.name.c_str(),
                    case_failures ? "FAIL" : "pass",
                    comparable - (size_t)std::min((size_t)case_failures, comparable),
                    points, latency);
        failures += case_failures;
    }

    delete dut;
    std::printf("\n%s: %d mismatches across %d points in %zu cases\n",
                failures ? "FAILED" : "PASSED", failures, total, cases.size());
    return failures ? 1 : 0;
}

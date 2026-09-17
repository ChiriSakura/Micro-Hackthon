// 集成层第一步的验证：**控制收进硬件之后，结果必须逐字节不变。**
//
// 评审 P0-4：AttentionTile 的控制在外部，`tb_attention_tile.cpp` 逐 query
// 复位、只驱动第 0 行、跨趟分子分母在 C++ 里相加——它自己的注释写着
// 「这正是硬件缺的那层控制」。于是那个测试能证明单行数值通路，却证明不了
// 完整执行时间、多行吞吐和存储停顿。
//
// `AttentionTileTop` 把时序搬进状态机、把跨趟累加搬进寄存器。这里要回答的
// 唯一问题是：**搬进去之后，算出来的还是同一个数吗。**
//
// 所以判据是「和 golden 参照逐维一致」，用的是同一份 tile.json、同一个容差
// 口径。时序自己发明一套的话，一次数值不符说不清是控制错了还是数据通路错了。
//
// 附带产出的是硬件自己数的拍数——那个数原来散在 C++ 循环里，没人看得见。

#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

#include "golden.h"

#include "VAttentionTileTop.h"
#include "verilated.h"
#ifdef DUMP_VCD
// 活动轨迹：用真实 Q/K/V 跑出来的翻转率喂给 OpenSTA 的 read_vcd，替掉
// 那个拍脑袋的 0.2。功耗模型现有的两个锚点里，RePEArray_L 明确记录用的是
// **默认常数 0.200** 而不是激励——只有 _S 是真实翻转率数出来的。
#include "verilated_vcd_c.h"
#endif

namespace {

constexpr int kPoint = 8;
constexpr int kTileQ = 4;
constexpr int kTileK = 32;
constexpr int kHeadDim = 8;
constexpr int kKept = 8;
constexpr int kPe = 8;
constexpr int kPasses = (kKept + kPe - 1) / kPe;

std::vector<std::vector<long>> matrix(const std::string& text, const char* key,
                                      int rows, int cols) {
    size_t cursor = text.find(key);
    if (cursor == std::string::npos) {
        std::fprintf(stderr, "tile.json 里没有 %s\n", key);
        std::exit(2);
    }
    std::vector<std::vector<long>> out(rows, std::vector<long>(cols, 0));
    size_t at = text.find('[', cursor);
    for (int r = 0; r < rows; r++) {
        at = text.find('[', at + 1);
        size_t end = text.find(']', at);
        std::string row = text.substr(at + 1, end - at - 1);
        const char* p = row.c_str();
        for (int c = 0; c < cols; c++) {
            char* next = nullptr;
            out[r][c] = std::strtol(p, &next, 10);
            if (next == p) break;
            p = next;
            while (*p == ',' || *p == ' ' || *p == '\n') p++;
        }
        at = end;
    }
    return out;
}

class Driver {
public:
    explicit Driver(VAttentionTileTop* dut) : dut_(dut) {}
#ifdef DUMP_VCD
    void attach(VerilatedVcdC* trace, uint64_t* time) { trace_ = trace; time_ = time; }
    VerilatedVcdC* trace_ = nullptr;
    // Verilator 5 的 dump 有多个重载，`long` 会歧义——必须给确定宽度。
    uint64_t* time_ = nullptr;
#endif

    void tick() {
        dut_->clock = 0; dut_->eval();
#ifdef DUMP_VCD
        if (trace_) trace_->dump(static_cast<uint64_t>(2 * (*time_)++));
#endif
        dut_->clock = 1; dut_->eval();
#ifdef DUMP_VCD
        if (trace_) trace_->dump(static_cast<uint64_t>(2 * (*time_)++));
#endif
    }

    void reset() {
        dut_->reset = 1;
        for (int i = 0; i < 4; i++) tick();
        dut_->reset = 0;
        dut_->eval();
    }

private:
    VAttentionTileTop* dut_;
};

}  // namespace

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    if (argc < 2) {
        std::fprintf(stderr, "用法: %s <tile.json>\n", argv[0]);
        return 2;
    }
    const std::string path = argv[1];
    const std::string text = golden::slurp(path.c_str());

    const auto q = matrix(text, "\"q_ticks\"", kTileQ, kHeadDim);
    const auto k = matrix(text, "\"k_ticks\"", kTileK, kHeadDim);
    const auto v = matrix(text, "\"v_ticks\"", kTileK, kHeadDim);
    const auto expected = matrix(text, "\"expected_sparse\"", kTileQ, kHeadDim);
    const auto kept = matrix(text, "\"expected_kept_idx\"", kTileQ, kKept);

    auto* dut = new VAttentionTileTop;
    Driver drv(dut);
#ifdef DUMP_VCD
    Verilated::traceEverOn(true);
    auto* trace = new VerilatedVcdC;
    dut->trace(trace, 99);
    trace->open("activity.vcd");
    uint64_t vcdTime = 0;
    drv.attach(trace, &vcdTime);
#endif

    int failures = 0, checked = 0, matched = 0;
    long deltaSum = 0;
    long totalCycles = 0;

    for (int row = 0; row < kTileQ; row++) {
        drv.reset();
        dut->io_perf_clear = 1; drv.tick(); dut->io_perf_clear = 0;

        // **每条 query 都送进阵列第 0 行**，和 golden testbench 同一个范围。
        //
        // 执行阵列是脉动列广播：`rows(i+1).regs_top := rows(i).regs_bottom`，
        // 所以第 r 行看到的列数据**延迟 r 拍**。喂数据时不补偿这个偏移的话，
        // 只有第 0 行是对的——实测把 query 装进第 1/2/3 行时误差随行号变大，
        // 而第 0 行全对。
        //
        // 这一步要回答的问题是「控制搬进硬件之后结果变不变」，所以范围必须
        // 和参照实现一致。多行并发是第三步的事，那时要处理的正是这个偏移。
        dut->io_row = 0;
        for (int d = 0; d < kHeadDim; d++)
            dut->io_q_in_0 = 0;  // 逐维在循环里给（见下）
        for (int s = 0; s < kKept; s++) {
            // 端口是展开的 Vec；用 __VformatN 的命名规则访问。
        }

        // Verilator 把 Vec 展开成 io_x_0 / io_x_1 ...，这里用宏统一处理。
#define SET_Q(i)   dut->io_q_in_##i = (unsigned short)(q[row][i] & 0xFFFF)
#define SET_IDX(i) dut->io_ext_idx_##i = (unsigned int)kept[row][i]; \
                   dut->io_ext_valid_##i = 1
        SET_Q(0); SET_Q(1); SET_Q(2); SET_Q(3);
        SET_Q(4); SET_Q(5); SET_Q(6); SET_Q(7);
        SET_IDX(0); SET_IDX(1); SET_IDX(2); SET_IDX(3);
        SET_IDX(4); SET_IDX(5); SET_IDX(6); SET_IDX(7);
#undef SET_Q
#undef SET_IDX

        // 启动，然后每拍按状态机的请求把 K/V 放上来。
        dut->io_start = 1;
        dut->eval();

        std::vector<long> got;
        const int budget = 4000;
        int cycle = 0;
        for (; cycle < budget; cycle++) {
            dut->eval();
            // 状态机说这一拍要哪个 (列, 维)。
            const int dim = dut->io_k_dim_req;
#define FEED(pe) { \
    const unsigned col = dut->io_k_col_req_##pe; \
    const bool act = dut->io_k_slot_active_##pe; \
    const long kv = act ? (dut->io_want_v ? v[col][dim] : k[col][dim]) : 0; \
    dut->io_k_data_##pe = (unsigned short)(kv & 0xFFFF); \
    dut->io_v_data_##pe = (unsigned short)(kv & 0xFFFF); }
            FEED(0) FEED(1) FEED(2) FEED(3)
            FEED(4) FEED(5) FEED(6) FEED(7)
#undef FEED
            dut->eval();
            drv.tick();
            if (dut->io_done) break;
        }

        if (cycle >= budget) {
            std::printf("FAIL 行 %d：状态机在 %d 拍内没有完成\n", row, budget);
            failures++;
            continue;
        }
        totalCycles += dut->io_total_cycles;

        // 收结果
        for (int d = 0; d < kHeadDim; d++) {
#define GET(i) case i: got.push_back((short)dut->io_out_##i); break;
            switch (d) { GET(0) GET(1) GET(2) GET(3) GET(4) GET(5) GET(6) GET(7) }
#undef GET
        }

        for (int d = 0; d < kHeadDim; d++) {
            checked++;
            const long want = expected[row][d];
            const long have = got[d];
            const long delta = have - want;
            deltaSum += delta;
            // 和 golden 测试同一个容差口径：定点末位若干。
            const long tolerance = 6 * kPasses;
            if (std::labs(delta) <= tolerance) matched++;
            else {
                if (failures < 8)
                    std::printf("  行 %d 维 %d: 硬件 %ld 参照 %ld 差 %ld\n",
                                row, d, have, want, delta);
                failures++;
            }
        }
        dut->io_start = 0;
        drv.tick();
    }

    std::printf("每行平均 %ld 拍（硬件自己数的）\n", totalCycles / kTileQ);
    std::printf("  QK %u  AV %u  归一化 %u  状态转换开销 %u\n",
                dut->io_qk_cycles, dut->io_av_cycles,
                dut->io_norm_cycles, dut->io_overhead_cycles);
    std::printf("有符号误差均值 %.3f\n", (double)deltaSum / (checked ? checked : 1));
    std::printf("%s: %d/%d\n", failures ? "FAILED" : "PASSED", matched, checked);
#ifdef DUMP_VCD
    trace->close();
    delete trace;
    std::printf("活动轨迹已写到 activity.vcd\n");
#endif
    delete dut;
    return failures ? 1 : 0;
}

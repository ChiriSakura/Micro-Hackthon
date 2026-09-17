module ProcessingLane (
    input wire clock,
    input wire reset,
    input wire p_valid_in,
    input wire [7:0] q_in,
    input wire [7:0] k_in,
    input wire [3:0] v_in,
    output wire p_valid_out,
    output wire [8:0] weight_out,
    output wire [12:0] weighted_v_out
);

    parameter THRESHOLD = 9'd64;

    // Stage 1: Score Calculation (Combinational Logic)
    wire [3:0] q0 = q_in[3:0];
    wire [3:0] q1 = q_in[7:4];
    wire [3:0] k0 = k_in[3:0];
    wire [3:0] k1 = k_in[7:4];

    wire [7:0] prod0 = q0 * k0;
    wire [7:0] prod1 = q1 * k1;

    // Widen before addition to avoid silent truncation. Sum of two 8-bit numbers needs 9 bits.
    wire [8:0] score_s1 = {1'b0, prod0} + {1'b0, prod1};

    // Pipeline Registers: Stage 1 -> Stage 2
    reg [8:0] score_s2_reg;
    reg [3:0] v_s2_reg;
    reg p_valid_s2_reg;

    always @(posedge clock) begin
        if (reset) begin
            score_s2_reg <= 9'd0;
            v_s2_reg <= 4'd0;
            p_valid_s2_reg <= 1'b0;
        end else begin
            p_valid_s2_reg <= p_valid_in;
            score_s2_reg <= score_s1;
            v_s2_reg <= v_in;
        end
    end

    // Stage 2: Weighting and Multiplication (Combinational Logic)
    wire [8:0] weight_s2;
    assign weight_s2 = (score_s2_reg >= THRESHOLD) ? score_s2_reg : 9'd0;

    // 9-bit weight * 4-bit value -> 13-bit result
    wire [12:0] weighted_v_s2 = weight_s2 * v_s2_reg;

    // Pipeline Registers: Stage 2 -> Output
    reg [8:0] weight_out_reg;
    reg [12:0] weighted_v_out_reg;
    reg p_valid_out_reg;

    always @(posedge clock) begin
        if (reset) begin
            weight_out_reg <= 9'd0;
            weighted_v_out_reg <= 13'd0;
            p_valid_out_reg <= 1'b0;
        end else begin
            p_valid_out_reg <= p_valid_s2_reg;
            weight_out_reg <= weight_s2;
            weighted_v_out_reg <= weighted_v_s2;
        end
    end

    // Assign registered outputs
    assign p_valid_out = p_valid_out_reg;
    assign weight_out = weight_out_reg;
    assign weighted_v_out = weighted_v_out_reg;

endmodule

/*
 * Module: ReductionDivider
 * 
 * Purpose: Sums the weights and weighted values from all four lanes and performs
 *          the final integer division to produce the result.
 * 
 * Implementation:
 * This module is controlled by a state machine with states IDLE, SUM, DIV_SETUP,
 * DIV_ITER, and DIV_DONE. Total latency is 18 cycles.
 * 
 * State: IDLE
 * - Waits for start_calc to go high.
 * 
 * State: SUM (1 cycle)
 * - On start_calc, it unpacks the 36-bit weights_in and 52-bit weighted_vs_in
 *   into four 9-bit weights and four 13-bit weighted values.
 * - Two parallel 2-level adder trees combinationally compute weight_sum (11 bits)
 *   and weighted_v_sum (15 bits).
 * - The sums are registered at the end of the cycle.
 * 
 * State: DIV_SETUP (1 cycle)
 * - Initializes a 15-iteration restoring integer divider.
 * - The registered weighted_v_sum is loaded into the quotient register Q (15 bits)
 *   and weight_sum into the divisor register M (padded to 15 bits). The remainder
 *   register A (16 bits) is cleared.
 * - A 5-bit counter is loaded with 15.
 * - If weight_sum is zero, the result is set to 0 and the state transitions
 *   directly to DIV_DONE.
 * 
 * State: DIV_ITER (15 cycles)
 * - The divider performs one iteration per cycle for 15 cycles.
 * - Each step consists of a left shift of {A, Q}, a subtraction A = A - M,
 *   and a conditional restoration of A based on its sign, which also determines
 *   the new LSB of Q.
 * 
 * State: DIV_DONE (1 cycle)
 * - The final quotient is in Q. The lower 4 bits are driven to result_out.
 * - calc_done is asserted for one cycle.
 * - The FSM returns to IDLE.
 */
module ReductionDivider (
    input wire clock,
    input wire reset,
    input wire start_calc,
    input wire [35:0] weights_in,
    input wire [51:0] weighted_vs_in,
    output wire [3:0] result_out,
    output wire calc_done
);

    // FSM state parameters
    localparam IDLE      = 3'd0;
    localparam SUM       = 3'd1;
    localparam DIV_SETUP = 3'd2;
    localparam DIV_ITER  = 3'd3;
    localparam DIV_DONE  = 3'd4;

    // State register
    reg [2:0] state;

    // Input unpacking and summation logic (combinational)
    wire [8:0] w0 = weights_in[8:0];
    wire [8:0] w1 = weights_in[17:9];
    wire [8:0] w2 = weights_in[26:18];
    wire [8:0] w3 = weights_in[35:27];

    wire [12:0] wv0 = weighted_vs_in[12:0];
    wire [12:0] wv1 = weighted_vs_in[25:13];
    wire [12:0] wv2 = weighted_vs_in[38:26];
    wire [12:0] wv3 = weighted_vs_in[51:39];

    // Widen unsigned expressions before addition to avoid silent truncation
    wire [9:0] sum_w_01 = {1'b0, w0} + {1'b0, w1};
    wire [9:0] sum_w_23 = {1'b0, w2} + {1'b0, w3};
    wire [10:0] weight_sum = {1'b0, sum_w_01} + {1'b0, sum_w_23};

    wire [13:0] sum_wv_01 = {1'b0, wv0} + {1'b0, wv1};
    wire [13:0] sum_wv_23 = {1'b0, wv2} + {1'b0, wv3};
    wire [14:0] weighted_v_sum = {1'b0, sum_wv_01} + {1'b0, sum_wv_23};

    // Registered sums
    reg [10:0] weight_sum_reg;
    reg [14:0] weighted_v_sum_reg;

    // Divider registers
    reg [15:0] div_A; // Remainder accumulator
    reg [14:0] div_Q; // Quotient (starts as dividend)
    reg [14:0] div_M; // Divisor
    reg [4:0]  iter_count;

    // Output register
    reg [3:0] result_out_reg;

    // Combinational logic for one step of restoring division
    wire [15:0] A_shifted = {div_A[14:0], div_Q[14]};
    wire [16:0] A_sub = {1'b0, A_shifted} - {2'b0, div_M};
    wire        restore = A_sub[16]; // Sign bit (1 if negative)
    wire        new_q_lsb = ~restore;

    wire [15:0] next_A = restore ? A_shifted : A_sub[15:0];
    wire [14:0] next_Q = {div_Q[13:0], new_q_lsb};

    // FSM and Datapath logic
    always @(posedge clock) begin
        if (reset) begin
            state <= IDLE;
            weight_sum_reg <= 11'd0;
            weighted_v_sum_reg <= 15'd0;
            div_A <= 16'd0;
            div_Q <= 15'd0;
            div_M <= 15'd0;
            iter_count <= 5'd0;
            result_out_reg <= 4'd0;
        end else begin
            case (state)
                IDLE: begin
                    if (start_calc) begin
                        state <= SUM;
                    end
                end
                SUM: begin
                    weight_sum_reg <= weight_sum;
                    weighted_v_sum_reg <= weighted_v_sum;
                    state <= DIV_SETUP;
                end
                DIV_SETUP: begin
                    if (weight_sum_reg == 11'd0) begin
                        result_out_reg <= 4'd0;
                        state <= DIV_DONE;
                    end else begin
                        div_A <= 16'd0;
                        div_Q <= weighted_v_sum_reg;
                        div_M <= {4'b0, weight_sum_reg};
                        iter_count <= 5'd15;
                        state <= DIV_ITER;
                    end
                end
                DIV_ITER: begin
                    div_A <= next_A;
                    div_Q <= next_Q;
                    iter_count <= iter_count - 1;
                    if (iter_count == 5'd1) begin
                        result_out_reg <= next_Q[3:0];
                        state <= DIV_DONE;
                    end
                end
                DIV_DONE: begin
                    state <= IDLE;
                end
                default: begin
                    state <= IDLE;
                end
            endcase
        end
    end

    // Output assignments
    assign calc_done = (state == DIV_DONE);
    assign result_out = result_out_reg;

endmodule

/*
 * Module: threshold_attention
 * 
 * Purpose: Top-level module that orchestrates the threshold attention computation,
 *          handles I/O, and manages the overall control flow.
 * 
 * Implementation:
 * The module uses a 2-state FSM (IDLE, BUSY). On a `start` pulse in IDLE, it
 * latches the `q`, `k`, and `v` inputs into registers and transitions to BUSY.
 * The latched inputs are then unpacked and fed to four parallel `ProcessingLane`
 * instances. A 4-stage pipeline register chain (`pipe_valid_reg`), triggered by
 * the initial `start`, generates the `p_valid_in` for the lanes, a latch enable
 * for the lane outputs, and the `start_calc` for the `ReductionDivider` at the
 * correct cycles. The outputs from the four lanes are registered and then
 * concatenated to be fed into the `ReductionDivider`. When the `ReductionDivider`
 * signals completion via its `calc_done` port, the FSM asserts the top-level
 * `done` signal for one cycle, updates the `result` output register, and
 * transitions back to IDLE. Total latency is 22 cycles.
 */
module threshold_attention (
    input wire clock,
    input wire reset,
    input wire start,
    input wire [7:0] q,
    input wire [31:0] k,
    input wire [15:0] v,
    output wire done,
    output wire [3:0] result
);

    // FSM state parameters
    localparam S_IDLE = 1'b0;
    localparam S_BUSY = 1'b1;

    // State and data registers
    reg state_reg;
    reg [7:0] q_reg;
    reg [31:0] k_reg;
    reg [15:0] v_reg;
    reg [3:0] pipe_valid_reg; // Control signal pipeline
    reg [35:0] all_weights_reg;
    reg [51:0] all_weighted_vs_reg;
    reg [3:0] result_reg;
    reg done_reg;

    // Wires for control and data path
    wire start_pulse = (state_reg == S_IDLE) && start;
    wire p_valid_in_wire = pipe_valid_reg[0];
    wire lane_outputs_valid_wire = pipe_valid_reg[2];
    wire start_calc_wire = pipe_valid_reg[3];
    wire calc_done_wire;
    wire [3:0] result_from_reducer;
    wire transaction_done = (state_reg == S_BUSY) && calc_done_wire;

    wire [8:0] lane_weights_out [0:3];
    wire [12:0] lane_weighted_vs_out [0:3];
    wire [0:3] lane_p_valid_out;

    // Main sequential logic block
    always @(posedge clock) begin
        if (reset) begin
            state_reg <= S_IDLE;
            q_reg <= 8'd0;
            k_reg <= 32'd0;
            v_reg <= 16'd0;
            pipe_valid_reg <= 4'd0;
            all_weights_reg <= 36'd0;
            all_weighted_vs_reg <= 52'd0;
            result_reg <= 4'd0;
            done_reg <= 1'b0;
        end else begin
            // FSM state transitions
            if (state_reg == S_IDLE) begin
                if (start) begin
                    state_reg <= S_BUSY;
                    // Latch inputs on start of a new transaction
                    q_reg <= q;
                    k_reg <= k;
                    v_reg <= v;
                end
            end else begin // S_BUSY
                if (calc_done_wire) begin
                    state_reg <= S_IDLE;
                end
            end

            // Pipeline valid signal propagation.
            // A '1' is injected on start_pulse and propagates through the shift register.
            pipe_valid_reg[0] <= start_pulse;
            pipe_valid_reg[1] <= pipe_valid_reg[0];
            pipe_valid_reg[2] <= pipe_valid_reg[1];
            pipe_valid_reg[3] <= pipe_valid_reg[2];

            // Latch lane outputs, triggered by the valid signal from the pipeline.
            if (lane_outputs_valid_wire) begin
                all_weights_reg <= {lane_weights_out[3], lane_weights_out[2], lane_weights_out[1], lane_weights_out[0]};
                all_weighted_vs_reg <= {lane_weighted_vs_out[3], lane_weighted_vs_out[2], lane_weighted_vs_out[1], lane_weighted_vs_out[0]};
            end

            // Final result and done signal generation
            done_reg <= transaction_done;
            if (transaction_done) begin
                result_reg <= result_from_reducer;
            end
        end
    end

    // Instantiate four ProcessingLanes in parallel
    genvar i;
    generate
        for (i = 0; i < 4; i = i + 1) begin : lane_gen
            ProcessingLane lane_inst (
                .clock(clock),
                .reset(reset),
                .p_valid_in(p_valid_in_wire),
                .q_in(q_reg),
                .k_in(k_reg[(i*8)+7 : i*8]),
                .v_in(v_reg[(i*4)+3 : i*4]),
                .p_valid_out(lane_p_valid_out[i]),
                .weight_out(lane_weights_out[i]),
                .weighted_v_out(lane_weighted_vs_out[i])
            );
        end
    endgenerate

    // Instantiate the Reduction and Division module
    ReductionDivider reducer_inst (
        .clock(clock),
        .reset(reset),
        .start_calc(start_calc_wire),
        .weights_in(all_weights_reg),
        .weighted_vs_in(all_weighted_vs_reg),
        .result_out(result_from_reducer),
        .calc_done(calc_done_wire)
    );

    // Assign outputs
    assign done = done_reg;
    assign result = result_reg;

endmodule

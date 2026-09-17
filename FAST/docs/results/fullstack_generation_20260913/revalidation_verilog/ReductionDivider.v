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

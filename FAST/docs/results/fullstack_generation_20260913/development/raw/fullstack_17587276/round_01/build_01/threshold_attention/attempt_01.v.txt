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

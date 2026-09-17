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

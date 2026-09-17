module ThresholdAttention(
  input wire clock,
  input wire reset,
  input wire start,
  input wire [7:0] q,
  input wire [31:0] k,
  input wire [15:0] v,
  output wire done,
  output wire [3:0] result
);

  // FSM state encoding
  localparam S_IDLE      = 3'd0;
  localparam S_S1_SCORE  = 3'd1;
  localparam S_S2_WEIGHT = 3'd2;
  localparam S_S3_AGG    = 3'd3;
  localparam S_S4_DIV_WAIT = 3'd4;
  localparam S_S5_DONE   = 3'd5;

  // FSM state registers
  reg [2:0] state_reg, state_next;

  // Pipeline registers
  reg [7:0] q_reg;
  reg [31:0] k_reg;
  reg [15:0] v_reg;

  reg [8:0] score_reg_0, score_reg_1, score_reg_2, score_reg_3;
  reg [8:0] weight_reg_0, weight_reg_1, weight_reg_2, weight_reg_3;
  reg [12:0] wv_reg_0, wv_reg_1, wv_reg_2, wv_reg_3;

  reg [10:0] sum_w_reg;
  reg [14:0] sum_wv_reg;

  reg [3:0] final_result_reg;

  // Wires for unpacking inputs
  wire [3:0] q0_in, q1_in;
  wire [3:0] k00_in, k01_in, k10_in, k11_in, k20_in, k21_in, k30_in, k31_in;
  wire [3:0] v0_in, v1_in, v2_in, v3_in;

  // Wires for module interconnections
  wire [8:0] score_out_0, score_out_1, score_out_2, score_out_3;
  wire [8:0] weight_out_0, weight_out_1, weight_out_2, weight_out_3;
  wire [12:0] wv_out_0, wv_out_1, wv_out_2, wv_out_3;
  wire [10:0] sum_w_out;
  wire [14:0] sum_wv_out;
  wire div_start;
  wire [3:0] div_quotient_out;
  wire div_done;

  // Unpack registered inputs based on protocol
  assign q0_in = q_reg[3:0];
  assign q1_in = q_reg[7:4];

  assign k00_in = k_reg[3:0];
  assign k01_in = k_reg[7:4];
  assign k10_in = k_reg[11:8];
  assign k11_in = k_reg[15:12];
  assign k20_in = k_reg[19:16];
  assign k21_in = k_reg[23:20];
  assign k30_in = k_reg[27:24];
  assign k31_in = k_reg[31:28];

  assign v0_in = v_reg[3:0];
  assign v1_in = v_reg[7:4];
  assign v2_in = v_reg[11:8];
  assign v3_in = v_reg[15:12];

  // Stage 1: Instantiate ScoreLane modules
  ScoreLane sl0 ( .q0_in(q0_in), .q1_in(q1_in), .k0_in(k00_in), .k1_in(k01_in), .score_out(score_out_0) );
  ScoreLane sl1 ( .q0_in(q0_in), .q1_in(q1_in), .k0_in(k10_in), .k1_in(k11_in), .score_out(score_out_1) );
  ScoreLane sl2 ( .q0_in(q0_in), .q1_in(q1_in), .k0_in(k20_in), .k1_in(k21_in), .score_out(score_out_2) );
  ScoreLane sl3 ( .q0_in(q0_in), .q1_in(q1_in), .k0_in(k30_in), .k1_in(k31_in), .score_out(score_out_3) );

  // Stage 2: Instantiate WeightLane modules
  WeightLane wl0 ( .score_in(score_reg_0), .v_in(v0_in), .weight_out(weight_out_0), .wv_out(wv_out_0) );
  WeightLane wl1 ( .score_in(score_reg_1), .v_in(v1_in), .weight_out(weight_out_1), .wv_out(wv_out_1) );
  WeightLane wl2 ( .score_in(score_reg_2), .v_in(v2_in), .weight_out(weight_out_2), .wv_out(wv_out_2) );
  WeightLane wl3 ( .score_in(score_reg_3), .v_in(v3_in), .weight_out(weight_out_3), .wv_out(wv_out_3) );

  // Stage 3: Instantiate Aggregator module
  Aggregator agg (
    .w_in_0(weight_reg_0), .w_in_1(weight_reg_1), .w_in_2(weight_reg_2), .w_in_3(weight_reg_3),
    .wv_in_0(wv_reg_0), .wv_in_1(wv_reg_1), .wv_in_2(wv_reg_2), .wv_in_3(wv_reg_3),
    .sum_w_out(sum_w_out), .sum_wv_out(sum_wv_out)
  );

  // Stage 4: Instantiate Divider module
  assign div_start = (state_reg == S_S3_AGG);
  Divider_15_11_4 divider (
    .clock(clock), .reset(reset), .start_in(div_start),
    .dividend_in(sum_wv_reg), .divisor_in(sum_w_reg),
    .quotient_out(div_quotient_out), .done_out(div_done)
  );

  // FSM sequential logic
  always @(posedge clock) begin
    if (reset) begin
      state_reg <= S_IDLE;
    end else begin
      state_reg <= state_next;
    end
  end

  // FSM combinational logic
  always @(*) begin
    state_next = state_reg;
    case (state_reg)
      S_IDLE: if (start) state_next = S_S1_SCORE;
      S_S1_SCORE: state_next = S_S2_WEIGHT;
      S_S2_WEIGHT: state_next = S_S3_AGG;
      S_S3_AGG: state_next = S_S4_DIV_WAIT;
      S_S4_DIV_WAIT: if (div_done) state_next = S_S5_DONE;
      S_S5_DONE: state_next = S_IDLE;
      default: state_next = S_IDLE;
    endcase
  end

  // Pipeline registers update logic
  always @(posedge clock) begin
    if (reset) begin
      q_reg <= 8'd0;
      k_reg <= 32'd0;
      v_reg <= 16'd0;
      score_reg_0 <= 9'd0;
      score_reg_1 <= 9'd0;
      score_reg_2 <= 9'd0;
      score_reg_3 <= 9'd0;
      weight_reg_0 <= 9'd0;
      weight_reg_1 <= 9'd0;
      weight_reg_2 <= 9'd0;
      weight_reg_3 <= 9'd0;
      wv_reg_0 <= 13'd0;
      wv_reg_1 <= 13'd0;
      wv_reg_2 <= 13'd0;
      wv_reg_3 <= 13'd0;
      sum_w_reg <= 11'd0;
      sum_wv_reg <= 15'd0;
      final_result_reg <= 4'd0;
    end else begin
      // Stage 0 -> 1: Latch inputs
      if (state_reg == S_IDLE && start) begin
        q_reg <= q;
        k_reg <= k;
        v_reg <= v;
      end

      // Stage 1 -> 2: Latch scores
      if (state_reg == S_S1_SCORE) begin
        score_reg_0 <= score_out_0;
        score_reg_1 <= score_out_1;
        score_reg_2 <= score_out_2;
        score_reg_3 <= score_out_3;
      end

      // Stage 2 -> 3: Latch weights and weighted values
      if (state_reg == S_S2_WEIGHT) begin
        weight_reg_0 <= weight_out_0;
        weight_reg_1 <= weight_out_1;
        weight_reg_2 <= weight_out_2;
        weight_reg_3 <= weight_out_3;
        wv_reg_0 <= wv_out_0;
        wv_reg_1 <= wv_out_1;
        wv_reg_2 <= wv_out_2;
        wv_reg_3 <= wv_out_3;
      end

      // Stage 3 -> 4: Latch sums
      if (state_reg == S_S3_AGG) begin
        sum_w_reg <= sum_w_out;
        sum_wv_reg <= sum_wv_out;
      end

      // Stage 4 -> 5: Latch final result
      if (state_reg == S_S4_DIV_WAIT && div_done) begin
        final_result_reg <= div_quotient_out;
      end
    end
  end

  // Output assignments
  assign done = (state_reg == S_S5_DONE);
  assign result = final_result_reg;

endmodule

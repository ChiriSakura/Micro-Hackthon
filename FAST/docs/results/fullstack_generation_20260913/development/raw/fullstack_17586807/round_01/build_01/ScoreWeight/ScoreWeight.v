module ScoreWeight (
    input  [3:0] q0,
    input  [3:0] q1,
    input  [3:0] k0,
    input  [3:0] k1,
    input  [3:0] v_in,
    output [8:0] weight,
    output [12:0] weighted_v
);

parameter THRESHOLD = 0;

wire [7:0] p0;
wire [7:0] p1;
wire [8:0] score;

// 1. Two 4x4 multipliers compute p0 = q0 * k0 and p1 = q1 * k1.
assign p0 = q0 * k0;
assign p1 = q1 * k1;

// 2. An adder sums the products: score[8:0] = p0 + p1.
//    Max score is 15*15 + 15*15 = 450, which fits in 9 bits.
//    Widen operands before addition to prevent silent truncation.
assign score = {1'b0, p0} + {1'b0, p1};

// 3. A 9-bit comparator checks if score >= THRESHOLD.
// 4. A mux selects the weight: weight = (score >= THRESHOLD) ? score : 9'd0.
assign weight = (score >= THRESHOLD) ? score : 9'd0;

// 5. A 9x4 multiplier computes weighted_v = weight * v_in.
//    Max weight is 450, max v_in is 15. Max product is 450 * 15 = 6750.
//    This fits in 13 bits (2^13 - 1 = 8191).
assign weighted_v = weight * v_in;

endmodule

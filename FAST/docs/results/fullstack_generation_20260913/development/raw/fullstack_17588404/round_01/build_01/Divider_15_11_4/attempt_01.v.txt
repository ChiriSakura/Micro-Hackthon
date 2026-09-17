module Divider_15_11_4(
  input wire clock,
  input wire reset,
  input wire start_in,
  input wire [14:0] dividend_in,
  input wire [10:0] divisor_in,
  output wire [3:0] quotient_out,
  output wire done_out
);

  localparam IDLE = 2'b00;
  localparam CALC = 2'b01;
  localparam DONE_S = 2'b10;

  reg [1:0] state_reg;
  reg [14:0] remainder_reg;
  reg [10:0] divisor_reg;
  reg [3:0] quotient_reg;
  reg [1:0] count_reg;

  wire [14:0] shifted_divisor;
  wire [15:0] sub_res_ext;
  wire subtract_ok;
  wire [14:0] sub_result;

  // Widen the 11-bit divisor to 15 bits before shifting to prevent truncation.
  // The shift amount is at most 3.
  assign shifted_divisor = (15'd0 + divisor_reg) << count_reg;

  // Perform subtraction: remainder - shifted_divisor. Use 16 bits to capture the borrow-out.
  assign sub_res_ext = {1'b0, remainder_reg} - {1'b0, shifted_divisor};
  assign subtract_ok = !sub_res_ext[15]; // If MSB is 0, no borrow occurred, so remainder >= shifted_divisor.
  assign sub_result = sub_res_ext[14:0];

  always @(posedge clock) begin
    if (reset) begin
      state_reg <= IDLE;
      remainder_reg <= 15'd0;
      divisor_reg <= 11'd0;
      quotient_reg <= 4'd0;
      count_reg <= 2'd0;
    end else begin
      case (state_reg)
        IDLE: begin
          if (start_in) begin
            remainder_reg <= dividend_in;
            divisor_reg <= divisor_in;
            if (divisor_in == 11'd0) begin
              quotient_reg <= 4'd0;
              state_reg <= DONE_S;
            end else begin
              quotient_reg <= 4'd0;
              count_reg <= 2'd3;
              state_reg <= CALC;
            end
          end
        end

        CALC: begin
          // This is one step of restoring division.
          if (subtract_ok) begin
            remainder_reg <= sub_result;
            // Set the corresponding quotient bit. The OR operation correctly sets the bit
            // for the current iteration without affecting previously set bits.
            quotient_reg <= quotient_reg | (4'd1 << count_reg);
          end
          // If not subtract_ok, the remainder is not updated (restored) and the quotient bit remains 0.

          // Decrement counter and check for completion after 4 iterations (count 3, 2, 1, 0).
          if (count_reg == 2'd0) begin
            state_reg <= DONE_S;
          end else begin
            count_reg <= count_reg - 1;
          end
        end

        DONE_S: begin
          state_reg <= IDLE;
          // The result in quotient_reg is held until the next transaction starts.
        end
        
        default: begin
            state_reg <= IDLE;
        end
      endcase
    end
  end

  assign quotient_out = quotient_reg;
  assign done_out = (state_reg == DONE_S);

endmodule

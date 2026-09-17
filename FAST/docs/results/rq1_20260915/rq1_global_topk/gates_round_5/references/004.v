// Read-only example of a synchronous valid/data register. It is a reference,
// not a mandatory module, prewritten attention datapath, or generated output.
module ReferenceRegister(input clock, input reset, input valid_in,
                         input [15:0] data_in,
                         output reg valid_out, output reg [15:0] data_out);
  always @(posedge clock) begin
    if (reset) begin valid_out <= 0; data_out <= 0; end
    else begin valid_out <= valid_in; if(valid_in) data_out <= data_in; end
  end
endmodule

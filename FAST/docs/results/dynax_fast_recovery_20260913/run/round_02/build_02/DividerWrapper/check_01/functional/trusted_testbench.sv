module FASTTestbench;
reg [0:0] clock;
reg [0:0] reset;
reg [0:0] valid_in;
reg [27:0] N_in;
reg [18:0] D_in;
wire [15:0] result_out;
wire [0:0] valid_out;
DividerWrapper dut(.clock(clock),.reset(reset),.valid_in(valid_in),.N_in(N_in),.D_in(D_in),.result_out(result_out),.valid_out(valid_out));
initial begin
clock=0;
reset=1'd1;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=0 output=valid_out expected=0 actual=%0d",valid_out);
if (result_out !== 16'd0) $fatal(1,"module case=0 step=0 output=result_out expected=0 actual=%0d",result_out);
reset=1'd0;
valid_in=1'd1;
N_in=28'd0;
D_in=19'd1;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=1 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=2 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=3 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=4 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=5 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=6 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=7 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=0 step=8 output=valid_out expected=1 actual=%0d",valid_out);
if (result_out !== 16'd0) $fatal(1,"module case=0 step=8 output=result_out expected=0 actual=%0d",result_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=9 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd1;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=10 output=valid_out expected=0 actual=%0d",valid_out);
if (result_out !== 16'd0) $fatal(1,"module case=0 step=10 output=result_out expected=0 actual=%0d",result_out);
$display("FAST_CASE cycles=1");
reset=1'd1;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=0 output=valid_out expected=0 actual=%0d",valid_out);
if (result_out !== 16'd0) $fatal(1,"module case=1 step=0 output=result_out expected=0 actual=%0d",result_out);
reset=1'd0;
valid_in=1'd1;
N_in=28'd1000;
D_in=19'd10;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=1 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=2 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=3 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=4 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=5 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=6 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=7 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=1 step=8 output=valid_out expected=1 actual=%0d",valid_out);
if (result_out !== 16'd1600) $fatal(1,"module case=1 step=8 output=result_out expected=1600 actual=%0d",result_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=9 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd1;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=10 output=valid_out expected=0 actual=%0d",valid_out);
if (result_out !== 16'd0) $fatal(1,"module case=1 step=10 output=result_out expected=0 actual=%0d",result_out);
$display("FAST_CASE cycles=1");
reset=1'd1;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=0 output=valid_out expected=0 actual=%0d",valid_out);
if (result_out !== 16'd0) $fatal(1,"module case=2 step=0 output=result_out expected=0 actual=%0d",result_out);
reset=1'd0;
valid_in=1'd1;
N_in=28'd134217727;
D_in=19'd524287;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=1 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=2 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=3 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=4 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=5 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=6 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=7 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=2 step=8 output=valid_out expected=1 actual=%0d",valid_out);
if (result_out !== 16'd4096) $fatal(1,"module case=2 step=8 output=result_out expected=4096 actual=%0d",result_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=9 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd1;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=10 output=valid_out expected=0 actual=%0d",valid_out);
if (result_out !== 16'd0) $fatal(1,"module case=2 step=10 output=result_out expected=0 actual=%0d",result_out);
$display("FAST_CASE cycles=1");
reset=1'd1;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=0 output=valid_out expected=0 actual=%0d",valid_out);
if (result_out !== 16'd0) $fatal(1,"module case=3 step=0 output=result_out expected=0 actual=%0d",result_out);
reset=1'd0;
valid_in=1'd1;
N_in=28'd0;
D_in=19'd1;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=1 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd1;
N_in=28'd1000;
D_in=19'd10;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=2 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd1;
N_in=28'd134217727;
D_in=19'd524287;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=3 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=4 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd1;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=5 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd1;
N_in=28'd6591832;
D_in=19'd492388;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=6 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd1;
N_in=28'd60343676;
D_in=19'd411919;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=7 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=8 output=valid_out expected=1 actual=%0d",valid_out);
if (result_out !== 16'd0) $fatal(1,"module case=3 step=8 output=result_out expected=0 actual=%0d",result_out);
reset=1'd0;
valid_in=1'd1;
N_in=28'd75621076;
D_in=19'd45370;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=9 output=valid_out expected=1 actual=%0d",valid_out);
if (result_out !== 16'd1600) $fatal(1,"module case=3 step=9 output=result_out expected=1600 actual=%0d",result_out);
reset=1'd0;
valid_in=1'd1;
N_in=28'd74459125;
D_in=19'd117905;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=10 output=valid_out expected=1 actual=%0d",valid_out);
if (result_out !== 16'd4096) $fatal(1,"module case=3 step=10 output=result_out expected=4096 actual=%0d",result_out);
reset=1'd0;
valid_in=1'd1;
N_in=28'd124447943;
D_in=19'd146372;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=11 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=12 output=valid_out expected=1 actual=%0d",valid_out);
if (result_out !== 16'd0) $fatal(1,"module case=3 step=12 output=result_out expected=0 actual=%0d",result_out);
reset=1'd0;
valid_in=1'd1;
N_in=28'd79135424;
D_in=19'd34724;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=13 output=valid_out expected=1 actual=%0d",valid_out);
if (result_out !== 16'd214) $fatal(1,"module case=3 step=13 output=result_out expected=214 actual=%0d",result_out);
reset=1'd0;
valid_in=1'd1;
N_in=28'd32543666;
D_in=19'd143212;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=14 output=valid_out expected=1 actual=%0d",valid_out);
if (result_out !== 16'd2343) $fatal(1,"module case=3 step=14 output=result_out expected=2343 actual=%0d",result_out);
reset=1'd0;
valid_in=1'd1;
N_in=28'd124108027;
D_in=19'd469500;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=15 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=16 output=valid_out expected=1 actual=%0d",valid_out);
if (result_out !== 16'd26668) $fatal(1,"module case=3 step=16 output=result_out expected=26668 actual=%0d",result_out);
reset=1'd0;
valid_in=1'd1;
N_in=28'd221496879;
D_in=19'd214883;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=17 output=valid_out expected=1 actual=%0d",valid_out);
if (result_out !== 16'd10104) $fatal(1,"module case=3 step=17 output=result_out expected=10104 actual=%0d",result_out);
reset=1'd0;
valid_in=1'd1;
N_in=28'd49988799;
D_in=19'd123887;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=18 output=valid_out expected=1 actual=%0d",valid_out);
if (result_out !== 16'd13603) $fatal(1,"module case=3 step=18 output=result_out expected=13603 actual=%0d",result_out);
reset=1'd0;
valid_in=1'd1;
N_in=28'd10934157;
D_in=19'd422519;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=19 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=20 output=valid_out expected=1 actual=%0d",valid_out);
if (result_out !== 16'd36463) $fatal(1,"module case=3 step=20 output=result_out expected=36463 actual=%0d",result_out);
reset=1'd0;
valid_in=1'd1;
N_in=28'd183359260;
D_in=19'd208139;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=21 output=valid_out expected=1 actual=%0d",valid_out);
if (result_out !== 16'd3635) $fatal(1,"module case=3 step=21 output=result_out expected=3635 actual=%0d",result_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=22 output=valid_out expected=1 actual=%0d",valid_out);
if (result_out !== 16'd4229) $fatal(1,"module case=3 step=22 output=result_out expected=4229 actual=%0d",result_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=23 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=24 output=valid_out expected=1 actual=%0d",valid_out);
if (result_out !== 16'd62041) $fatal(1,"module case=3 step=24 output=result_out expected=62041 actual=%0d",result_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=25 output=valid_out expected=1 actual=%0d",valid_out);
if (result_out !== 16'd6456) $fatal(1,"module case=3 step=25 output=result_out expected=6456 actual=%0d",result_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=26 output=valid_out expected=1 actual=%0d",valid_out);
if (result_out !== 16'd414) $fatal(1,"module case=3 step=26 output=result_out expected=414 actual=%0d",result_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=27 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=28 output=valid_out expected=1 actual=%0d",valid_out);
if (result_out !== 16'd58997) $fatal(1,"module case=3 step=28 output=result_out expected=58997 actual=%0d",result_out);
reset=1'd0;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=29 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd1;
valid_in=1'd0;
N_in=28'd0;
D_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=30 output=valid_out expected=0 actual=%0d",valid_out);
if (result_out !== 16'd0) $fatal(1,"module case=3 step=30 output=result_out expected=0 actual=%0d",result_out);
$display("FAST_CASE cycles=1");
$display("FAST_PASS cases=4");
$finish;
end
endmodule
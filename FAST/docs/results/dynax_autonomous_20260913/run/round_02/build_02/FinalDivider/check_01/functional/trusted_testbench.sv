module FASTTestbench;
reg [0:0] clock;
reg [0:0] reset;
reg [0:0] valid_in;
reg [26:0] numer_in;
reg [18:0] denom_in;
wire [0:0] valid_out;
wire [15:0] quot_out;
FinalDivider dut(.clock(clock),.reset(reset),.valid_in(valid_in),.numer_in(numer_in),.denom_in(denom_in),.valid_out(valid_out),.quot_out(quot_out));
initial begin
clock=0;
reset=1'd1;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=0 output=valid_out expected=0 actual=%0d",valid_out);
if (quot_out !== 16'd0) $fatal(1,"module case=0 step=0 output=quot_out expected=0 actual=%0d",quot_out);
reset=1'd0;
valid_in=1'd1;
numer_in=27'd0;
denom_in=19'd100;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=1 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=2 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=3 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=4 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=5 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=6 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=7 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=8 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=0 step=9 output=valid_out expected=1 actual=%0d",valid_out);
if (quot_out !== 16'd0) $fatal(1,"module case=0 step=9 output=quot_out expected=0 actual=%0d",quot_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=10 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd1;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=11 output=valid_out expected=0 actual=%0d",valid_out);
if (quot_out !== 16'd0) $fatal(1,"module case=0 step=11 output=quot_out expected=0 actual=%0d",quot_out);
$display("FAST_CASE cycles=1");
reset=1'd1;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=0 output=valid_out expected=0 actual=%0d",valid_out);
if (quot_out !== 16'd0) $fatal(1,"module case=1 step=0 output=quot_out expected=0 actual=%0d",quot_out);
reset=1'd0;
valid_in=1'd1;
numer_in=27'd1000;
denom_in=19'd10;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=1 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=2 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=3 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=4 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=5 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=6 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=7 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=8 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=1 step=9 output=valid_out expected=1 actual=%0d",valid_out);
if (quot_out !== 16'd1600) $fatal(1,"module case=1 step=9 output=quot_out expected=1600 actual=%0d",quot_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=10 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd1;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=11 output=valid_out expected=0 actual=%0d",valid_out);
if (quot_out !== 16'd0) $fatal(1,"module case=1 step=11 output=quot_out expected=0 actual=%0d",quot_out);
$display("FAST_CASE cycles=1");
reset=1'd1;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=0 output=valid_out expected=0 actual=%0d",valid_out);
if (quot_out !== 16'd0) $fatal(1,"module case=2 step=0 output=quot_out expected=0 actual=%0d",quot_out);
reset=1'd0;
valid_in=1'd1;
numer_in=27'd67107840;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=1 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=2 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=3 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=4 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=5 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=6 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=7 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=8 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=2 step=9 output=valid_out expected=1 actual=%0d",valid_out);
if (quot_out !== 16'd0) $fatal(1,"module case=2 step=9 output=quot_out expected=0 actual=%0d",quot_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=10 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd1;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=11 output=valid_out expected=0 actual=%0d",valid_out);
if (quot_out !== 16'd0) $fatal(1,"module case=2 step=11 output=quot_out expected=0 actual=%0d",quot_out);
$display("FAST_CASE cycles=1");
reset=1'd1;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=0 output=valid_out expected=0 actual=%0d",valid_out);
if (quot_out !== 16'd0) $fatal(1,"module case=3 step=0 output=quot_out expected=0 actual=%0d",quot_out);
reset=1'd0;
valid_in=1'd1;
numer_in=27'd0;
denom_in=19'd100;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=1 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd1;
numer_in=27'd1000;
denom_in=19'd10;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=2 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd1;
numer_in=27'd67107840;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=3 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=4 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd1;
numer_in=27'd3295916;
denom_in=19'd492388;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=5 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd1;
numer_in=27'd30171838;
denom_in=19'd411919;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=6 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd1;
numer_in=27'd37810538;
denom_in=19'd45370;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=7 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=8 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd1;
numer_in=27'd37229562;
denom_in=19'd117905;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=9 output=valid_out expected=1 actual=%0d",valid_out);
if (quot_out !== 16'd0) $fatal(1,"module case=3 step=9 output=quot_out expected=0 actual=%0d",quot_out);
reset=1'd0;
valid_in=1'd1;
numer_in=27'd62223971;
denom_in=19'd146372;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=10 output=valid_out expected=1 actual=%0d",valid_out);
if (quot_out !== 16'd1600) $fatal(1,"module case=3 step=10 output=quot_out expected=1600 actual=%0d",quot_out);
reset=1'd0;
valid_in=1'd1;
numer_in=27'd39567712;
denom_in=19'd34724;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=11 output=valid_out expected=1 actual=%0d",valid_out);
if (quot_out !== 16'd0) $fatal(1,"module case=3 step=11 output=quot_out expected=0 actual=%0d",quot_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=12 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd1;
numer_in=27'd16271833;
denom_in=19'd143212;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=13 output=valid_out expected=1 actual=%0d",valid_out);
if (quot_out !== 16'd107) $fatal(1,"module case=3 step=13 output=quot_out expected=107 actual=%0d",quot_out);
reset=1'd0;
valid_in=1'd1;
numer_in=27'd62054013;
denom_in=19'd469500;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=14 output=valid_out expected=1 actual=%0d",valid_out);
if (quot_out !== 16'd1171) $fatal(1,"module case=3 step=14 output=quot_out expected=1171 actual=%0d",quot_out);
reset=1'd0;
valid_in=1'd1;
numer_in=27'd110748439;
denom_in=19'd214883;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=15 output=valid_out expected=1 actual=%0d",valid_out);
if (quot_out !== 16'd13334) $fatal(1,"module case=3 step=15 output=quot_out expected=13334 actual=%0d",quot_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=16 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd1;
numer_in=27'd24994399;
denom_in=19'd123887;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=17 output=valid_out expected=1 actual=%0d",valid_out);
if (quot_out !== 16'd5052) $fatal(1,"module case=3 step=17 output=quot_out expected=5052 actual=%0d",quot_out);
reset=1'd0;
valid_in=1'd1;
numer_in=27'd5467078;
denom_in=19'd422519;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=18 output=valid_out expected=1 actual=%0d",valid_out);
if (quot_out !== 16'd6801) $fatal(1,"module case=3 step=18 output=quot_out expected=6801 actual=%0d",quot_out);
reset=1'd0;
valid_in=1'd1;
numer_in=27'd91679630;
denom_in=19'd208139;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=19 output=valid_out expected=1 actual=%0d",valid_out);
if (quot_out !== 16'd18231) $fatal(1,"module case=3 step=19 output=quot_out expected=18231 actual=%0d",quot_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=20 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=21 output=valid_out expected=1 actual=%0d",valid_out);
if (quot_out !== 16'd1817) $fatal(1,"module case=3 step=21 output=quot_out expected=1817 actual=%0d",quot_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=22 output=valid_out expected=1 actual=%0d",valid_out);
if (quot_out !== 16'd2114) $fatal(1,"module case=3 step=22 output=quot_out expected=2114 actual=%0d",quot_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=23 output=valid_out expected=1 actual=%0d",valid_out);
if (quot_out !== 16'd63789) $fatal(1,"module case=3 step=23 output=quot_out expected=63789 actual=%0d",quot_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=24 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=25 output=valid_out expected=1 actual=%0d",valid_out);
if (quot_out !== 16'd3228) $fatal(1,"module case=3 step=25 output=quot_out expected=3228 actual=%0d",quot_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=26 output=valid_out expected=1 actual=%0d",valid_out);
if (quot_out !== 16'd207) $fatal(1,"module case=3 step=26 output=quot_out expected=207 actual=%0d",quot_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=27 output=valid_out expected=1 actual=%0d",valid_out);
if (quot_out !== 16'd62267) $fatal(1,"module case=3 step=27 output=quot_out expected=62267 actual=%0d",quot_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=28 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=29 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd1;
valid_in=1'd0;
numer_in=27'd0;
denom_in=19'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=30 output=valid_out expected=0 actual=%0d",valid_out);
if (quot_out !== 16'd0) $fatal(1,"module case=3 step=30 output=quot_out expected=0 actual=%0d",quot_out);
$display("FAST_CASE cycles=1");
$display("FAST_PASS cases=4");
$finish;
end
endmodule
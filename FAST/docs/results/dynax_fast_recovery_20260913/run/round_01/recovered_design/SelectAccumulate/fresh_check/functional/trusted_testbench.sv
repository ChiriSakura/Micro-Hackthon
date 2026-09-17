module FASTTestbench;
reg [0:0] clock;
reg [0:0] reset;
reg [0:0] valid_in;
reg [71:0] scores_in;
reg [127:0] weights_in;
reg [63:0] values_in;
wire [27:0] N_out;
wire [18:0] D_out;
wire [7:0] keep_mask_out;
wire [0:0] valid_out;
SelectAccumulate dut(.clock(clock),.reset(reset),.valid_in(valid_in),.scores_in(scores_in),.weights_in(weights_in),.values_in(values_in),.N_out(N_out),.D_out(D_out),.keep_mask_out(keep_mask_out),.valid_out(valid_out));
initial begin
clock=0;
reset=1'd1;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=0 output=valid_out expected=0 actual=%0d",valid_out);
if (N_out !== 28'd0) $fatal(1,"module case=0 step=0 output=N_out expected=0 actual=%0d",N_out);
if (D_out !== 19'd0) $fatal(1,"module case=0 step=0 output=D_out expected=0 actual=%0d",D_out);
if (keep_mask_out !== 8'd0) $fatal(1,"module case=0 step=0 output=keep_mask_out expected=0 actual=%0d",keep_mask_out);
reset=1'd0;
valid_in=1'd1;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=1 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=2 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=3 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=4 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=0 step=5 output=valid_out expected=1 actual=%0d",valid_out);
if (N_out !== 28'd0) $fatal(1,"module case=0 step=5 output=N_out expected=0 actual=%0d",N_out);
if (D_out !== 19'd0) $fatal(1,"module case=0 step=5 output=D_out expected=0 actual=%0d",D_out);
if (keep_mask_out !== 8'd17) $fatal(1,"module case=0 step=5 output=keep_mask_out expected=17 actual=%0d",keep_mask_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=6 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd1;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=7 output=valid_out expected=0 actual=%0d",valid_out);
if (N_out !== 28'd0) $fatal(1,"module case=0 step=7 output=N_out expected=0 actual=%0d",N_out);
if (D_out !== 19'd0) $fatal(1,"module case=0 step=7 output=D_out expected=0 actual=%0d",D_out);
if (keep_mask_out !== 8'd0) $fatal(1,"module case=0 step=7 output=keep_mask_out expected=0 actual=%0d",keep_mask_out);
$display("FAST_CASE cycles=1");
reset=1'd1;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=0 output=valid_out expected=0 actual=%0d",valid_out);
if (N_out !== 28'd0) $fatal(1,"module case=1 step=0 output=N_out expected=0 actual=%0d",N_out);
if (D_out !== 19'd0) $fatal(1,"module case=1 step=0 output=D_out expected=0 actual=%0d",D_out);
if (keep_mask_out !== 8'd0) $fatal(1,"module case=1 step=0 output=keep_mask_out expected=0 actual=%0d",keep_mask_out);
reset=1'd0;
valid_in=1'd1;
scores_in=72'd832268032761797027850;
weights_in=128'd51923760879062861620415854748631140;
values_in=64'd578437695752307201;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=1 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=2 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=3 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=4 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=1 step=5 output=valid_out expected=1 actual=%0d",valid_out);
if (N_out !== 28'd600) $fatal(1,"module case=1 step=5 output=N_out expected=600 actual=%0d",N_out);
if (D_out !== 19'd200) $fatal(1,"module case=1 step=5 output=D_out expected=200 actual=%0d",D_out);
if (keep_mask_out !== 8'd10) $fatal(1,"module case=1 step=5 output=keep_mask_out expected=10 actual=%0d",keep_mask_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=6 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd1;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=7 output=valid_out expected=0 actual=%0d",valid_out);
if (N_out !== 28'd0) $fatal(1,"module case=1 step=7 output=N_out expected=0 actual=%0d",N_out);
if (D_out !== 19'd0) $fatal(1,"module case=1 step=7 output=D_out expected=0 actual=%0d",D_out);
if (keep_mask_out !== 8'd0) $fatal(1,"module case=1 step=7 output=keep_mask_out expected=0 actual=%0d",keep_mask_out);
$display("FAST_CASE cycles=1");
reset=1'd1;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=0 output=valid_out expected=0 actual=%0d",valid_out);
if (N_out !== 28'd0) $fatal(1,"module case=2 step=0 output=N_out expected=0 actual=%0d",N_out);
if (D_out !== 19'd0) $fatal(1,"module case=2 step=0 output=D_out expected=0 actual=%0d",D_out);
if (keep_mask_out !== 8'd0) $fatal(1,"module case=2 step=0 output=keep_mask_out expected=0 actual=%0d",keep_mask_out);
reset=1'd0;
valid_in=1'd1;
scores_in=72'd92414216885903037450;
weights_in=128'd340282366920938463463374607431768211455;
values_in=64'd143973900865208192;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=1 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=2 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=3 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=4 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=2 step=5 output=valid_out expected=1 actual=%0d",valid_out);
if (N_out !== 28'd251658496) $fatal(1,"module case=2 step=5 output=N_out expected=251658496 actual=%0d",N_out);
if (D_out !== 19'd131070) $fatal(1,"module case=2 step=5 output=D_out expected=131070 actual=%0d",D_out);
if (keep_mask_out !== 8'd17) $fatal(1,"module case=2 step=5 output=keep_mask_out expected=17 actual=%0d",keep_mask_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=6 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd1;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=7 output=valid_out expected=0 actual=%0d",valid_out);
if (N_out !== 28'd0) $fatal(1,"module case=2 step=7 output=N_out expected=0 actual=%0d",N_out);
if (D_out !== 19'd0) $fatal(1,"module case=2 step=7 output=D_out expected=0 actual=%0d",D_out);
if (keep_mask_out !== 8'd0) $fatal(1,"module case=2 step=7 output=keep_mask_out expected=0 actual=%0d",keep_mask_out);
$display("FAST_CASE cycles=1");
reset=1'd1;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=0 output=valid_out expected=0 actual=%0d",valid_out);
if (N_out !== 28'd0) $fatal(1,"module case=3 step=0 output=N_out expected=0 actual=%0d",N_out);
if (D_out !== 19'd0) $fatal(1,"module case=3 step=0 output=D_out expected=0 actual=%0d",D_out);
if (keep_mask_out !== 8'd0) $fatal(1,"module case=3 step=0 output=keep_mask_out expected=0 actual=%0d",keep_mask_out);
reset=1'd0;
valid_in=1'd1;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=1 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd1;
scores_in=72'd832268032761797027850;
weights_in=128'd51923760879062861620415854748631140;
values_in=64'd578437695752307201;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=2 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd1;
scores_in=72'd92414216885903037450;
weights_in=128'd340282366920938463463374607431768211455;
values_in=64'd143973900865208192;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=3 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=4 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd1;
scores_in=72'd1060126600920943602371;
weights_in=128'd232706954871686115284115957884067773710;
values_in=64'd17529341237428043689;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=5 output=valid_out expected=1 actual=%0d",valid_out);
if (N_out !== 28'd0) $fatal(1,"module case=3 step=5 output=N_out expected=0 actual=%0d",N_out);
if (D_out !== 19'd0) $fatal(1,"module case=3 step=5 output=D_out expected=0 actual=%0d",D_out);
if (keep_mask_out !== 8'd17) $fatal(1,"module case=3 step=5 output=keep_mask_out expected=17 actual=%0d",keep_mask_out);
reset=1'd0;
valid_in=1'd1;
scores_in=72'd1386080816752464336091;
weights_in=128'd225323637317621340801391407492785874185;
values_in=64'd1717602057517805535;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=6 output=valid_out expected=1 actual=%0d",valid_out);
if (N_out !== 28'd600) $fatal(1,"module case=3 step=6 output=N_out expected=600 actual=%0d",N_out);
if (D_out !== 19'd200) $fatal(1,"module case=3 step=6 output=D_out expected=200 actual=%0d",D_out);
if (keep_mask_out !== 8'd10) $fatal(1,"module case=3 step=6 output=keep_mask_out expected=10 actual=%0d",keep_mask_out);
reset=1'd0;
valid_in=1'd1;
scores_in=72'd3217166507126298658634;
weights_in=128'd133370153580710099644062364362297359795;
values_in=64'd17618722244719778127;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=7 output=valid_out expected=1 actual=%0d",valid_out);
if (N_out !== 28'd251658496) $fatal(1,"module case=3 step=7 output=N_out expected=251658496 actual=%0d",N_out);
if (D_out !== 19'd131070) $fatal(1,"module case=3 step=7 output=D_out expected=131070 actual=%0d",D_out);
if (keep_mask_out !== 8'd17) $fatal(1,"module case=3 step=7 output=keep_mask_out expected=17 actual=%0d",keep_mask_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=8 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd1;
scores_in=72'd2060943562362716706306;
weights_in=128'd186264260839816408647488300986668489901;
values_in=64'd6557893407921752448;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=9 output=valid_out expected=1 actual=%0d",valid_out);
if (N_out !== 28'd253981867) $fatal(1,"module case=3 step=9 output=N_out expected=253981867 actual=%0d",N_out);
if (D_out !== 19'd174441) $fatal(1,"module case=3 step=9 output=D_out expected=174441 actual=%0d",D_out);
if (keep_mask_out !== 8'd133) $fatal(1,"module case=3 step=9 output=keep_mask_out expected=133 actual=%0d",keep_mask_out);
reset=1'd0;
valid_in=1'd1;
scores_in=72'd3560018283594261377227;
weights_in=128'd74303733760430963450444476902571597532;
values_in=64'd3575198171100520934;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=10 output=valid_out expected=1 actual=%0d",valid_out);
if (N_out !== 28'd2627707) $fatal(1,"module case=3 step=10 output=N_out expected=2627707 actual=%0d",N_out);
if (D_out !== 19'd149981) $fatal(1,"module case=3 step=10 output=D_out expected=149981 actual=%0d",D_out);
if (keep_mask_out !== 8'd131) $fatal(1,"module case=3 step=10 output=keep_mask_out expected=131 actual=%0d",keep_mask_out);
reset=1'd0;
valid_in=1'd1;
scores_in=72'd2081139943103823679618;
weights_in=128'd114338293569247375291287316758650324661;
values_in=64'd10549662629399854333;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=11 output=valid_out expected=1 actual=%0d",valid_out);
if (N_out !== 28'd263381883) $fatal(1,"module case=3 step=11 output=N_out expected=263381883 actual=%0d",N_out);
if (D_out !== 19'd68171) $fatal(1,"module case=3 step=11 output=D_out expected=68171 actual=%0d",D_out);
if (keep_mask_out !== 8'd76) $fatal(1,"module case=3 step=11 output=keep_mask_out expected=76 actual=%0d",keep_mask_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=12 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd1;
scores_in=72'd872440244337650762791;
weights_in=128'd325658187844897906898829496095350237744;
values_in=64'd7363428734141540959;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=13 output=valid_out expected=1 actual=%0d",valid_out);
if (N_out !== 28'd2016937) $fatal(1,"module case=3 step=13 output=N_out expected=2016937 actual=%0d",N_out);
if (D_out !== 19'd39851) $fatal(1,"module case=3 step=13 output=D_out expected=39851 actual=%0d",D_out);
if (keep_mask_out !== 8'd66) $fatal(1,"module case=3 step=13 output=keep_mask_out expected=66 actual=%0d",keep_mask_out);
reset=1'd0;
valid_in=1'd1;
scores_in=72'd4281747461095540889748;
weights_in=128'd151315618562600960486996424322765924420;
values_in=64'd2177403935143796794;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=14 output=valid_out expected=1 actual=%0d",valid_out);
if (N_out !== 28'd268118163) $fatal(1,"module case=3 step=14 output=N_out expected=268118163 actual=%0d",N_out);
if (D_out !== 19'd77201) $fatal(1,"module case=3 step=14 output=D_out expected=77201 actual=%0d",D_out);
if (keep_mask_out !== 8'd20) $fatal(1,"module case=3 step=14 output=keep_mask_out expected=20 actual=%0d",keep_mask_out);
reset=1'd0;
valid_in=1'd1;
scores_in=72'd3158102991311184397108;
weights_in=128'd290631415477676652337489445804254935783;
values_in=64'd1069128636030162772;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=15 output=valid_out expected=1 actual=%0d",valid_out);
if (N_out !== 28'd265933248) $fatal(1,"module case=3 step=15 output=N_out expected=265933248 actual=%0d",N_out);
if (D_out !== 19'd41995) $fatal(1,"module case=3 step=15 output=D_out expected=41995 actual=%0d",D_out);
if (keep_mask_out !== 8'd168) $fatal(1,"module case=3 step=15 output=keep_mask_out expected=168 actual=%0d",keep_mask_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=16 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd1;
scores_in=72'd3520752496865994021896;
weights_in=128'd165180745847703466466928313815273528020;
values_in=64'd14158636256359457377;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=17 output=valid_out expected=1 actual=%0d",valid_out);
if (N_out !== 28'd4309908) $fatal(1,"module case=3 step=17 output=N_out expected=4309908 actual=%0d",N_out);
if (D_out !== 19'd87277) $fatal(1,"module case=3 step=17 output=D_out expected=87277 actual=%0d",D_out);
if (keep_mask_out !== 8'd136) $fatal(1,"module case=3 step=17 output=keep_mask_out expected=136 actual=%0d",keep_mask_out);
reset=1'd0;
valid_in=1'd1;
scores_in=72'd4445389222298701627304;
weights_in=128'd32931121575128624150353897105136028644;
values_in=64'd5211573513435677716;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=18 output=valid_out expected=1 actual=%0d",valid_out);
if (N_out !== 28'd267731371) $fatal(1,"module case=3 step=18 output=N_out expected=267731371 actual=%0d",N_out);
if (D_out !== 19'd55191) $fatal(1,"module case=3 step=18 output=D_out expected=55191 actual=%0d",D_out);
if (keep_mask_out !== 8'd68) $fatal(1,"module case=3 step=18 output=keep_mask_out expected=68 actual=%0d",keep_mask_out);
reset=1'd0;
valid_in=1'd1;
scores_in=72'd442595275106363491093;
weights_in=128'd301781378092472059421121106935502603622;
values_in=64'd15984205495533249911;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=19 output=valid_out expected=1 actual=%0d",valid_out);
if (N_out !== 28'd265736851) $fatal(1,"module case=3 step=19 output=N_out expected=265736851 actual=%0d",N_out);
if (D_out !== 19'd48294) $fatal(1,"module case=3 step=19 output=D_out expected=48294 actual=%0d",D_out);
if (keep_mask_out !== 8'd66) $fatal(1,"module case=3 step=19 output=keep_mask_out expected=66 actual=%0d",keep_mask_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=20 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=21 output=valid_out expected=1 actual=%0d",valid_out);
if (N_out !== 28'd264033652) $fatal(1,"module case=3 step=21 output=N_out expected=264033652 actual=%0d",N_out);
if (D_out !== 19'd78022) $fatal(1,"module case=3 step=21 output=D_out expected=78022 actual=%0d",D_out);
if (keep_mask_out !== 8'd24) $fatal(1,"module case=3 step=21 output=keep_mask_out expected=24 actual=%0d",keep_mask_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=22 output=valid_out expected=1 actual=%0d",valid_out);
if (N_out !== 28'd4094973) $fatal(1,"module case=3 step=22 output=N_out expected=4094973 actual=%0d",N_out);
if (D_out !== 19'd97467) $fatal(1,"module case=3 step=22 output=D_out expected=97467 actual=%0d",D_out);
if (keep_mask_out !== 8'd70) $fatal(1,"module case=3 step=22 output=keep_mask_out expected=70 actual=%0d",keep_mask_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=23 output=valid_out expected=1 actual=%0d",valid_out);
if (N_out !== 28'd1159369) $fatal(1,"module case=3 step=23 output=N_out expected=1159369 actual=%0d",N_out);
if (D_out !== 19'd119365) $fatal(1,"module case=3 step=23 output=D_out expected=119365 actual=%0d",D_out);
if (keep_mask_out !== 8'd146) $fatal(1,"module case=3 step=23 output=keep_mask_out expected=146 actual=%0d",keep_mask_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=24 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=25 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd1;
valid_in=1'd0;
scores_in=72'd0;
weights_in=128'd0;
values_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=26 output=valid_out expected=0 actual=%0d",valid_out);
if (N_out !== 28'd0) $fatal(1,"module case=3 step=26 output=N_out expected=0 actual=%0d",N_out);
if (D_out !== 19'd0) $fatal(1,"module case=3 step=26 output=D_out expected=0 actual=%0d",D_out);
if (keep_mask_out !== 8'd0) $fatal(1,"module case=3 step=26 output=keep_mask_out expected=0 actual=%0d",keep_mask_out);
$display("FAST_CASE cycles=1");
$display("FAST_PASS cases=4");
$finish;
end
endmodule
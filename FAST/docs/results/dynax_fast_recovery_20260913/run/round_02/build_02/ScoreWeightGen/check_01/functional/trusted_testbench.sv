module FASTTestbench;
reg [0:0] clock;
reg [0:0] reset;
reg [0:0] start;
reg [7:0] q_in;
reg [63:0] k_in;
wire [71:0] scores_out;
wire [127:0] weights_out;
wire [0:0] valid_out;
ScoreWeightGen dut(.clock(clock),.reset(reset),.start(start),.q_in(q_in),.k_in(k_in),.scores_out(scores_out),.weights_out(weights_out),.valid_out(valid_out));
initial begin
clock=0;
reset=1'd1;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=0 output=valid_out expected=0 actual=%0d",valid_out);
if (scores_out !== 72'd0) $fatal(1,"module case=0 step=0 output=scores_out expected=0 actual=%0d",scores_out);
if (weights_out !== 128'd0) $fatal(1,"module case=0 step=0 output=weights_out expected=0 actual=%0d",weights_out);
reset=1'd0;
start=1'd1;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=1 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=2 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=0 step=3 output=valid_out expected=1 actual=%0d",valid_out);
if (scores_out !== 72'd0) $fatal(1,"module case=0 step=3 output=scores_out expected=0 actual=%0d",scores_out);
if (weights_out !== 128'd340282366920938463463374607431768211455) $fatal(1,"module case=0 step=3 output=weights_out expected=340282366920938463463374607431768211455 actual=%0d",weights_out);
reset=1'd0;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=4 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd1;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=0 step=5 output=valid_out expected=0 actual=%0d",valid_out);
if (scores_out !== 72'd0) $fatal(1,"module case=0 step=5 output=scores_out expected=0 actual=%0d",scores_out);
if (weights_out !== 128'd0) $fatal(1,"module case=0 step=5 output=weights_out expected=0 actual=%0d",weights_out);
$display("FAST_CASE cycles=1");
reset=1'd1;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=0 output=valid_out expected=0 actual=%0d",valid_out);
if (scores_out !== 72'd0) $fatal(1,"module case=1 step=0 output=scores_out expected=0 actual=%0d",scores_out);
if (weights_out !== 128'd0) $fatal(1,"module case=1 step=0 output=weights_out expected=0 actual=%0d",weights_out);
reset=1'd0;
start=1'd1;
q_in=8'd135;
k_in=64'd8608480567731124087;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=1 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=2 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=1 step=3 output=valid_out expected=1 actual=%0d",valid_out);
if (scores_out !== 72'd4666917952738103391225) $fatal(1,"module case=1 step=3 output=scores_out expected=4666917952738103391225 actual=%0d",scores_out);
if (weights_out !== 128'd340282366920938463463374607431768211455) $fatal(1,"module case=1 step=3 output=weights_out expected=340282366920938463463374607431768211455 actual=%0d",weights_out);
reset=1'd0;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=4 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd1;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=1 step=5 output=valid_out expected=0 actual=%0d",valid_out);
if (scores_out !== 72'd0) $fatal(1,"module case=1 step=5 output=scores_out expected=0 actual=%0d",scores_out);
if (weights_out !== 128'd0) $fatal(1,"module case=1 step=5 output=weights_out expected=0 actual=%0d",weights_out);
$display("FAST_CASE cycles=1");
reset=1'd1;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=0 output=valid_out expected=0 actual=%0d",valid_out);
if (scores_out !== 72'd0) $fatal(1,"module case=2 step=0 output=scores_out expected=0 actual=%0d",scores_out);
if (weights_out !== 128'd0) $fatal(1,"module case=2 step=0 output=weights_out expected=0 actual=%0d",weights_out);
reset=1'd0;
start=1'd1;
q_in=8'd33;
k_in=64'd63563607751104135;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=1 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=2 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=2 step=3 output=valid_out expected=1 actual=%0d",valid_out);
if (scores_out !== 72'd9187237411168973303) $fatal(1,"module case=2 step=3 output=scores_out expected=9187237411168973303 actual=%0d",scores_out);
if (weights_out !== 128'd340281479151852577984788328340808634845) $fatal(1,"module case=2 step=3 output=weights_out expected=340281479151852577984788328340808634845 actual=%0d",weights_out);
reset=1'd0;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=4 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd1;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=2 step=5 output=valid_out expected=0 actual=%0d",valid_out);
if (scores_out !== 72'd0) $fatal(1,"module case=2 step=5 output=scores_out expected=0 actual=%0d",scores_out);
if (weights_out !== 128'd0) $fatal(1,"module case=2 step=5 output=weights_out expected=0 actual=%0d",weights_out);
$display("FAST_CASE cycles=1");
reset=1'd1;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=0 output=valid_out expected=0 actual=%0d",valid_out);
if (scores_out !== 72'd0) $fatal(1,"module case=3 step=0 output=scores_out expected=0 actual=%0d",scores_out);
if (weights_out !== 128'd0) $fatal(1,"module case=3 step=0 output=weights_out expected=0 actual=%0d",weights_out);
reset=1'd0;
start=1'd1;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=1 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
start=1'd1;
q_in=8'd135;
k_in=64'd8608480567731124087;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=2 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
start=1'd1;
q_in=8'd33;
k_in=64'd63563607751104135;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=3 output=valid_out expected=1 actual=%0d",valid_out);
if (scores_out !== 72'd0) $fatal(1,"module case=3 step=3 output=scores_out expected=0 actual=%0d",scores_out);
if (weights_out !== 128'd340282366920938463463374607431768211455) $fatal(1,"module case=3 step=3 output=weights_out expected=340282366920938463463374607431768211455 actual=%0d",weights_out);
reset=1'd0;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=4 output=valid_out expected=1 actual=%0d",valid_out);
if (scores_out !== 72'd4666917952738103391225) $fatal(1,"module case=3 step=4 output=scores_out expected=4666917952738103391225 actual=%0d",scores_out);
if (weights_out !== 128'd340282366920938463463374607431768211455) $fatal(1,"module case=3 step=4 output=weights_out expected=340282366920938463463374607431768211455 actual=%0d",weights_out);
reset=1'd0;
start=1'd1;
q_in=8'd6;
k_in=64'd9872921485067753974;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=5 output=valid_out expected=1 actual=%0d",valid_out);
if (scores_out !== 72'd9187237411168973303) $fatal(1,"module case=3 step=5 output=scores_out expected=9187237411168973303 actual=%0d",scores_out);
if (weights_out !== 128'd340281479151852577984788328340808634845) $fatal(1,"module case=3 step=5 output=weights_out expected=340281479151852577984788328340808634845 actual=%0d",weights_out);
reset=1'd0;
start=1'd1;
q_in=8'd71;
k_in=64'd12214818854605046828;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=6 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
start=1'd1;
q_in=8'd69;
k_in=64'd9704267385038425620;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=7 output=valid_out expected=1 actual=%0d",valid_out);
if (scores_out !== 72'd4335325685101255961636) $fatal(1,"module case=3 step=7 output=scores_out expected=4335325685101255961636 actual=%0d",scores_out);
if (weights_out !== 128'd2597834088257536558232919435763843071) $fatal(1,"module case=3 step=7 output=weights_out expected=2597834088257536558232919435763843071 actual=%0d",weights_out);
reset=1'd0;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=8 output=valid_out expected=1 actual=%0d",valid_out);
if (scores_out !== 72'd4058103266969072982508) $fatal(1,"module case=3 step=8 output=scores_out expected=4058103266969072982508 actual=%0d",scores_out);
if (weights_out !== 128'd228627998399658244807023462075794608) $fatal(1,"module case=3 step=8 output=weights_out expected=228627998399658244807023462075794608 actual=%0d",weights_out);
reset=1'd0;
start=1'd1;
q_in=8'd104;
k_in=64'd10940422033893253440;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=9 output=valid_out expected=1 actual=%0d",valid_out);
if (scores_out !== 72'd4712350583475190877208) $fatal(1,"module case=3 step=9 output=scores_out expected=4712350583475190877208 actual=%0d",scores_out);
if (weights_out !== 128'd27929395709931647290298136030824393399) $fatal(1,"module case=3 step=9 output=weights_out expected=27929395709931647290298136030824393399 actual=%0d",weights_out);
reset=1'd0;
start=1'd1;
q_in=8'd60;
k_in=64'd7433038300836677450;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=10 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
start=1'd1;
q_in=8'd101;
k_in=64'd6093133167277354323;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=11 output=valid_out expected=1 actual=%0d",valid_out);
if (scores_out !== 72'd3826799413554146981912) $fatal(1,"module case=3 step=11 output=scores_out expected=3826799413554146981912 actual=%0d",scores_out);
if (weights_out !== 128'd129847083598332681728333325382174559) $fatal(1,"module case=3 step=11 output=weights_out expected=129847083598332681728333325382174559 actual=%0d",weights_out);
reset=1'd0;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=12 output=valid_out expected=1 actual=%0d",valid_out);
if (scores_out !== 72'd4638960027912492277796) $fatal(1,"module case=3 step=12 output=scores_out expected=4638960027912492277796 actual=%0d",scores_out);
if (weights_out !== 128'd19196059829788526210266269421065338879) $fatal(1,"module case=3 step=12 output=weights_out expected=19196059829788526210266269421065338879 actual=%0d",weights_out);
reset=1'd0;
start=1'd1;
q_in=8'd186;
k_in=64'd17618722244719778127;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=13 output=valid_out expected=1 actual=%0d",valid_out);
if (scores_out !== 72'd469454243779355056685) $fatal(1,"module case=3 step=13 output=scores_out expected=469454243779355056685 actual=%0d",scores_out);
if (weights_out !== 128'd248949871280323034839603854174838032646) $fatal(1,"module case=3 step=13 output=weights_out expected=248949871280323034839603854174838032646 actual=%0d",weights_out);
reset=1'd0;
start=1'd1;
q_in=8'd107;
k_in=64'd4001579002242687647;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=14 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
start=1'd1;
q_in=8'd30;
k_in=64'd6557893407921752448;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=15 output=valid_out expected=1 actual=%0d",valid_out);
if (scores_out !== 72'd4547642867459809647602) $fatal(1,"module case=3 step=15 output=scores_out expected=4547642867459809647602 actual=%0d",scores_out);
if (weights_out !== 128'd425890433009170674309145356735676528) $fatal(1,"module case=3 step=15 output=weights_out expected=425890433009170674309145356735676528 actual=%0d",weights_out);
reset=1'd0;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=16 output=valid_out expected=1 actual=%0d",valid_out);
if (scores_out !== 72'd4574648869603183179227) $fatal(1,"module case=3 step=16 output=scores_out expected=4574648869603183179227 actual=%0d",scores_out);
if (weights_out !== 128'd23158264140919992088939114184096810238) $fatal(1,"module case=3 step=16 output=weights_out expected=23158264140919992088939114184096810238 actual=%0d",weights_out);
reset=1'd0;
start=1'd1;
q_in=8'd104;
k_in=64'd6943577248329738020;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=17 output=valid_out expected=1 actual=%0d",valid_out);
if (scores_out !== 72'd147502000961878500856) $fatal(1,"module case=3 step=17 output=scores_out expected=147502000961878500856 actual=%0d",scores_out);
if (weights_out !== 128'd282098801165876489717295677373662835305) $fatal(1,"module case=3 step=17 output=weights_out expected=282098801165876489717295677373662835305 actual=%0d",weights_out);
reset=1'd0;
start=1'd1;
q_in=8'd44;
k_in=64'd13462770687058978335;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=18 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
start=1'd1;
q_in=8'd99;
k_in=64'd8893068527085053031;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=19 output=valid_out expected=1 actual=%0d",valid_out);
if (scores_out !== 72'd333158315311282473452) $fatal(1,"module case=3 step=19 output=scores_out expected=333158315311282473452 actual=%0d",scores_out);
if (weights_out !== 128'd67011783178666462086086043730199183750) $fatal(1,"module case=3 step=19 output=weights_out expected=67011783178666462086086043730199183750 actual=%0d",weights_out);
reset=1'd0;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=20 output=valid_out expected=1 actual=%0d",valid_out);
if (scores_out !== 72'd137882839650526812166) $fatal(1,"module case=3 step=20 output=scores_out expected=137882839650526812166 actual=%0d",scores_out);
if (weights_out !== 128'd233871728078559929622492571142887533239) $fatal(1,"module case=3 step=20 output=weights_out expected=233871728078559929622492571142887533239 actual=%0d",weights_out);
reset=1'd0;
start=1'd1;
q_in=8'd136;
k_in=64'd9838263505978427528;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=21 output=valid_out expected=1 actual=%0d",valid_out);
if (scores_out !== 72'd249372297257223217209) $fatal(1,"module case=3 step=21 output=scores_out expected=249372297257223217209 actual=%0d",scores_out);
if (weights_out !== 128'd52183037089078131632508134228318093311) $fatal(1,"module case=3 step=21 output=weights_out expected=52183037089078131632508134228318093311 actual=%0d",weights_out);
reset=1'd0;
start=1'd1;
q_in=8'd119;
k_in=64'd8608480567731124087;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=22 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
start=1'd1;
q_in=8'd136;
k_in=64'd8608480567731124087;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=23 output=valid_out expected=1 actual=%0d",valid_out);
if (scores_out !== 72'd1182901976139558879360) $fatal(1,"module case=3 step=23 output=scores_out expected=1182901976139558879360 actual=%0d",scores_out);
if (weights_out !== 128'd340282366920938463463374607431768211455) $fatal(1,"module case=3 step=23 output=weights_out expected=340282366920938463463374607431768211455 actual=%0d",weights_out);
reset=1'd0;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=24 output=valid_out expected=1 actual=%0d",valid_out);
if (scores_out !== 72'd905659325481849767010) $fatal(1,"module case=3 step=24 output=scores_out expected=905659325481849767010 actual=%0d",scores_out);
if (weights_out !== 128'd340282366920938463463374607431768211455) $fatal(1,"module case=3 step=24 output=weights_out expected=340282366920938463463374607431768211455 actual=%0d",weights_out);
reset=1'd0;
start=1'd1;
q_in=8'd119;
k_in=64'd9838263505978427528;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=25 output=valid_out expected=1 actual=%0d",valid_out);
if (scores_out !== 72'd3696568675436121498000) $fatal(1,"module case=3 step=25 output=scores_out expected=3696568675436121498000 actual=%0d",scores_out);
if (weights_out !== 128'd340282366920938463463374607431768211455) $fatal(1,"module case=3 step=25 output=weights_out expected=340282366920938463463374607431768211455 actual=%0d",weights_out);
reset=1'd0;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=26 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd0;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd1) $fatal(1,"module case=3 step=27 output=valid_out expected=1 actual=%0d",valid_out);
if (scores_out !== 72'd3696568675436121498000) $fatal(1,"module case=3 step=27 output=scores_out expected=3696568675436121498000 actual=%0d",scores_out);
if (weights_out !== 128'd340282366920938463463374607431768211455) $fatal(1,"module case=3 step=27 output=weights_out expected=340282366920938463463374607431768211455 actual=%0d",weights_out);
reset=1'd0;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=28 output=valid_out expected=0 actual=%0d",valid_out);
reset=1'd1;
start=1'd0;
q_in=8'd0;
k_in=64'd0;
#5;
repeat (1) begin clock=1; #5; clock=0; #5; end
if (valid_out !== 1'd0) $fatal(1,"module case=3 step=29 output=valid_out expected=0 actual=%0d",valid_out);
if (scores_out !== 72'd0) $fatal(1,"module case=3 step=29 output=scores_out expected=0 actual=%0d",scores_out);
if (weights_out !== 128'd0) $fatal(1,"module case=3 step=29 output=weights_out expected=0 actual=%0d",weights_out);
$display("FAST_CASE cycles=1");
$display("FAST_PASS cases=4");
$finish;
end
endmodule
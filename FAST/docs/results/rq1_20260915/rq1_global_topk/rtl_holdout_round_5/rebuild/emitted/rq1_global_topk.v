module ScoreCalculator(
  input  [7:0] q_in, // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ScoreCalculator.scala 5:16]
  input  [7:0] k_in, // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ScoreCalculator.scala 6:16]
  output [8:0] score_out // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ScoreCalculator.scala 7:21]
);
  wire [3:0] q0 = q_in[3:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ScoreCalculator.scala 11:23]
  wire [3:0] q1 = q_in[7:4]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ScoreCalculator.scala 12:23]
  wire [3:0] k0 = k_in[3:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ScoreCalculator.scala 13:23]
  wire [3:0] k1 = k_in[7:4]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ScoreCalculator.scala 14:23]
  wire [7:0] p0 = $signed(q0) * $signed(k0); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ScoreCalculator.scala 17:15]
  wire [7:0] p1 = $signed(q1) * $signed(k1); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ScoreCalculator.scala 18:15]
  assign score_out = $signed(p0) + $signed(p1); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ScoreCalculator.scala 23:18]
endmodule
module ExpLut(
  input  [7:0]  delta, // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 5:17]
  output [15:0] exp_val // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 6:19]
);
  wire [15:0] _GEN_1 = 8'h1 == delta ? 16'hf07c : 16'hffff; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_2 = 8'h2 == delta ? 16'he1ea : _GEN_1; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_3 = 8'h3 == delta ? 16'hd43a : _GEN_2; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_4 = 8'h4 == delta ? 16'hc75f : _GEN_3; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_5 = 8'h5 == delta ? 16'hbb4a : _GEN_4; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_6 = 8'h6 == delta ? 16'haff2 : _GEN_5; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_7 = 8'h7 == delta ? 16'ha549 : _GEN_6; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_8 = 8'h8 == delta ? 16'h9b45 : _GEN_7; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_9 = 8'h9 == delta ? 16'h91dd : _GEN_8; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_10 = 8'ha == delta ? 16'h8906 : _GEN_9; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_11 = 8'hb == delta ? 16'h80b9 : _GEN_10; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_12 = 8'hc == delta ? 16'h78ed : _GEN_11; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_13 = 8'hd == delta ? 16'h7199 : _GEN_12; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_14 = 8'he == delta ? 16'h6ab7 : _GEN_13; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_15 = 8'hf == delta ? 16'h6440 : _GEN_14; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_16 = 8'h10 == delta ? 16'h5e2d : _GEN_15; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_17 = 8'h11 == delta ? 16'h5878 : _GEN_16; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_18 = 8'h12 == delta ? 16'h531c : _GEN_17; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_19 = 8'h13 == delta ? 16'h4e13 : _GEN_18; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_20 = 8'h14 == delta ? 16'h4958 : _GEN_19; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_21 = 8'h15 == delta ? 16'h44e7 : _GEN_20; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_22 = 8'h16 == delta ? 16'h40ba : _GEN_21; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_23 = 8'h17 == delta ? 16'h3cce : _GEN_22; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_24 = 8'h18 == delta ? 16'h391f : _GEN_23; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_25 = 8'h19 == delta ? 16'h35a9 : _GEN_24; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_26 = 8'h1a == delta ? 16'h3269 : _GEN_25; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_27 = 8'h1b == delta ? 16'h2f5b : _GEN_26; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_28 = 8'h1c == delta ? 16'h2c7c : _GEN_27; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_29 = 8'h1d == delta ? 16'h29ca : _GEN_28; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_30 = 8'h1e == delta ? 16'h2742 : _GEN_29; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_31 = 8'h1f == delta ? 16'h24e1 : _GEN_30; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_32 = 8'h20 == delta ? 16'h22a5 : _GEN_31; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_33 = 8'h21 == delta ? 16'h208c : _GEN_32; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_34 = 8'h22 == delta ? 16'h1e93 : _GEN_33; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_35 = 8'h23 == delta ? 16'h1cb9 : _GEN_34; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_36 = 8'h24 == delta ? 16'h1afb : _GEN_35; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_37 = 8'h25 == delta ? 16'h1959 : _GEN_36; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_38 = 8'h26 == delta ? 16'h17d0 : _GEN_37; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_39 = 8'h27 == delta ? 16'h165e : _GEN_38; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_40 = 8'h28 == delta ? 16'h1503 : _GEN_39; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_41 = 8'h29 == delta ? 16'h13be : _GEN_40; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_42 = 8'h2a == delta ? 16'h128b : _GEN_41; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_43 = 8'h2b == delta ? 16'h116c : _GEN_42; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_44 = 8'h2c == delta ? 16'h105e : _GEN_43; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_45 = 8'h2d == delta ? 16'hf60 : _GEN_44; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_46 = 8'h2e == delta ? 16'he71 : _GEN_45; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_47 = 8'h2f == delta ? 16'hd91 : _GEN_46; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_48 = 8'h30 == delta ? 16'hcbf : _GEN_47; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_49 = 8'h31 == delta ? 16'hbf9 : _GEN_48; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_50 = 8'h32 == delta ? 16'hb3f : _GEN_49; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_51 = 8'h33 == delta ? 16'ha91 : _GEN_50; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_52 = 8'h34 == delta ? 16'h9ed : _GEN_51; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_53 = 8'h35 == delta ? 16'h953 : _GEN_52; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_54 = 8'h36 == delta ? 16'h8c2 : _GEN_53; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_55 = 8'h37 == delta ? 16'h83b : _GEN_54; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_56 = 8'h38 == delta ? 16'h7bb : _GEN_55; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_57 = 8'h39 == delta ? 16'h743 : _GEN_56; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_58 = 8'h3a == delta ? 16'h6d2 : _GEN_57; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_59 = 8'h3b == delta ? 16'h669 : _GEN_58; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_60 = 8'h3c == delta ? 16'h605 : _GEN_59; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_61 = 8'h3d == delta ? 16'h5a8 : _GEN_60; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_62 = 8'h3e == delta ? 16'h550 : _GEN_61; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_63 = 8'h3f == delta ? 16'h4fe : _GEN_62; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_64 = 8'h40 == delta ? 16'h4b0 : _GEN_63; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_65 = 8'h41 == delta ? 16'h468 : _GEN_64; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_66 = 8'h42 == delta ? 16'h423 : _GEN_65; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_67 = 8'h43 == delta ? 16'h3e3 : _GEN_66; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_68 = 8'h44 == delta ? 16'h3a7 : _GEN_67; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_69 = 8'h45 == delta ? 16'h36e : _GEN_68; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_70 = 8'h46 == delta ? 16'h339 : _GEN_69; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_71 = 8'h47 == delta ? 16'h307 : _GEN_70; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_72 = 8'h48 == delta ? 16'h2d8 : _GEN_71; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_73 = 8'h49 == delta ? 16'h2ac : _GEN_72; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_74 = 8'h4a == delta ? 16'h282 : _GEN_73; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_75 = 8'h4b == delta ? 16'h25c : _GEN_74; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_76 = 8'h4c == delta ? 16'h237 : _GEN_75; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_77 = 8'h4d == delta ? 16'h215 : _GEN_76; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_78 = 8'h4e == delta ? 16'h1f4 : _GEN_77; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_79 = 8'h4f == delta ? 16'h1d6 : _GEN_78; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_80 = 8'h50 == delta ? 16'h1ba : _GEN_79; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_81 = 8'h51 == delta ? 16'h19f : _GEN_80; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_82 = 8'h52 == delta ? 16'h186 : _GEN_81; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_83 = 8'h53 == delta ? 16'h16e : _GEN_82; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_84 = 8'h54 == delta ? 16'h158 : _GEN_83; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_85 = 8'h55 == delta ? 16'h143 : _GEN_84; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_86 = 8'h56 == delta ? 16'h12f : _GEN_85; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_87 = 8'h57 == delta ? 16'h11d : _GEN_86; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_88 = 8'h58 == delta ? 16'h10c : _GEN_87; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_89 = 8'h59 == delta ? 16'hfc : _GEN_88; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_90 = 8'h5a == delta ? 16'hec : _GEN_89; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_91 = 8'h5b == delta ? 16'hde : _GEN_90; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_92 = 8'h5c == delta ? 16'hd1 : _GEN_91; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_93 = 8'h5d == delta ? 16'hc4 : _GEN_92; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_94 = 8'h5e == delta ? 16'hb8 : _GEN_93; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_95 = 8'h5f == delta ? 16'had : _GEN_94; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_96 = 8'h60 == delta ? 16'ha2 : _GEN_95; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_97 = 8'h61 == delta ? 16'h99 : _GEN_96; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_98 = 8'h62 == delta ? 16'h8f : _GEN_97; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_99 = 8'h63 == delta ? 16'h87 : _GEN_98; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_100 = 8'h64 == delta ? 16'h7f : _GEN_99; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_101 = 8'h65 == delta ? 16'h77 : _GEN_100; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_102 = 8'h66 == delta ? 16'h70 : _GEN_101; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_103 = 8'h67 == delta ? 16'h69 : _GEN_102; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_104 = 8'h68 == delta ? 16'h63 : _GEN_103; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_105 = 8'h69 == delta ? 16'h5d : _GEN_104; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_106 = 8'h6a == delta ? 16'h57 : _GEN_105; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_107 = 8'h6b == delta ? 16'h52 : _GEN_106; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_108 = 8'h6c == delta ? 16'h4d : _GEN_107; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_109 = 8'h6d == delta ? 16'h48 : _GEN_108; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_110 = 8'h6e == delta ? 16'h44 : _GEN_109; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_111 = 8'h6f == delta ? 16'h40 : _GEN_110; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_112 = 8'h70 == delta ? 16'h3c : _GEN_111; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_113 = 8'h71 == delta ? 16'h38 : _GEN_112; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_114 = 8'h72 == delta ? 16'h35 : _GEN_113; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_115 = 8'h73 == delta ? 16'h32 : _GEN_114; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_116 = 8'h74 == delta ? 16'h2f : _GEN_115; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_117 = 8'h75 == delta ? 16'h2c : _GEN_116; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_118 = 8'h76 == delta ? 16'h29 : _GEN_117; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_119 = 8'h77 == delta ? 16'h27 : _GEN_118; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_120 = 8'h78 == delta ? 16'h24 : _GEN_119; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_121 = 8'h79 == delta ? 16'h22 : _GEN_120; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_122 = 8'h7a == delta ? 16'h20 : _GEN_121; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_123 = 8'h7b == delta ? 16'h1e : _GEN_122; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_124 = 8'h7c == delta ? 16'h1c : _GEN_123; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_125 = 8'h7d == delta ? 16'h1b : _GEN_124; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_126 = 8'h7e == delta ? 16'h19 : _GEN_125; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_127 = 8'h7f == delta ? 16'h17 : _GEN_126; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_128 = 8'h80 == delta ? 16'h16 : _GEN_127; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_129 = 8'h81 == delta ? 16'h15 : _GEN_128; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_130 = 8'h82 == delta ? 16'h13 : _GEN_129; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_131 = 8'h83 == delta ? 16'h12 : _GEN_130; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_132 = 8'h84 == delta ? 16'h11 : _GEN_131; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_133 = 8'h85 == delta ? 16'h10 : _GEN_132; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_134 = 8'h86 == delta ? 16'hf : _GEN_133; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_135 = 8'h87 == delta ? 16'he : _GEN_134; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_136 = 8'h88 == delta ? 16'hd : _GEN_135; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_137 = 8'h89 == delta ? 16'hd : _GEN_136; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_138 = 8'h8a == delta ? 16'hc : _GEN_137; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_139 = 8'h8b == delta ? 16'hb : _GEN_138; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_140 = 8'h8c == delta ? 16'ha : _GEN_139; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_141 = 8'h8d == delta ? 16'ha : _GEN_140; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_142 = 8'h8e == delta ? 16'h9 : _GEN_141; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_143 = 8'h8f == delta ? 16'h9 : _GEN_142; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_144 = 8'h90 == delta ? 16'h8 : _GEN_143; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_145 = 8'h91 == delta ? 16'h8 : _GEN_144; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_146 = 8'h92 == delta ? 16'h7 : _GEN_145; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_147 = 8'h93 == delta ? 16'h7 : _GEN_146; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_148 = 8'h94 == delta ? 16'h6 : _GEN_147; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_149 = 8'h95 == delta ? 16'h6 : _GEN_148; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_150 = 8'h96 == delta ? 16'h6 : _GEN_149; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_151 = 8'h97 == delta ? 16'h5 : _GEN_150; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_152 = 8'h98 == delta ? 16'h5 : _GEN_151; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_153 = 8'h99 == delta ? 16'h5 : _GEN_152; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_154 = 8'h9a == delta ? 16'h4 : _GEN_153; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_155 = 8'h9b == delta ? 16'h4 : _GEN_154; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_156 = 8'h9c == delta ? 16'h4 : _GEN_155; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_157 = 8'h9d == delta ? 16'h4 : _GEN_156; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_158 = 8'h9e == delta ? 16'h3 : _GEN_157; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_159 = 8'h9f == delta ? 16'h3 : _GEN_158; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_160 = 8'ha0 == delta ? 16'h3 : _GEN_159; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_161 = 8'ha1 == delta ? 16'h3 : _GEN_160; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_162 = 8'ha2 == delta ? 16'h3 : _GEN_161; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_163 = 8'ha3 == delta ? 16'h2 : _GEN_162; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_164 = 8'ha4 == delta ? 16'h2 : _GEN_163; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_165 = 8'ha5 == delta ? 16'h2 : _GEN_164; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_166 = 8'ha6 == delta ? 16'h2 : _GEN_165; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_167 = 8'ha7 == delta ? 16'h2 : _GEN_166; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_168 = 8'ha8 == delta ? 16'h2 : _GEN_167; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_169 = 8'ha9 == delta ? 16'h2 : _GEN_168; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_170 = 8'haa == delta ? 16'h2 : _GEN_169; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_171 = 8'hab == delta ? 16'h1 : _GEN_170; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_172 = 8'hac == delta ? 16'h1 : _GEN_171; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_173 = 8'had == delta ? 16'h1 : _GEN_172; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_174 = 8'hae == delta ? 16'h1 : _GEN_173; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_175 = 8'haf == delta ? 16'h1 : _GEN_174; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_176 = 8'hb0 == delta ? 16'h1 : _GEN_175; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_177 = 8'hb1 == delta ? 16'h1 : _GEN_176; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_178 = 8'hb2 == delta ? 16'h1 : _GEN_177; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_179 = 8'hb3 == delta ? 16'h1 : _GEN_178; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_180 = 8'hb4 == delta ? 16'h1 : _GEN_179; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_181 = 8'hb5 == delta ? 16'h1 : _GEN_180; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_182 = 8'hb6 == delta ? 16'h1 : _GEN_181; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_183 = 8'hb7 == delta ? 16'h1 : _GEN_182; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_184 = 8'hb8 == delta ? 16'h1 : _GEN_183; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_185 = 8'hb9 == delta ? 16'h1 : _GEN_184; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_186 = 8'hba == delta ? 16'h1 : _GEN_185; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_187 = 8'hbb == delta ? 16'h1 : _GEN_186; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_188 = 8'hbc == delta ? 16'h1 : _GEN_187; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_189 = 8'hbd == delta ? 16'h0 : _GEN_188; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_190 = 8'hbe == delta ? 16'h0 : _GEN_189; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_191 = 8'hbf == delta ? 16'h0 : _GEN_190; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_192 = 8'hc0 == delta ? 16'h0 : _GEN_191; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_193 = 8'hc1 == delta ? 16'h0 : _GEN_192; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_194 = 8'hc2 == delta ? 16'h0 : _GEN_193; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_195 = 8'hc3 == delta ? 16'h0 : _GEN_194; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_196 = 8'hc4 == delta ? 16'h0 : _GEN_195; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_197 = 8'hc5 == delta ? 16'h0 : _GEN_196; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_198 = 8'hc6 == delta ? 16'h0 : _GEN_197; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_199 = 8'hc7 == delta ? 16'h0 : _GEN_198; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_200 = 8'hc8 == delta ? 16'h0 : _GEN_199; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_201 = 8'hc9 == delta ? 16'h0 : _GEN_200; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_202 = 8'hca == delta ? 16'h0 : _GEN_201; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_203 = 8'hcb == delta ? 16'h0 : _GEN_202; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_204 = 8'hcc == delta ? 16'h0 : _GEN_203; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_205 = 8'hcd == delta ? 16'h0 : _GEN_204; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_206 = 8'hce == delta ? 16'h0 : _GEN_205; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_207 = 8'hcf == delta ? 16'h0 : _GEN_206; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_208 = 8'hd0 == delta ? 16'h0 : _GEN_207; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_209 = 8'hd1 == delta ? 16'h0 : _GEN_208; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_210 = 8'hd2 == delta ? 16'h0 : _GEN_209; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_211 = 8'hd3 == delta ? 16'h0 : _GEN_210; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_212 = 8'hd4 == delta ? 16'h0 : _GEN_211; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_213 = 8'hd5 == delta ? 16'h0 : _GEN_212; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_214 = 8'hd6 == delta ? 16'h0 : _GEN_213; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_215 = 8'hd7 == delta ? 16'h0 : _GEN_214; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_216 = 8'hd8 == delta ? 16'h0 : _GEN_215; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_217 = 8'hd9 == delta ? 16'h0 : _GEN_216; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_218 = 8'hda == delta ? 16'h0 : _GEN_217; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_219 = 8'hdb == delta ? 16'h0 : _GEN_218; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_220 = 8'hdc == delta ? 16'h0 : _GEN_219; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_221 = 8'hdd == delta ? 16'h0 : _GEN_220; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_222 = 8'hde == delta ? 16'h0 : _GEN_221; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_223 = 8'hdf == delta ? 16'h0 : _GEN_222; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_224 = 8'he0 == delta ? 16'h0 : _GEN_223; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_225 = 8'he1 == delta ? 16'h0 : _GEN_224; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_226 = 8'he2 == delta ? 16'h0 : _GEN_225; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_227 = 8'he3 == delta ? 16'h0 : _GEN_226; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_228 = 8'he4 == delta ? 16'h0 : _GEN_227; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_229 = 8'he5 == delta ? 16'h0 : _GEN_228; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_230 = 8'he6 == delta ? 16'h0 : _GEN_229; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_231 = 8'he7 == delta ? 16'h0 : _GEN_230; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_232 = 8'he8 == delta ? 16'h0 : _GEN_231; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_233 = 8'he9 == delta ? 16'h0 : _GEN_232; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_234 = 8'hea == delta ? 16'h0 : _GEN_233; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_235 = 8'heb == delta ? 16'h0 : _GEN_234; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_236 = 8'hec == delta ? 16'h0 : _GEN_235; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_237 = 8'hed == delta ? 16'h0 : _GEN_236; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_238 = 8'hee == delta ? 16'h0 : _GEN_237; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_239 = 8'hef == delta ? 16'h0 : _GEN_238; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_240 = 8'hf0 == delta ? 16'h0 : _GEN_239; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_241 = 8'hf1 == delta ? 16'h0 : _GEN_240; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_242 = 8'hf2 == delta ? 16'h0 : _GEN_241; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_243 = 8'hf3 == delta ? 16'h0 : _GEN_242; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_244 = 8'hf4 == delta ? 16'h0 : _GEN_243; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_245 = 8'hf5 == delta ? 16'h0 : _GEN_244; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_246 = 8'hf6 == delta ? 16'h0 : _GEN_245; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_247 = 8'hf7 == delta ? 16'h0 : _GEN_246; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_248 = 8'hf8 == delta ? 16'h0 : _GEN_247; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_249 = 8'hf9 == delta ? 16'h0 : _GEN_248; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_250 = 8'hfa == delta ? 16'h0 : _GEN_249; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_251 = 8'hfb == delta ? 16'h0 : _GEN_250; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_252 = 8'hfc == delta ? 16'h0 : _GEN_251; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_253 = 8'hfd == delta ? 16'h0 : _GEN_252; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  wire [15:0] _GEN_254 = 8'hfe == delta ? 16'h0 : _GEN_253; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
  assign exp_val = 8'hff == delta ? 16'h0 : _GEN_254; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/ExpLut.scala 43:{11,11}]
endmodule
module FinalDivider(
  input         clock, // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 5:17]
  input         reset, // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 6:17]
  input         valid_in, // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 7:20]
  input  [27:0] numer, // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 8:17]
  input  [19:0] denom, // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 9:17]
  output [15:0] quotient, // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 10:20]
  output        valid_out // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 11:21]
);
`ifdef RANDOMIZE_REG_INIT
  reg [31:0] _RAND_0;
  reg [31:0] _RAND_1;
  reg [31:0] _RAND_2;
  reg [31:0] _RAND_3;
  reg [31:0] _RAND_4;
  reg [31:0] _RAND_5;
  reg [31:0] _RAND_6;
  reg [31:0] _RAND_7;
  reg [31:0] _RAND_8;
  reg [31:0] _RAND_9;
  reg [31:0] _RAND_10;
  reg [31:0] _RAND_11;
  reg [31:0] _RAND_12;
  reg [31:0] _RAND_13;
  reg [31:0] _RAND_14;
  reg [31:0] _RAND_15;
  reg [31:0] _RAND_16;
  reg [31:0] _RAND_17;
  reg [31:0] _RAND_18;
  reg [31:0] _RAND_19;
  reg [31:0] _RAND_20;
  reg [31:0] _RAND_21;
  reg [31:0] _RAND_22;
  reg [31:0] _RAND_23;
  reg [31:0] _RAND_24;
  reg [31:0] _RAND_25;
  reg [31:0] _RAND_26;
  reg [31:0] _RAND_27;
  reg [31:0] _RAND_28;
  reg [31:0] _RAND_29;
  reg [31:0] _RAND_30;
  reg [31:0] _RAND_31;
  reg [31:0] _RAND_32;
  reg [31:0] _RAND_33;
  reg [31:0] _RAND_34;
  reg [31:0] _RAND_35;
  reg [31:0] _RAND_36;
  reg [31:0] _RAND_37;
  reg [31:0] _RAND_38;
  reg [31:0] _RAND_39;
  reg [31:0] _RAND_40;
  reg [31:0] _RAND_41;
  reg [31:0] _RAND_42;
  reg [31:0] _RAND_43;
  reg [31:0] _RAND_44;
  reg [31:0] _RAND_45;
  reg [31:0] _RAND_46;
  reg [31:0] _RAND_47;
  reg [31:0] _RAND_48;
  reg [31:0] _RAND_49;
  reg [31:0] _RAND_50;
  reg [31:0] _RAND_51;
  reg [31:0] _RAND_52;
  reg [31:0] _RAND_53;
  reg [31:0] _RAND_54;
  reg [31:0] _RAND_55;
  reg [31:0] _RAND_56;
  reg [31:0] _RAND_57;
  reg [31:0] _RAND_58;
  reg [31:0] _RAND_59;
  reg [31:0] _RAND_60;
  reg [31:0] _RAND_61;
  reg [31:0] _RAND_62;
  reg [31:0] _RAND_63;
  reg [31:0] _RAND_64;
  reg [31:0] _RAND_65;
  reg [31:0] _RAND_66;
  reg [31:0] _RAND_67;
  reg [31:0] _RAND_68;
  reg [31:0] _RAND_69;
  reg [31:0] _RAND_70;
  reg [31:0] _RAND_71;
  reg [31:0] _RAND_72;
  reg [31:0] _RAND_73;
  reg [31:0] _RAND_74;
  reg [31:0] _RAND_75;
  reg [31:0] _RAND_76;
  reg [31:0] _RAND_77;
  reg [31:0] _RAND_78;
  reg [31:0] _RAND_79;
  reg [31:0] _RAND_80;
  reg [31:0] _RAND_81;
  reg [31:0] _RAND_82;
  reg [31:0] _RAND_83;
  reg [31:0] _RAND_84;
  reg [31:0] _RAND_85;
  reg [31:0] _RAND_86;
  reg [31:0] _RAND_87;
  reg [31:0] _RAND_88;
  reg [31:0] _RAND_89;
  reg [31:0] _RAND_90;
  reg [31:0] _RAND_91;
  reg [31:0] _RAND_92;
  reg [31:0] _RAND_93;
  reg [31:0] _RAND_94;
  reg [31:0] _RAND_95;
  reg [31:0] _RAND_96;
  reg [31:0] _RAND_97;
  reg [31:0] _RAND_98;
  reg [31:0] _RAND_99;
  reg [31:0] _RAND_100;
  reg [31:0] _RAND_101;
  reg [31:0] _RAND_102;
  reg [31:0] _RAND_103;
  reg [31:0] _RAND_104;
  reg [31:0] _RAND_105;
  reg [31:0] _RAND_106;
  reg [31:0] _RAND_107;
  reg [31:0] _RAND_108;
  reg [31:0] _RAND_109;
  reg [31:0] _RAND_110;
  reg [31:0] _RAND_111;
  reg [31:0] _RAND_112;
  reg [31:0] _RAND_113;
  reg [31:0] _RAND_114;
  reg [31:0] _RAND_115;
  reg [31:0] _RAND_116;
  reg [31:0] _RAND_117;
  reg [31:0] _RAND_118;
  reg [31:0] _RAND_119;
  reg [31:0] _RAND_120;
  reg [31:0] _RAND_121;
  reg [31:0] _RAND_122;
`endif // RANDOMIZE_REG_INIT
  wire [31:0] dividend_sint = {$signed(numer), 4'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 64:34]
  wire [31:0] _dividend_abs_T_3 = 32'sh0 - $signed(dividend_sint); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 65:36]
  wire [31:0] dividend_abs = $signed(dividend_sint) < 32'sh0 ? $signed(_dividend_abs_T_3) : $signed(dividend_sint); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 65:40]
  wire  result_sign = $signed(numer) < 28'sh0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 67:32]
  wire  is_zero_denom = denom == 20'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 68:29]
  wire [20:0] final_state_state_after_steps_shifted_rem = {20'h0,dividend_abs[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire [20:0] _GEN_0 = {{1'd0}, denom}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire  final_state_state_after_steps_can_subtract = final_state_state_after_steps_shifted_rem >= _GEN_0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub = final_state_state_after_steps_shifted_rem - _GEN_0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [20:0] final_state_state_after_steps_next_remainder = final_state_state_after_steps_can_subtract ?
    final_state_state_after_steps_trial_sub : final_state_state_after_steps_shifted_rem; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
  wire [31:0] final_state_state_after_steps_next_quotient = {31'h0,final_state_state_after_steps_can_subtract}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T = {dividend_abs, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  wire [31:0] final_state_state_after_steps_next_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [20:0] final_state_state_after_steps_shifted_rem_1 = {final_state_state_after_steps_next_remainder[19:0],
    final_state_state_after_steps_next_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire  final_state_state_after_steps_can_subtract_1 = final_state_state_after_steps_shifted_rem_1 >= _GEN_0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_1 = final_state_state_after_steps_shifted_rem_1 - _GEN_0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [31:0] final_state_state_after_steps_quotient = {final_state_state_after_steps_next_quotient[30:0],
    final_state_state_after_steps_can_subtract_1}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_1 = {
    final_state_state_after_steps_next_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  reg [20:0] final_state_REG_remainder; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [19:0] final_state_REG_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  wire [20:0] final_state_state_after_steps_shifted_rem_2 = {final_state_REG_remainder[19:0],
    final_state_REG_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire [20:0] _GEN_4 = {{1'd0}, final_state_REG_divisor}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire  final_state_state_after_steps_can_subtract_2 = final_state_state_after_steps_shifted_rem_2 >= _GEN_4; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_2 = final_state_state_after_steps_shifted_rem_2 - _GEN_4; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [20:0] final_state_state_after_steps_next_1_remainder = final_state_state_after_steps_can_subtract_2 ?
    final_state_state_after_steps_trial_sub_2 : final_state_state_after_steps_shifted_rem_2; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
  wire [31:0] final_state_state_after_steps_next_1_quotient = {final_state_REG_quotient[30:0],
    final_state_state_after_steps_can_subtract_2}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_2 = {final_state_REG_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  wire [31:0] final_state_state_after_steps_next_1_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_2[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [20:0] final_state_state_after_steps_shifted_rem_3 = {final_state_state_after_steps_next_1_remainder[19:0],
    final_state_state_after_steps_next_1_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire  final_state_state_after_steps_can_subtract_3 = final_state_state_after_steps_shifted_rem_3 >= _GEN_4; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_3 = final_state_state_after_steps_shifted_rem_3 - _GEN_4; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [31:0] final_state_state_after_steps_1_quotient = {final_state_state_after_steps_next_1_quotient[30:0],
    final_state_state_after_steps_can_subtract_3}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_3 = {
    final_state_state_after_steps_next_1_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  reg [20:0] final_state_REG_1_remainder; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_1_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_1_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [19:0] final_state_REG_1_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_1_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_1_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_1_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  wire [20:0] final_state_state_after_steps_shifted_rem_4 = {final_state_REG_1_remainder[19:0],
    final_state_REG_1_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire [20:0] _GEN_8 = {{1'd0}, final_state_REG_1_divisor}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire  final_state_state_after_steps_can_subtract_4 = final_state_state_after_steps_shifted_rem_4 >= _GEN_8; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_4 = final_state_state_after_steps_shifted_rem_4 - _GEN_8; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [20:0] final_state_state_after_steps_next_2_remainder = final_state_state_after_steps_can_subtract_4 ?
    final_state_state_after_steps_trial_sub_4 : final_state_state_after_steps_shifted_rem_4; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
  wire [31:0] final_state_state_after_steps_next_2_quotient = {final_state_REG_1_quotient[30:0],
    final_state_state_after_steps_can_subtract_4}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_4 = {final_state_REG_1_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  wire [31:0] final_state_state_after_steps_next_2_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_4[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [20:0] final_state_state_after_steps_shifted_rem_5 = {final_state_state_after_steps_next_2_remainder[19:0],
    final_state_state_after_steps_next_2_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire  final_state_state_after_steps_can_subtract_5 = final_state_state_after_steps_shifted_rem_5 >= _GEN_8; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_5 = final_state_state_after_steps_shifted_rem_5 - _GEN_8; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [31:0] final_state_state_after_steps_2_quotient = {final_state_state_after_steps_next_2_quotient[30:0],
    final_state_state_after_steps_can_subtract_5}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_5 = {
    final_state_state_after_steps_next_2_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  reg [20:0] final_state_REG_2_remainder; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_2_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_2_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [19:0] final_state_REG_2_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_2_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_2_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_2_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  wire [20:0] final_state_state_after_steps_shifted_rem_6 = {final_state_REG_2_remainder[19:0],
    final_state_REG_2_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire [20:0] _GEN_12 = {{1'd0}, final_state_REG_2_divisor}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire  final_state_state_after_steps_can_subtract_6 = final_state_state_after_steps_shifted_rem_6 >= _GEN_12; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_6 = final_state_state_after_steps_shifted_rem_6 - _GEN_12; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [20:0] final_state_state_after_steps_next_3_remainder = final_state_state_after_steps_can_subtract_6 ?
    final_state_state_after_steps_trial_sub_6 : final_state_state_after_steps_shifted_rem_6; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
  wire [31:0] final_state_state_after_steps_next_3_quotient = {final_state_REG_2_quotient[30:0],
    final_state_state_after_steps_can_subtract_6}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_6 = {final_state_REG_2_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  wire [31:0] final_state_state_after_steps_next_3_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_6[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [20:0] final_state_state_after_steps_shifted_rem_7 = {final_state_state_after_steps_next_3_remainder[19:0],
    final_state_state_after_steps_next_3_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire  final_state_state_after_steps_can_subtract_7 = final_state_state_after_steps_shifted_rem_7 >= _GEN_12; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_7 = final_state_state_after_steps_shifted_rem_7 - _GEN_12; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [31:0] final_state_state_after_steps_3_quotient = {final_state_state_after_steps_next_3_quotient[30:0],
    final_state_state_after_steps_can_subtract_7}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_7 = {
    final_state_state_after_steps_next_3_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  reg [20:0] final_state_REG_3_remainder; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_3_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_3_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [19:0] final_state_REG_3_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_3_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_3_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_3_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  wire [20:0] final_state_state_after_steps_shifted_rem_8 = {final_state_REG_3_remainder[19:0],
    final_state_REG_3_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire [20:0] _GEN_16 = {{1'd0}, final_state_REG_3_divisor}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire  final_state_state_after_steps_can_subtract_8 = final_state_state_after_steps_shifted_rem_8 >= _GEN_16; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_8 = final_state_state_after_steps_shifted_rem_8 - _GEN_16; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [20:0] final_state_state_after_steps_next_4_remainder = final_state_state_after_steps_can_subtract_8 ?
    final_state_state_after_steps_trial_sub_8 : final_state_state_after_steps_shifted_rem_8; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
  wire [31:0] final_state_state_after_steps_next_4_quotient = {final_state_REG_3_quotient[30:0],
    final_state_state_after_steps_can_subtract_8}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_8 = {final_state_REG_3_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  wire [31:0] final_state_state_after_steps_next_4_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_8[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [20:0] final_state_state_after_steps_shifted_rem_9 = {final_state_state_after_steps_next_4_remainder[19:0],
    final_state_state_after_steps_next_4_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire  final_state_state_after_steps_can_subtract_9 = final_state_state_after_steps_shifted_rem_9 >= _GEN_16; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_9 = final_state_state_after_steps_shifted_rem_9 - _GEN_16; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [31:0] final_state_state_after_steps_4_quotient = {final_state_state_after_steps_next_4_quotient[30:0],
    final_state_state_after_steps_can_subtract_9}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_9 = {
    final_state_state_after_steps_next_4_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  reg [20:0] final_state_REG_4_remainder; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_4_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_4_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [19:0] final_state_REG_4_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_4_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_4_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_4_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  wire [20:0] final_state_state_after_steps_shifted_rem_10 = {final_state_REG_4_remainder[19:0],
    final_state_REG_4_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire [20:0] _GEN_20 = {{1'd0}, final_state_REG_4_divisor}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire  final_state_state_after_steps_can_subtract_10 = final_state_state_after_steps_shifted_rem_10 >= _GEN_20; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_10 = final_state_state_after_steps_shifted_rem_10 - _GEN_20; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [20:0] final_state_state_after_steps_next_5_remainder = final_state_state_after_steps_can_subtract_10 ?
    final_state_state_after_steps_trial_sub_10 : final_state_state_after_steps_shifted_rem_10; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
  wire [31:0] final_state_state_after_steps_next_5_quotient = {final_state_REG_4_quotient[30:0],
    final_state_state_after_steps_can_subtract_10}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_10 = {final_state_REG_4_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  wire [31:0] final_state_state_after_steps_next_5_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_10[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [20:0] final_state_state_after_steps_shifted_rem_11 = {final_state_state_after_steps_next_5_remainder[19:0],
    final_state_state_after_steps_next_5_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire  final_state_state_after_steps_can_subtract_11 = final_state_state_after_steps_shifted_rem_11 >= _GEN_20; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_11 = final_state_state_after_steps_shifted_rem_11 - _GEN_20; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [31:0] final_state_state_after_steps_5_quotient = {final_state_state_after_steps_next_5_quotient[30:0],
    final_state_state_after_steps_can_subtract_11}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_11 = {
    final_state_state_after_steps_next_5_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  reg [20:0] final_state_REG_5_remainder; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_5_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_5_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [19:0] final_state_REG_5_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_5_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_5_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_5_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  wire [20:0] final_state_state_after_steps_shifted_rem_12 = {final_state_REG_5_remainder[19:0],
    final_state_REG_5_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire [20:0] _GEN_24 = {{1'd0}, final_state_REG_5_divisor}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire  final_state_state_after_steps_can_subtract_12 = final_state_state_after_steps_shifted_rem_12 >= _GEN_24; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_12 = final_state_state_after_steps_shifted_rem_12 - _GEN_24; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [20:0] final_state_state_after_steps_next_6_remainder = final_state_state_after_steps_can_subtract_12 ?
    final_state_state_after_steps_trial_sub_12 : final_state_state_after_steps_shifted_rem_12; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
  wire [31:0] final_state_state_after_steps_next_6_quotient = {final_state_REG_5_quotient[30:0],
    final_state_state_after_steps_can_subtract_12}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_12 = {final_state_REG_5_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  wire [31:0] final_state_state_after_steps_next_6_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_12[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [20:0] final_state_state_after_steps_shifted_rem_13 = {final_state_state_after_steps_next_6_remainder[19:0],
    final_state_state_after_steps_next_6_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire  final_state_state_after_steps_can_subtract_13 = final_state_state_after_steps_shifted_rem_13 >= _GEN_24; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_13 = final_state_state_after_steps_shifted_rem_13 - _GEN_24; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [31:0] final_state_state_after_steps_6_quotient = {final_state_state_after_steps_next_6_quotient[30:0],
    final_state_state_after_steps_can_subtract_13}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_13 = {
    final_state_state_after_steps_next_6_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  reg [20:0] final_state_REG_6_remainder; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_6_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_6_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [19:0] final_state_REG_6_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_6_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_6_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_6_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  wire [20:0] final_state_state_after_steps_shifted_rem_14 = {final_state_REG_6_remainder[19:0],
    final_state_REG_6_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire [20:0] _GEN_28 = {{1'd0}, final_state_REG_6_divisor}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire  final_state_state_after_steps_can_subtract_14 = final_state_state_after_steps_shifted_rem_14 >= _GEN_28; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_14 = final_state_state_after_steps_shifted_rem_14 - _GEN_28; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [20:0] final_state_state_after_steps_next_7_remainder = final_state_state_after_steps_can_subtract_14 ?
    final_state_state_after_steps_trial_sub_14 : final_state_state_after_steps_shifted_rem_14; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
  wire [31:0] final_state_state_after_steps_next_7_quotient = {final_state_REG_6_quotient[30:0],
    final_state_state_after_steps_can_subtract_14}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_14 = {final_state_REG_6_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  wire [31:0] final_state_state_after_steps_next_7_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_14[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [20:0] final_state_state_after_steps_shifted_rem_15 = {final_state_state_after_steps_next_7_remainder[19:0],
    final_state_state_after_steps_next_7_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire  final_state_state_after_steps_can_subtract_15 = final_state_state_after_steps_shifted_rem_15 >= _GEN_28; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_15 = final_state_state_after_steps_shifted_rem_15 - _GEN_28; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [31:0] final_state_state_after_steps_7_quotient = {final_state_state_after_steps_next_7_quotient[30:0],
    final_state_state_after_steps_can_subtract_15}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_15 = {
    final_state_state_after_steps_next_7_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  reg [20:0] final_state_REG_7_remainder; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_7_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_7_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [19:0] final_state_REG_7_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_7_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_7_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_7_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  wire [20:0] final_state_state_after_steps_shifted_rem_16 = {final_state_REG_7_remainder[19:0],
    final_state_REG_7_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire [20:0] _GEN_32 = {{1'd0}, final_state_REG_7_divisor}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire  final_state_state_after_steps_can_subtract_16 = final_state_state_after_steps_shifted_rem_16 >= _GEN_32; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_16 = final_state_state_after_steps_shifted_rem_16 - _GEN_32; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [20:0] final_state_state_after_steps_next_8_remainder = final_state_state_after_steps_can_subtract_16 ?
    final_state_state_after_steps_trial_sub_16 : final_state_state_after_steps_shifted_rem_16; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
  wire [31:0] final_state_state_after_steps_next_8_quotient = {final_state_REG_7_quotient[30:0],
    final_state_state_after_steps_can_subtract_16}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_16 = {final_state_REG_7_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  wire [31:0] final_state_state_after_steps_next_8_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_16[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [20:0] final_state_state_after_steps_shifted_rem_17 = {final_state_state_after_steps_next_8_remainder[19:0],
    final_state_state_after_steps_next_8_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire  final_state_state_after_steps_can_subtract_17 = final_state_state_after_steps_shifted_rem_17 >= _GEN_32; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_17 = final_state_state_after_steps_shifted_rem_17 - _GEN_32; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [31:0] final_state_state_after_steps_8_quotient = {final_state_state_after_steps_next_8_quotient[30:0],
    final_state_state_after_steps_can_subtract_17}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_17 = {
    final_state_state_after_steps_next_8_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  reg [20:0] final_state_REG_8_remainder; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_8_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_8_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [19:0] final_state_REG_8_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_8_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_8_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_8_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  wire [20:0] final_state_state_after_steps_shifted_rem_18 = {final_state_REG_8_remainder[19:0],
    final_state_REG_8_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire [20:0] _GEN_36 = {{1'd0}, final_state_REG_8_divisor}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire  final_state_state_after_steps_can_subtract_18 = final_state_state_after_steps_shifted_rem_18 >= _GEN_36; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_18 = final_state_state_after_steps_shifted_rem_18 - _GEN_36; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [20:0] final_state_state_after_steps_next_9_remainder = final_state_state_after_steps_can_subtract_18 ?
    final_state_state_after_steps_trial_sub_18 : final_state_state_after_steps_shifted_rem_18; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
  wire [31:0] final_state_state_after_steps_next_9_quotient = {final_state_REG_8_quotient[30:0],
    final_state_state_after_steps_can_subtract_18}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_18 = {final_state_REG_8_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  wire [31:0] final_state_state_after_steps_next_9_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_18[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [20:0] final_state_state_after_steps_shifted_rem_19 = {final_state_state_after_steps_next_9_remainder[19:0],
    final_state_state_after_steps_next_9_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire  final_state_state_after_steps_can_subtract_19 = final_state_state_after_steps_shifted_rem_19 >= _GEN_36; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_19 = final_state_state_after_steps_shifted_rem_19 - _GEN_36; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [31:0] final_state_state_after_steps_9_quotient = {final_state_state_after_steps_next_9_quotient[30:0],
    final_state_state_after_steps_can_subtract_19}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_19 = {
    final_state_state_after_steps_next_9_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  reg [20:0] final_state_REG_9_remainder; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_9_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_9_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [19:0] final_state_REG_9_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_9_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_9_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_9_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  wire [20:0] final_state_state_after_steps_shifted_rem_20 = {final_state_REG_9_remainder[19:0],
    final_state_REG_9_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire [20:0] _GEN_40 = {{1'd0}, final_state_REG_9_divisor}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire  final_state_state_after_steps_can_subtract_20 = final_state_state_after_steps_shifted_rem_20 >= _GEN_40; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_20 = final_state_state_after_steps_shifted_rem_20 - _GEN_40; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [20:0] final_state_state_after_steps_next_10_remainder = final_state_state_after_steps_can_subtract_20 ?
    final_state_state_after_steps_trial_sub_20 : final_state_state_after_steps_shifted_rem_20; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
  wire [31:0] final_state_state_after_steps_next_10_quotient = {final_state_REG_9_quotient[30:0],
    final_state_state_after_steps_can_subtract_20}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_20 = {final_state_REG_9_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  wire [31:0] final_state_state_after_steps_next_10_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_20[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [20:0] final_state_state_after_steps_shifted_rem_21 = {final_state_state_after_steps_next_10_remainder[19:0],
    final_state_state_after_steps_next_10_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire  final_state_state_after_steps_can_subtract_21 = final_state_state_after_steps_shifted_rem_21 >= _GEN_40; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_21 = final_state_state_after_steps_shifted_rem_21 - _GEN_40; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [31:0] final_state_state_after_steps_10_quotient = {final_state_state_after_steps_next_10_quotient[30:0],
    final_state_state_after_steps_can_subtract_21}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_21 = {
    final_state_state_after_steps_next_10_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  reg [20:0] final_state_REG_10_remainder; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_10_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_10_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [19:0] final_state_REG_10_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_10_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_10_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_10_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  wire [20:0] final_state_state_after_steps_shifted_rem_22 = {final_state_REG_10_remainder[19:0],
    final_state_REG_10_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire [20:0] _GEN_44 = {{1'd0}, final_state_REG_10_divisor}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire  final_state_state_after_steps_can_subtract_22 = final_state_state_after_steps_shifted_rem_22 >= _GEN_44; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_22 = final_state_state_after_steps_shifted_rem_22 - _GEN_44; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [20:0] final_state_state_after_steps_next_11_remainder = final_state_state_after_steps_can_subtract_22 ?
    final_state_state_after_steps_trial_sub_22 : final_state_state_after_steps_shifted_rem_22; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
  wire [31:0] final_state_state_after_steps_next_11_quotient = {final_state_REG_10_quotient[30:0],
    final_state_state_after_steps_can_subtract_22}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_22 = {final_state_REG_10_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  wire [31:0] final_state_state_after_steps_next_11_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_22[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [20:0] final_state_state_after_steps_shifted_rem_23 = {final_state_state_after_steps_next_11_remainder[19:0],
    final_state_state_after_steps_next_11_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire  final_state_state_after_steps_can_subtract_23 = final_state_state_after_steps_shifted_rem_23 >= _GEN_44; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_23 = final_state_state_after_steps_shifted_rem_23 - _GEN_44; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [31:0] final_state_state_after_steps_11_quotient = {final_state_state_after_steps_next_11_quotient[30:0],
    final_state_state_after_steps_can_subtract_23}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_23 = {
    final_state_state_after_steps_next_11_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  reg [20:0] final_state_REG_11_remainder; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_11_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_11_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [19:0] final_state_REG_11_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_11_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_11_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_11_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  wire [20:0] final_state_state_after_steps_shifted_rem_24 = {final_state_REG_11_remainder[19:0],
    final_state_REG_11_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire [20:0] _GEN_48 = {{1'd0}, final_state_REG_11_divisor}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire  final_state_state_after_steps_can_subtract_24 = final_state_state_after_steps_shifted_rem_24 >= _GEN_48; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_24 = final_state_state_after_steps_shifted_rem_24 - _GEN_48; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [20:0] final_state_state_after_steps_next_12_remainder = final_state_state_after_steps_can_subtract_24 ?
    final_state_state_after_steps_trial_sub_24 : final_state_state_after_steps_shifted_rem_24; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
  wire [31:0] final_state_state_after_steps_next_12_quotient = {final_state_REG_11_quotient[30:0],
    final_state_state_after_steps_can_subtract_24}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_24 = {final_state_REG_11_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  wire [31:0] final_state_state_after_steps_next_12_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_24[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [20:0] final_state_state_after_steps_shifted_rem_25 = {final_state_state_after_steps_next_12_remainder[19:0],
    final_state_state_after_steps_next_12_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire  final_state_state_after_steps_can_subtract_25 = final_state_state_after_steps_shifted_rem_25 >= _GEN_48; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_25 = final_state_state_after_steps_shifted_rem_25 - _GEN_48; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [31:0] final_state_state_after_steps_12_quotient = {final_state_state_after_steps_next_12_quotient[30:0],
    final_state_state_after_steps_can_subtract_25}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_25 = {
    final_state_state_after_steps_next_12_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  reg [20:0] final_state_REG_12_remainder; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_12_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_12_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [19:0] final_state_REG_12_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_12_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_12_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_12_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  wire [20:0] final_state_state_after_steps_shifted_rem_26 = {final_state_REG_12_remainder[19:0],
    final_state_REG_12_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire [20:0] _GEN_52 = {{1'd0}, final_state_REG_12_divisor}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire  final_state_state_after_steps_can_subtract_26 = final_state_state_after_steps_shifted_rem_26 >= _GEN_52; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_26 = final_state_state_after_steps_shifted_rem_26 - _GEN_52; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [20:0] final_state_state_after_steps_next_13_remainder = final_state_state_after_steps_can_subtract_26 ?
    final_state_state_after_steps_trial_sub_26 : final_state_state_after_steps_shifted_rem_26; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
  wire [31:0] final_state_state_after_steps_next_13_quotient = {final_state_REG_12_quotient[30:0],
    final_state_state_after_steps_can_subtract_26}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_26 = {final_state_REG_12_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  wire [31:0] final_state_state_after_steps_next_13_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_26[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [20:0] final_state_state_after_steps_shifted_rem_27 = {final_state_state_after_steps_next_13_remainder[19:0],
    final_state_state_after_steps_next_13_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire  final_state_state_after_steps_can_subtract_27 = final_state_state_after_steps_shifted_rem_27 >= _GEN_52; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_27 = final_state_state_after_steps_shifted_rem_27 - _GEN_52; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [31:0] final_state_state_after_steps_13_quotient = {final_state_state_after_steps_next_13_quotient[30:0],
    final_state_state_after_steps_can_subtract_27}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_27 = {
    final_state_state_after_steps_next_13_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  reg [20:0] final_state_REG_13_remainder; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_13_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_13_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [19:0] final_state_REG_13_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_13_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_13_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_13_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  wire [20:0] final_state_state_after_steps_shifted_rem_28 = {final_state_REG_13_remainder[19:0],
    final_state_REG_13_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire [20:0] _GEN_56 = {{1'd0}, final_state_REG_13_divisor}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire  final_state_state_after_steps_can_subtract_28 = final_state_state_after_steps_shifted_rem_28 >= _GEN_56; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_28 = final_state_state_after_steps_shifted_rem_28 - _GEN_56; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [31:0] final_state_state_after_steps_14_quotient = {final_state_REG_13_quotient[30:0],
    final_state_state_after_steps_can_subtract_28}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_28 = {final_state_REG_13_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  reg [20:0] final_state_REG_14_remainder; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_14_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_14_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [19:0] final_state_REG_14_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_14_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_14_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_14_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  wire [20:0] final_state_state_after_steps_shifted_rem_29 = {final_state_REG_14_remainder[19:0],
    final_state_REG_14_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire [20:0] _GEN_58 = {{1'd0}, final_state_REG_14_divisor}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire  final_state_state_after_steps_can_subtract_29 = final_state_state_after_steps_shifted_rem_29 >= _GEN_58; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_29 = final_state_state_after_steps_shifted_rem_29 - _GEN_58; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [31:0] final_state_state_after_steps_15_quotient = {final_state_REG_14_quotient[30:0],
    final_state_state_after_steps_can_subtract_29}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_29 = {final_state_REG_14_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  reg [20:0] final_state_REG_15_remainder; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_15_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_15_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [19:0] final_state_REG_15_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_15_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_15_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_15_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  wire [20:0] final_state_state_after_steps_shifted_rem_30 = {final_state_REG_15_remainder[19:0],
    final_state_REG_15_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire [20:0] _GEN_60 = {{1'd0}, final_state_REG_15_divisor}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire  final_state_state_after_steps_can_subtract_30 = final_state_state_after_steps_shifted_rem_30 >= _GEN_60; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [20:0] final_state_state_after_steps_trial_sub_30 = final_state_state_after_steps_shifted_rem_30 - _GEN_60; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 43:33]
  wire [31:0] final_state_state_after_steps_16_quotient = {final_state_REG_15_quotient[30:0],
    final_state_state_after_steps_can_subtract_30}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  wire [32:0] _final_state_state_after_steps_next_dividend_shifted_T_30 = {final_state_REG_15_dividend_shifted, 1'h0}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 50:53]
  reg [20:0] final_state_REG_16_remainder; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_16_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [31:0] final_state_REG_16_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg [19:0] final_state_REG_16_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_16_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_16_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_REG_16_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  wire [20:0] final_state_state_after_steps_shifted_rem_31 = {final_state_REG_16_remainder[19:0],
    final_state_REG_16_dividend_shifted[31]}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 39:26]
  wire [20:0] _GEN_62 = {{1'd0}, final_state_REG_16_divisor}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire  final_state_state_after_steps_can_subtract_31 = final_state_state_after_steps_shifted_rem_31 >= _GEN_62; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 42:36]
  wire [31:0] final_state_state_after_steps_17_quotient = {final_state_REG_16_quotient[30:0],
    final_state_state_after_steps_can_subtract_31}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 47:25]
  reg [31:0] final_state_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  reg  final_state_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
  wire [31:0] _signed_quotient_T_3 = 32'sh0 - $signed(final_state_quotient); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 102:51]
  wire [31:0] signed_quotient = final_state_negative ? $signed(_signed_quotient_T_3) : $signed(final_state_quotient); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 102:28]
  wire [31:0] _quotient_T = final_state_divideByZero ? $signed(32'sh0) : $signed(signed_quotient); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 108:22]
  wire [31:0] final_state_state_after_steps_dividend_shifted = _final_state_state_after_steps_next_dividend_shifted_T_1[
    31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [31:0] final_state_state_after_steps_1_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_3[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [31:0] final_state_state_after_steps_2_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_5[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [31:0] final_state_state_after_steps_3_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_7[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [31:0] final_state_state_after_steps_4_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_9[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [31:0] final_state_state_after_steps_5_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_11[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [31:0] final_state_state_after_steps_6_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_13[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [31:0] final_state_state_after_steps_7_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_15[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [31:0] final_state_state_after_steps_8_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_17[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [31:0] final_state_state_after_steps_9_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_19[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [31:0] final_state_state_after_steps_10_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_21[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [31:0] final_state_state_after_steps_11_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_23[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [31:0] final_state_state_after_steps_12_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_25[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [31:0] final_state_state_after_steps_13_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_27[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [31:0] final_state_state_after_steps_14_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_28[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [31:0] final_state_state_after_steps_15_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_29[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  wire [31:0] final_state_state_after_steps_16_dividend_shifted =
    _final_state_state_after_steps_next_dividend_shifted_T_30[31:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 36:20 50:27]
  assign quotient = _quotient_T[15:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 108:28]
  assign valid_out = final_state_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 109:13]
  always @(posedge clock) begin
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_remainder <= 21'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else if (final_state_state_after_steps_can_subtract_1) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
      final_state_REG_remainder <= final_state_state_after_steps_trial_sub_1;
    end else begin
      final_state_REG_remainder <= final_state_state_after_steps_shifted_rem_1;
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_quotient <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_quotient <= final_state_state_after_steps_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_dividend_shifted <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_dividend_shifted <= final_state_state_after_steps_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_divisor <= 20'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_divisor <= denom; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_negative <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_negative <= result_sign; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_divideByZero <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_divideByZero <= is_zero_denom; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_valid <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_valid <= valid_in; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_1_remainder <= 21'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else if (final_state_state_after_steps_can_subtract_3) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
      final_state_REG_1_remainder <= final_state_state_after_steps_trial_sub_3;
    end else begin
      final_state_REG_1_remainder <= final_state_state_after_steps_shifted_rem_3;
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_1_quotient <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_1_quotient <= final_state_state_after_steps_1_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_1_dividend_shifted <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_1_dividend_shifted <= final_state_state_after_steps_1_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_1_divisor <= 20'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_1_divisor <= final_state_REG_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_1_negative <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_1_negative <= final_state_REG_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_1_divideByZero <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_1_divideByZero <= final_state_REG_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_1_valid <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_1_valid <= final_state_REG_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_2_remainder <= 21'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else if (final_state_state_after_steps_can_subtract_5) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
      final_state_REG_2_remainder <= final_state_state_after_steps_trial_sub_5;
    end else begin
      final_state_REG_2_remainder <= final_state_state_after_steps_shifted_rem_5;
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_2_quotient <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_2_quotient <= final_state_state_after_steps_2_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_2_dividend_shifted <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_2_dividend_shifted <= final_state_state_after_steps_2_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_2_divisor <= 20'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_2_divisor <= final_state_REG_1_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_2_negative <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_2_negative <= final_state_REG_1_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_2_divideByZero <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_2_divideByZero <= final_state_REG_1_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_2_valid <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_2_valid <= final_state_REG_1_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_3_remainder <= 21'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else if (final_state_state_after_steps_can_subtract_7) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
      final_state_REG_3_remainder <= final_state_state_after_steps_trial_sub_7;
    end else begin
      final_state_REG_3_remainder <= final_state_state_after_steps_shifted_rem_7;
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_3_quotient <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_3_quotient <= final_state_state_after_steps_3_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_3_dividend_shifted <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_3_dividend_shifted <= final_state_state_after_steps_3_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_3_divisor <= 20'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_3_divisor <= final_state_REG_2_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_3_negative <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_3_negative <= final_state_REG_2_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_3_divideByZero <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_3_divideByZero <= final_state_REG_2_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_3_valid <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_3_valid <= final_state_REG_2_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_4_remainder <= 21'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else if (final_state_state_after_steps_can_subtract_9) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
      final_state_REG_4_remainder <= final_state_state_after_steps_trial_sub_9;
    end else begin
      final_state_REG_4_remainder <= final_state_state_after_steps_shifted_rem_9;
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_4_quotient <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_4_quotient <= final_state_state_after_steps_4_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_4_dividend_shifted <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_4_dividend_shifted <= final_state_state_after_steps_4_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_4_divisor <= 20'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_4_divisor <= final_state_REG_3_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_4_negative <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_4_negative <= final_state_REG_3_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_4_divideByZero <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_4_divideByZero <= final_state_REG_3_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_4_valid <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_4_valid <= final_state_REG_3_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_5_remainder <= 21'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else if (final_state_state_after_steps_can_subtract_11) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
      final_state_REG_5_remainder <= final_state_state_after_steps_trial_sub_11;
    end else begin
      final_state_REG_5_remainder <= final_state_state_after_steps_shifted_rem_11;
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_5_quotient <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_5_quotient <= final_state_state_after_steps_5_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_5_dividend_shifted <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_5_dividend_shifted <= final_state_state_after_steps_5_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_5_divisor <= 20'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_5_divisor <= final_state_REG_4_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_5_negative <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_5_negative <= final_state_REG_4_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_5_divideByZero <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_5_divideByZero <= final_state_REG_4_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_5_valid <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_5_valid <= final_state_REG_4_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_6_remainder <= 21'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else if (final_state_state_after_steps_can_subtract_13) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
      final_state_REG_6_remainder <= final_state_state_after_steps_trial_sub_13;
    end else begin
      final_state_REG_6_remainder <= final_state_state_after_steps_shifted_rem_13;
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_6_quotient <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_6_quotient <= final_state_state_after_steps_6_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_6_dividend_shifted <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_6_dividend_shifted <= final_state_state_after_steps_6_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_6_divisor <= 20'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_6_divisor <= final_state_REG_5_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_6_negative <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_6_negative <= final_state_REG_5_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_6_divideByZero <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_6_divideByZero <= final_state_REG_5_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_6_valid <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_6_valid <= final_state_REG_5_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_7_remainder <= 21'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else if (final_state_state_after_steps_can_subtract_15) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
      final_state_REG_7_remainder <= final_state_state_after_steps_trial_sub_15;
    end else begin
      final_state_REG_7_remainder <= final_state_state_after_steps_shifted_rem_15;
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_7_quotient <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_7_quotient <= final_state_state_after_steps_7_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_7_dividend_shifted <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_7_dividend_shifted <= final_state_state_after_steps_7_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_7_divisor <= 20'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_7_divisor <= final_state_REG_6_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_7_negative <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_7_negative <= final_state_REG_6_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_7_divideByZero <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_7_divideByZero <= final_state_REG_6_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_7_valid <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_7_valid <= final_state_REG_6_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_8_remainder <= 21'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else if (final_state_state_after_steps_can_subtract_17) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
      final_state_REG_8_remainder <= final_state_state_after_steps_trial_sub_17;
    end else begin
      final_state_REG_8_remainder <= final_state_state_after_steps_shifted_rem_17;
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_8_quotient <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_8_quotient <= final_state_state_after_steps_8_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_8_dividend_shifted <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_8_dividend_shifted <= final_state_state_after_steps_8_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_8_divisor <= 20'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_8_divisor <= final_state_REG_7_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_8_negative <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_8_negative <= final_state_REG_7_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_8_divideByZero <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_8_divideByZero <= final_state_REG_7_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_8_valid <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_8_valid <= final_state_REG_7_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_9_remainder <= 21'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else if (final_state_state_after_steps_can_subtract_19) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
      final_state_REG_9_remainder <= final_state_state_after_steps_trial_sub_19;
    end else begin
      final_state_REG_9_remainder <= final_state_state_after_steps_shifted_rem_19;
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_9_quotient <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_9_quotient <= final_state_state_after_steps_9_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_9_dividend_shifted <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_9_dividend_shifted <= final_state_state_after_steps_9_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_9_divisor <= 20'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_9_divisor <= final_state_REG_8_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_9_negative <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_9_negative <= final_state_REG_8_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_9_divideByZero <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_9_divideByZero <= final_state_REG_8_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_9_valid <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_9_valid <= final_state_REG_8_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_10_remainder <= 21'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else if (final_state_state_after_steps_can_subtract_21) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
      final_state_REG_10_remainder <= final_state_state_after_steps_trial_sub_21;
    end else begin
      final_state_REG_10_remainder <= final_state_state_after_steps_shifted_rem_21;
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_10_quotient <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_10_quotient <= final_state_state_after_steps_10_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_10_dividend_shifted <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_10_dividend_shifted <= final_state_state_after_steps_10_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_10_divisor <= 20'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_10_divisor <= final_state_REG_9_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_10_negative <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_10_negative <= final_state_REG_9_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_10_divideByZero <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_10_divideByZero <= final_state_REG_9_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_10_valid <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_10_valid <= final_state_REG_9_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_11_remainder <= 21'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else if (final_state_state_after_steps_can_subtract_23) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
      final_state_REG_11_remainder <= final_state_state_after_steps_trial_sub_23;
    end else begin
      final_state_REG_11_remainder <= final_state_state_after_steps_shifted_rem_23;
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_11_quotient <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_11_quotient <= final_state_state_after_steps_11_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_11_dividend_shifted <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_11_dividend_shifted <= final_state_state_after_steps_11_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_11_divisor <= 20'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_11_divisor <= final_state_REG_10_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_11_negative <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_11_negative <= final_state_REG_10_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_11_divideByZero <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_11_divideByZero <= final_state_REG_10_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_11_valid <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_11_valid <= final_state_REG_10_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_12_remainder <= 21'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else if (final_state_state_after_steps_can_subtract_25) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
      final_state_REG_12_remainder <= final_state_state_after_steps_trial_sub_25;
    end else begin
      final_state_REG_12_remainder <= final_state_state_after_steps_shifted_rem_25;
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_12_quotient <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_12_quotient <= final_state_state_after_steps_12_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_12_dividend_shifted <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_12_dividend_shifted <= final_state_state_after_steps_12_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_12_divisor <= 20'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_12_divisor <= final_state_REG_11_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_12_negative <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_12_negative <= final_state_REG_11_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_12_divideByZero <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_12_divideByZero <= final_state_REG_11_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_12_valid <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_12_valid <= final_state_REG_11_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_13_remainder <= 21'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else if (final_state_state_after_steps_can_subtract_27) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
      final_state_REG_13_remainder <= final_state_state_after_steps_trial_sub_27;
    end else begin
      final_state_REG_13_remainder <= final_state_state_after_steps_shifted_rem_27;
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_13_quotient <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_13_quotient <= final_state_state_after_steps_13_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_13_dividend_shifted <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_13_dividend_shifted <= final_state_state_after_steps_13_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_13_divisor <= 20'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_13_divisor <= final_state_REG_12_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_13_negative <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_13_negative <= final_state_REG_12_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_13_divideByZero <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_13_divideByZero <= final_state_REG_12_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_13_valid <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_13_valid <= final_state_REG_12_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_14_remainder <= 21'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else if (final_state_state_after_steps_can_subtract_28) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
      final_state_REG_14_remainder <= final_state_state_after_steps_trial_sub_28;
    end else begin
      final_state_REG_14_remainder <= final_state_state_after_steps_shifted_rem_28;
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_14_quotient <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_14_quotient <= final_state_state_after_steps_14_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_14_dividend_shifted <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_14_dividend_shifted <= final_state_state_after_steps_14_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_14_divisor <= 20'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_14_divisor <= final_state_REG_13_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_14_negative <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_14_negative <= final_state_REG_13_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_14_divideByZero <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_14_divideByZero <= final_state_REG_13_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_14_valid <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_14_valid <= final_state_REG_13_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_15_remainder <= 21'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else if (final_state_state_after_steps_can_subtract_29) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
      final_state_REG_15_remainder <= final_state_state_after_steps_trial_sub_29;
    end else begin
      final_state_REG_15_remainder <= final_state_state_after_steps_shifted_rem_29;
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_15_quotient <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_15_quotient <= final_state_state_after_steps_15_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_15_dividend_shifted <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_15_dividend_shifted <= final_state_state_after_steps_15_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_15_divisor <= 20'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_15_divisor <= final_state_REG_14_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_15_negative <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_15_negative <= final_state_REG_14_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_15_divideByZero <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_15_divideByZero <= final_state_REG_14_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_15_valid <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_15_valid <= final_state_REG_14_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_16_remainder <= 21'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else if (final_state_state_after_steps_can_subtract_30) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 46:26]
      final_state_REG_16_remainder <= final_state_state_after_steps_trial_sub_30;
    end else begin
      final_state_REG_16_remainder <= final_state_state_after_steps_shifted_rem_30;
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_16_quotient <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_16_quotient <= final_state_state_after_steps_16_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_16_dividend_shifted <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_16_dividend_shifted <= final_state_state_after_steps_16_dividend_shifted; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_16_divisor <= 20'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_16_divisor <= final_state_REG_15_divisor; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_16_negative <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_16_negative <= final_state_REG_15_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_16_divideByZero <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_16_divideByZero <= final_state_REG_15_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_REG_16_valid <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_REG_16_valid <= final_state_REG_15_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_quotient <= 32'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_quotient <= final_state_state_after_steps_17_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_negative <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_negative <= final_state_REG_16_negative; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_divideByZero <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_divideByZero <= final_state_REG_16_divideByZero; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
      final_state_valid <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end else begin
      final_state_valid <= final_state_REG_16_valid; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/FinalDivider.scala 95:14]
    end
  end
// Register and memory initialization
`ifdef RANDOMIZE_GARBAGE_ASSIGN
`define RANDOMIZE
`endif
`ifdef RANDOMIZE_INVALID_ASSIGN
`define RANDOMIZE
`endif
`ifdef RANDOMIZE_REG_INIT
`define RANDOMIZE
`endif
`ifdef RANDOMIZE_MEM_INIT
`define RANDOMIZE
`endif
`ifndef RANDOM
`define RANDOM $random
`endif
`ifdef RANDOMIZE_MEM_INIT
  integer initvar;
`endif
`ifndef SYNTHESIS
`ifdef FIRRTL_BEFORE_INITIAL
`FIRRTL_BEFORE_INITIAL
`endif
initial begin
  `ifdef RANDOMIZE
    `ifdef INIT_RANDOM
      `INIT_RANDOM
    `endif
    `ifndef VERILATOR
      `ifdef RANDOMIZE_DELAY
        #`RANDOMIZE_DELAY begin end
      `else
        #0.002 begin end
      `endif
    `endif
`ifdef RANDOMIZE_REG_INIT
  _RAND_0 = {1{`RANDOM}};
  final_state_REG_remainder = _RAND_0[20:0];
  _RAND_1 = {1{`RANDOM}};
  final_state_REG_quotient = _RAND_1[31:0];
  _RAND_2 = {1{`RANDOM}};
  final_state_REG_dividend_shifted = _RAND_2[31:0];
  _RAND_3 = {1{`RANDOM}};
  final_state_REG_divisor = _RAND_3[19:0];
  _RAND_4 = {1{`RANDOM}};
  final_state_REG_negative = _RAND_4[0:0];
  _RAND_5 = {1{`RANDOM}};
  final_state_REG_divideByZero = _RAND_5[0:0];
  _RAND_6 = {1{`RANDOM}};
  final_state_REG_valid = _RAND_6[0:0];
  _RAND_7 = {1{`RANDOM}};
  final_state_REG_1_remainder = _RAND_7[20:0];
  _RAND_8 = {1{`RANDOM}};
  final_state_REG_1_quotient = _RAND_8[31:0];
  _RAND_9 = {1{`RANDOM}};
  final_state_REG_1_dividend_shifted = _RAND_9[31:0];
  _RAND_10 = {1{`RANDOM}};
  final_state_REG_1_divisor = _RAND_10[19:0];
  _RAND_11 = {1{`RANDOM}};
  final_state_REG_1_negative = _RAND_11[0:0];
  _RAND_12 = {1{`RANDOM}};
  final_state_REG_1_divideByZero = _RAND_12[0:0];
  _RAND_13 = {1{`RANDOM}};
  final_state_REG_1_valid = _RAND_13[0:0];
  _RAND_14 = {1{`RANDOM}};
  final_state_REG_2_remainder = _RAND_14[20:0];
  _RAND_15 = {1{`RANDOM}};
  final_state_REG_2_quotient = _RAND_15[31:0];
  _RAND_16 = {1{`RANDOM}};
  final_state_REG_2_dividend_shifted = _RAND_16[31:0];
  _RAND_17 = {1{`RANDOM}};
  final_state_REG_2_divisor = _RAND_17[19:0];
  _RAND_18 = {1{`RANDOM}};
  final_state_REG_2_negative = _RAND_18[0:0];
  _RAND_19 = {1{`RANDOM}};
  final_state_REG_2_divideByZero = _RAND_19[0:0];
  _RAND_20 = {1{`RANDOM}};
  final_state_REG_2_valid = _RAND_20[0:0];
  _RAND_21 = {1{`RANDOM}};
  final_state_REG_3_remainder = _RAND_21[20:0];
  _RAND_22 = {1{`RANDOM}};
  final_state_REG_3_quotient = _RAND_22[31:0];
  _RAND_23 = {1{`RANDOM}};
  final_state_REG_3_dividend_shifted = _RAND_23[31:0];
  _RAND_24 = {1{`RANDOM}};
  final_state_REG_3_divisor = _RAND_24[19:0];
  _RAND_25 = {1{`RANDOM}};
  final_state_REG_3_negative = _RAND_25[0:0];
  _RAND_26 = {1{`RANDOM}};
  final_state_REG_3_divideByZero = _RAND_26[0:0];
  _RAND_27 = {1{`RANDOM}};
  final_state_REG_3_valid = _RAND_27[0:0];
  _RAND_28 = {1{`RANDOM}};
  final_state_REG_4_remainder = _RAND_28[20:0];
  _RAND_29 = {1{`RANDOM}};
  final_state_REG_4_quotient = _RAND_29[31:0];
  _RAND_30 = {1{`RANDOM}};
  final_state_REG_4_dividend_shifted = _RAND_30[31:0];
  _RAND_31 = {1{`RANDOM}};
  final_state_REG_4_divisor = _RAND_31[19:0];
  _RAND_32 = {1{`RANDOM}};
  final_state_REG_4_negative = _RAND_32[0:0];
  _RAND_33 = {1{`RANDOM}};
  final_state_REG_4_divideByZero = _RAND_33[0:0];
  _RAND_34 = {1{`RANDOM}};
  final_state_REG_4_valid = _RAND_34[0:0];
  _RAND_35 = {1{`RANDOM}};
  final_state_REG_5_remainder = _RAND_35[20:0];
  _RAND_36 = {1{`RANDOM}};
  final_state_REG_5_quotient = _RAND_36[31:0];
  _RAND_37 = {1{`RANDOM}};
  final_state_REG_5_dividend_shifted = _RAND_37[31:0];
  _RAND_38 = {1{`RANDOM}};
  final_state_REG_5_divisor = _RAND_38[19:0];
  _RAND_39 = {1{`RANDOM}};
  final_state_REG_5_negative = _RAND_39[0:0];
  _RAND_40 = {1{`RANDOM}};
  final_state_REG_5_divideByZero = _RAND_40[0:0];
  _RAND_41 = {1{`RANDOM}};
  final_state_REG_5_valid = _RAND_41[0:0];
  _RAND_42 = {1{`RANDOM}};
  final_state_REG_6_remainder = _RAND_42[20:0];
  _RAND_43 = {1{`RANDOM}};
  final_state_REG_6_quotient = _RAND_43[31:0];
  _RAND_44 = {1{`RANDOM}};
  final_state_REG_6_dividend_shifted = _RAND_44[31:0];
  _RAND_45 = {1{`RANDOM}};
  final_state_REG_6_divisor = _RAND_45[19:0];
  _RAND_46 = {1{`RANDOM}};
  final_state_REG_6_negative = _RAND_46[0:0];
  _RAND_47 = {1{`RANDOM}};
  final_state_REG_6_divideByZero = _RAND_47[0:0];
  _RAND_48 = {1{`RANDOM}};
  final_state_REG_6_valid = _RAND_48[0:0];
  _RAND_49 = {1{`RANDOM}};
  final_state_REG_7_remainder = _RAND_49[20:0];
  _RAND_50 = {1{`RANDOM}};
  final_state_REG_7_quotient = _RAND_50[31:0];
  _RAND_51 = {1{`RANDOM}};
  final_state_REG_7_dividend_shifted = _RAND_51[31:0];
  _RAND_52 = {1{`RANDOM}};
  final_state_REG_7_divisor = _RAND_52[19:0];
  _RAND_53 = {1{`RANDOM}};
  final_state_REG_7_negative = _RAND_53[0:0];
  _RAND_54 = {1{`RANDOM}};
  final_state_REG_7_divideByZero = _RAND_54[0:0];
  _RAND_55 = {1{`RANDOM}};
  final_state_REG_7_valid = _RAND_55[0:0];
  _RAND_56 = {1{`RANDOM}};
  final_state_REG_8_remainder = _RAND_56[20:0];
  _RAND_57 = {1{`RANDOM}};
  final_state_REG_8_quotient = _RAND_57[31:0];
  _RAND_58 = {1{`RANDOM}};
  final_state_REG_8_dividend_shifted = _RAND_58[31:0];
  _RAND_59 = {1{`RANDOM}};
  final_state_REG_8_divisor = _RAND_59[19:0];
  _RAND_60 = {1{`RANDOM}};
  final_state_REG_8_negative = _RAND_60[0:0];
  _RAND_61 = {1{`RANDOM}};
  final_state_REG_8_divideByZero = _RAND_61[0:0];
  _RAND_62 = {1{`RANDOM}};
  final_state_REG_8_valid = _RAND_62[0:0];
  _RAND_63 = {1{`RANDOM}};
  final_state_REG_9_remainder = _RAND_63[20:0];
  _RAND_64 = {1{`RANDOM}};
  final_state_REG_9_quotient = _RAND_64[31:0];
  _RAND_65 = {1{`RANDOM}};
  final_state_REG_9_dividend_shifted = _RAND_65[31:0];
  _RAND_66 = {1{`RANDOM}};
  final_state_REG_9_divisor = _RAND_66[19:0];
  _RAND_67 = {1{`RANDOM}};
  final_state_REG_9_negative = _RAND_67[0:0];
  _RAND_68 = {1{`RANDOM}};
  final_state_REG_9_divideByZero = _RAND_68[0:0];
  _RAND_69 = {1{`RANDOM}};
  final_state_REG_9_valid = _RAND_69[0:0];
  _RAND_70 = {1{`RANDOM}};
  final_state_REG_10_remainder = _RAND_70[20:0];
  _RAND_71 = {1{`RANDOM}};
  final_state_REG_10_quotient = _RAND_71[31:0];
  _RAND_72 = {1{`RANDOM}};
  final_state_REG_10_dividend_shifted = _RAND_72[31:0];
  _RAND_73 = {1{`RANDOM}};
  final_state_REG_10_divisor = _RAND_73[19:0];
  _RAND_74 = {1{`RANDOM}};
  final_state_REG_10_negative = _RAND_74[0:0];
  _RAND_75 = {1{`RANDOM}};
  final_state_REG_10_divideByZero = _RAND_75[0:0];
  _RAND_76 = {1{`RANDOM}};
  final_state_REG_10_valid = _RAND_76[0:0];
  _RAND_77 = {1{`RANDOM}};
  final_state_REG_11_remainder = _RAND_77[20:0];
  _RAND_78 = {1{`RANDOM}};
  final_state_REG_11_quotient = _RAND_78[31:0];
  _RAND_79 = {1{`RANDOM}};
  final_state_REG_11_dividend_shifted = _RAND_79[31:0];
  _RAND_80 = {1{`RANDOM}};
  final_state_REG_11_divisor = _RAND_80[19:0];
  _RAND_81 = {1{`RANDOM}};
  final_state_REG_11_negative = _RAND_81[0:0];
  _RAND_82 = {1{`RANDOM}};
  final_state_REG_11_divideByZero = _RAND_82[0:0];
  _RAND_83 = {1{`RANDOM}};
  final_state_REG_11_valid = _RAND_83[0:0];
  _RAND_84 = {1{`RANDOM}};
  final_state_REG_12_remainder = _RAND_84[20:0];
  _RAND_85 = {1{`RANDOM}};
  final_state_REG_12_quotient = _RAND_85[31:0];
  _RAND_86 = {1{`RANDOM}};
  final_state_REG_12_dividend_shifted = _RAND_86[31:0];
  _RAND_87 = {1{`RANDOM}};
  final_state_REG_12_divisor = _RAND_87[19:0];
  _RAND_88 = {1{`RANDOM}};
  final_state_REG_12_negative = _RAND_88[0:0];
  _RAND_89 = {1{`RANDOM}};
  final_state_REG_12_divideByZero = _RAND_89[0:0];
  _RAND_90 = {1{`RANDOM}};
  final_state_REG_12_valid = _RAND_90[0:0];
  _RAND_91 = {1{`RANDOM}};
  final_state_REG_13_remainder = _RAND_91[20:0];
  _RAND_92 = {1{`RANDOM}};
  final_state_REG_13_quotient = _RAND_92[31:0];
  _RAND_93 = {1{`RANDOM}};
  final_state_REG_13_dividend_shifted = _RAND_93[31:0];
  _RAND_94 = {1{`RANDOM}};
  final_state_REG_13_divisor = _RAND_94[19:0];
  _RAND_95 = {1{`RANDOM}};
  final_state_REG_13_negative = _RAND_95[0:0];
  _RAND_96 = {1{`RANDOM}};
  final_state_REG_13_divideByZero = _RAND_96[0:0];
  _RAND_97 = {1{`RANDOM}};
  final_state_REG_13_valid = _RAND_97[0:0];
  _RAND_98 = {1{`RANDOM}};
  final_state_REG_14_remainder = _RAND_98[20:0];
  _RAND_99 = {1{`RANDOM}};
  final_state_REG_14_quotient = _RAND_99[31:0];
  _RAND_100 = {1{`RANDOM}};
  final_state_REG_14_dividend_shifted = _RAND_100[31:0];
  _RAND_101 = {1{`RANDOM}};
  final_state_REG_14_divisor = _RAND_101[19:0];
  _RAND_102 = {1{`RANDOM}};
  final_state_REG_14_negative = _RAND_102[0:0];
  _RAND_103 = {1{`RANDOM}};
  final_state_REG_14_divideByZero = _RAND_103[0:0];
  _RAND_104 = {1{`RANDOM}};
  final_state_REG_14_valid = _RAND_104[0:0];
  _RAND_105 = {1{`RANDOM}};
  final_state_REG_15_remainder = _RAND_105[20:0];
  _RAND_106 = {1{`RANDOM}};
  final_state_REG_15_quotient = _RAND_106[31:0];
  _RAND_107 = {1{`RANDOM}};
  final_state_REG_15_dividend_shifted = _RAND_107[31:0];
  _RAND_108 = {1{`RANDOM}};
  final_state_REG_15_divisor = _RAND_108[19:0];
  _RAND_109 = {1{`RANDOM}};
  final_state_REG_15_negative = _RAND_109[0:0];
  _RAND_110 = {1{`RANDOM}};
  final_state_REG_15_divideByZero = _RAND_110[0:0];
  _RAND_111 = {1{`RANDOM}};
  final_state_REG_15_valid = _RAND_111[0:0];
  _RAND_112 = {1{`RANDOM}};
  final_state_REG_16_remainder = _RAND_112[20:0];
  _RAND_113 = {1{`RANDOM}};
  final_state_REG_16_quotient = _RAND_113[31:0];
  _RAND_114 = {1{`RANDOM}};
  final_state_REG_16_dividend_shifted = _RAND_114[31:0];
  _RAND_115 = {1{`RANDOM}};
  final_state_REG_16_divisor = _RAND_115[19:0];
  _RAND_116 = {1{`RANDOM}};
  final_state_REG_16_negative = _RAND_116[0:0];
  _RAND_117 = {1{`RANDOM}};
  final_state_REG_16_divideByZero = _RAND_117[0:0];
  _RAND_118 = {1{`RANDOM}};
  final_state_REG_16_valid = _RAND_118[0:0];
  _RAND_119 = {1{`RANDOM}};
  final_state_quotient = _RAND_119[31:0];
  _RAND_120 = {1{`RANDOM}};
  final_state_negative = _RAND_120[0:0];
  _RAND_121 = {1{`RANDOM}};
  final_state_divideByZero = _RAND_121[0:0];
  _RAND_122 = {1{`RANDOM}};
  final_state_valid = _RAND_122[0:0];
`endif // RANDOMIZE_REG_INIT
  `endif // RANDOMIZE
end // initial
`ifdef FIRRTL_AFTER_INITIAL
`FIRRTL_AFTER_INITIAL
`endif
`endif // SYNTHESIS
endmodule
module rq1_global_topk(
  input          clock, // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 5:17]
  input          reset, // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 6:17]
  input          start, // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 7:17]
  input  [7:0]   q, // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 8:13]
  input  [127:0] k, // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 9:13]
  input  [127:0] v, // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 10:13]
  output         done, // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 11:16]
  output [15:0]  result, // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 12:18]
  output [15:0]  keep_mask // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 13:21]
);
`ifdef RANDOMIZE_REG_INIT
  reg [31:0] _RAND_0;
  reg [31:0] _RAND_1;
  reg [127:0] _RAND_2;
  reg [127:0] _RAND_3;
  reg [31:0] _RAND_4;
  reg [31:0] _RAND_5;
  reg [31:0] _RAND_6;
  reg [31:0] _RAND_7;
  reg [31:0] _RAND_8;
  reg [31:0] _RAND_9;
  reg [31:0] _RAND_10;
  reg [31:0] _RAND_11;
  reg [31:0] _RAND_12;
  reg [31:0] _RAND_13;
  reg [31:0] _RAND_14;
  reg [31:0] _RAND_15;
  reg [31:0] _RAND_16;
  reg [31:0] _RAND_17;
  reg [31:0] _RAND_18;
  reg [31:0] _RAND_19;
  reg [31:0] _RAND_20;
  reg [31:0] _RAND_21;
  reg [31:0] _RAND_22;
  reg [31:0] _RAND_23;
  reg [31:0] _RAND_24;
  reg [31:0] _RAND_25;
  reg [31:0] _RAND_26;
  reg [31:0] _RAND_27;
  reg [31:0] _RAND_28;
`endif // RANDOMIZE_REG_INIT
  wire [7:0] score_calc_q_in; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 16:26]
  wire [7:0] score_calc_k_in; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 16:26]
  wire [8:0] score_calc_score_out; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 16:26]
  wire [7:0] exp_lut_delta; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 17:23]
  wire [15:0] exp_lut_exp_val; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 17:23]
  wire  divider_clock; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 18:23]
  wire  divider_reset; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 18:23]
  wire  divider_valid_in; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 18:23]
  wire [27:0] divider_numer; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 18:23]
  wire [19:0] divider_denom; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 18:23]
  wire [15:0] divider_quotient; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 18:23]
  wire  divider_valid_out; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 18:23]
  reg [2:0] state; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 26:56]
  reg [7:0] q_reg; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 29:52]
  reg [127:0] k_reg; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 30:52]
  reg [127:0] v_reg; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 31:52]
  reg [8:0] score_regs_0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 33:57]
  reg [8:0] score_regs_1; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 33:57]
  reg [8:0] score_regs_2; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 33:57]
  reg [8:0] score_regs_3; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 33:57]
  reg [8:0] score_regs_4; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 33:57]
  reg [8:0] score_regs_5; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 33:57]
  reg [8:0] score_regs_6; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 33:57]
  reg [8:0] score_regs_7; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 33:57]
  reg [8:0] score_regs_8; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 33:57]
  reg [8:0] score_regs_9; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 33:57]
  reg [8:0] score_regs_10; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 33:57]
  reg [8:0] score_regs_11; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 33:57]
  reg [8:0] score_regs_12; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 33:57]
  reg [8:0] score_regs_13; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 33:57]
  reg [8:0] score_regs_14; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 33:57]
  reg [8:0] score_regs_15; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 33:57]
  reg [8:0] h_reg; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 34:52]
  reg [8:0] min_score_reg; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 35:60]
  reg [3:0] loser_idx_reg; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 36:60]
  reg [27:0] N_reg; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 38:52]
  reg [19:0] D_reg; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 39:52]
  reg [3:0] cycle_counter; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 41:60]
  reg [15:0] result_reg; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 44:57]
  reg [15:0] keep_mask_reg; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 45:60]
  reg  done_reg; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 46:59]
  wire [7:0] k_vec_0 = k_reg[7:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 57:29]
  wire [7:0] k_vec_1 = k_reg[15:8]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 57:29]
  wire [7:0] k_vec_2 = k_reg[23:16]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 57:29]
  wire [7:0] k_vec_3 = k_reg[31:24]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 57:29]
  wire [7:0] k_vec_4 = k_reg[39:32]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 57:29]
  wire [7:0] k_vec_5 = k_reg[47:40]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 57:29]
  wire [7:0] k_vec_6 = k_reg[55:48]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 57:29]
  wire [7:0] k_vec_7 = k_reg[63:56]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 57:29]
  wire [7:0] k_vec_8 = k_reg[71:64]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 57:29]
  wire [7:0] k_vec_9 = k_reg[79:72]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 57:29]
  wire [7:0] k_vec_10 = k_reg[87:80]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 57:29]
  wire [7:0] k_vec_11 = k_reg[95:88]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 57:29]
  wire [7:0] k_vec_12 = k_reg[103:96]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 57:29]
  wire [7:0] k_vec_13 = k_reg[111:104]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 57:29]
  wire [7:0] k_vec_14 = k_reg[119:112]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 57:29]
  wire [7:0] k_vec_15 = k_reg[127:120]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 57:29]
  wire [7:0] v_vec_0 = v_reg[7:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 58:29]
  wire [7:0] v_vec_1 = v_reg[15:8]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 58:29]
  wire [7:0] v_vec_2 = v_reg[23:16]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 58:29]
  wire [7:0] v_vec_3 = v_reg[31:24]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 58:29]
  wire [7:0] v_vec_4 = v_reg[39:32]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 58:29]
  wire [7:0] v_vec_5 = v_reg[47:40]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 58:29]
  wire [7:0] v_vec_6 = v_reg[55:48]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 58:29]
  wire [7:0] v_vec_7 = v_reg[63:56]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 58:29]
  wire [7:0] v_vec_8 = v_reg[71:64]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 58:29]
  wire [7:0] v_vec_9 = v_reg[79:72]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 58:29]
  wire [7:0] v_vec_10 = v_reg[87:80]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 58:29]
  wire [7:0] v_vec_11 = v_reg[95:88]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 58:29]
  wire [7:0] v_vec_12 = v_reg[103:96]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 58:29]
  wire [7:0] v_vec_13 = v_reg[111:104]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 58:29]
  wire [7:0] v_vec_14 = v_reg[119:112]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 58:29]
  wire [7:0] v_vec_15 = v_reg[127:120]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 58:29]
  wire [7:0] _GEN_1 = 4'h1 == cycle_counter ? k_vec_1 : k_vec_0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 61:{19,19}]
  wire [7:0] _GEN_2 = 4'h2 == cycle_counter ? k_vec_2 : _GEN_1; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 61:{19,19}]
  wire [7:0] _GEN_3 = 4'h3 == cycle_counter ? k_vec_3 : _GEN_2; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 61:{19,19}]
  wire [7:0] _GEN_4 = 4'h4 == cycle_counter ? k_vec_4 : _GEN_3; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 61:{19,19}]
  wire [7:0] _GEN_5 = 4'h5 == cycle_counter ? k_vec_5 : _GEN_4; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 61:{19,19}]
  wire [7:0] _GEN_6 = 4'h6 == cycle_counter ? k_vec_6 : _GEN_5; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 61:{19,19}]
  wire [7:0] _GEN_7 = 4'h7 == cycle_counter ? k_vec_7 : _GEN_6; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 61:{19,19}]
  wire [7:0] _GEN_8 = 4'h8 == cycle_counter ? k_vec_8 : _GEN_7; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 61:{19,19}]
  wire [7:0] _GEN_9 = 4'h9 == cycle_counter ? k_vec_9 : _GEN_8; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 61:{19,19}]
  wire [7:0] _GEN_10 = 4'ha == cycle_counter ? k_vec_10 : _GEN_9; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 61:{19,19}]
  wire [7:0] _GEN_11 = 4'hb == cycle_counter ? k_vec_11 : _GEN_10; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 61:{19,19}]
  wire [7:0] _GEN_12 = 4'hc == cycle_counter ? k_vec_12 : _GEN_11; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 61:{19,19}]
  wire [7:0] _GEN_13 = 4'hd == cycle_counter ? k_vec_13 : _GEN_12; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 61:{19,19}]
  wire [7:0] _GEN_14 = 4'he == cycle_counter ? k_vec_14 : _GEN_13; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 61:{19,19}]
  wire [8:0] _GEN_17 = 4'h1 == cycle_counter ? $signed(score_regs_1) : $signed(score_regs_0); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 63:{22,22}]
  wire [8:0] _GEN_18 = 4'h2 == cycle_counter ? $signed(score_regs_2) : $signed(_GEN_17); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 63:{22,22}]
  wire [8:0] _GEN_19 = 4'h3 == cycle_counter ? $signed(score_regs_3) : $signed(_GEN_18); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 63:{22,22}]
  wire [8:0] _GEN_20 = 4'h4 == cycle_counter ? $signed(score_regs_4) : $signed(_GEN_19); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 63:{22,22}]
  wire [8:0] _GEN_21 = 4'h5 == cycle_counter ? $signed(score_regs_5) : $signed(_GEN_20); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 63:{22,22}]
  wire [8:0] _GEN_22 = 4'h6 == cycle_counter ? $signed(score_regs_6) : $signed(_GEN_21); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 63:{22,22}]
  wire [8:0] _GEN_23 = 4'h7 == cycle_counter ? $signed(score_regs_7) : $signed(_GEN_22); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 63:{22,22}]
  wire [8:0] _GEN_24 = 4'h8 == cycle_counter ? $signed(score_regs_8) : $signed(_GEN_23); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 63:{22,22}]
  wire [8:0] _GEN_25 = 4'h9 == cycle_counter ? $signed(score_regs_9) : $signed(_GEN_24); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 63:{22,22}]
  wire [8:0] _GEN_26 = 4'ha == cycle_counter ? $signed(score_regs_10) : $signed(_GEN_25); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 63:{22,22}]
  wire [8:0] _GEN_27 = 4'hb == cycle_counter ? $signed(score_regs_11) : $signed(_GEN_26); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 63:{22,22}]
  wire [8:0] _GEN_28 = 4'hc == cycle_counter ? $signed(score_regs_12) : $signed(_GEN_27); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 63:{22,22}]
  wire [8:0] _GEN_29 = 4'hd == cycle_counter ? $signed(score_regs_13) : $signed(_GEN_28); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 63:{22,22}]
  wire [8:0] _GEN_30 = 4'he == cycle_counter ? $signed(score_regs_14) : $signed(_GEN_29); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 63:{22,22}]
  wire [8:0] _GEN_31 = 4'hf == cycle_counter ? $signed(score_regs_15) : $signed(_GEN_30); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 63:{22,22}]
  wire [8:0] delta = $signed(h_reg) - $signed(_GEN_31); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 63:51]
  wire [8:0] _score_regs_cycle_counter_0 = score_calc_score_out; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:{33,33}]
  wire [3:0] next_counter = cycle_counter + 4'h1; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 94:40]
  wire  _T_2 = cycle_counter == 4'hf; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 96:26]
  wire [3:0] _GEN_59 = cycle_counter == 4'hf ? 4'h0 : next_counter; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 95:21 96:36 98:23]
  wire [2:0] _GEN_63 = _T_2 ? 3'h3 : state; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 117:36 118:15 26:56]
  wire [16:0] _product_T = {1'b0,$signed(exp_lut_exp_val)}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 128:25]
  wire [7:0] _GEN_66 = 4'h1 == cycle_counter ? $signed(v_vec_1) : $signed(v_vec_0); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 128:{30,30}]
  wire [7:0] _GEN_67 = 4'h2 == cycle_counter ? $signed(v_vec_2) : $signed(_GEN_66); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 128:{30,30}]
  wire [7:0] _GEN_68 = 4'h3 == cycle_counter ? $signed(v_vec_3) : $signed(_GEN_67); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 128:{30,30}]
  wire [7:0] _GEN_69 = 4'h4 == cycle_counter ? $signed(v_vec_4) : $signed(_GEN_68); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 128:{30,30}]
  wire [7:0] _GEN_70 = 4'h5 == cycle_counter ? $signed(v_vec_5) : $signed(_GEN_69); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 128:{30,30}]
  wire [7:0] _GEN_71 = 4'h6 == cycle_counter ? $signed(v_vec_6) : $signed(_GEN_70); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 128:{30,30}]
  wire [7:0] _GEN_72 = 4'h7 == cycle_counter ? $signed(v_vec_7) : $signed(_GEN_71); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 128:{30,30}]
  wire [7:0] _GEN_73 = 4'h8 == cycle_counter ? $signed(v_vec_8) : $signed(_GEN_72); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 128:{30,30}]
  wire [7:0] _GEN_74 = 4'h9 == cycle_counter ? $signed(v_vec_9) : $signed(_GEN_73); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 128:{30,30}]
  wire [7:0] _GEN_75 = 4'ha == cycle_counter ? $signed(v_vec_10) : $signed(_GEN_74); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 128:{30,30}]
  wire [7:0] _GEN_76 = 4'hb == cycle_counter ? $signed(v_vec_11) : $signed(_GEN_75); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 128:{30,30}]
  wire [7:0] _GEN_77 = 4'hc == cycle_counter ? $signed(v_vec_12) : $signed(_GEN_76); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 128:{30,30}]
  wire [7:0] _GEN_78 = 4'hd == cycle_counter ? $signed(v_vec_13) : $signed(_GEN_77); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 128:{30,30}]
  wire [7:0] _GEN_79 = 4'he == cycle_counter ? $signed(v_vec_14) : $signed(_GEN_78); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 128:{30,30}]
  wire [7:0] _GEN_80 = 4'hf == cycle_counter ? $signed(v_vec_15) : $signed(_GEN_79); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 128:{30,30}]
  wire [24:0] product = $signed(_product_T) * $signed(_GEN_80); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 128:30]
  wire [27:0] _GEN_174 = {{3{product[24]}},product}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 132:24]
  wire [27:0] _N_reg_T_2 = $signed(N_reg) + $signed(_GEN_174); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 132:24]
  wire [19:0] _GEN_175 = {{4'd0}, exp_lut_exp_val}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 133:24]
  wire [19:0] _D_reg_T_1 = D_reg + _GEN_175; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 133:24]
  wire [27:0] _GEN_81 = cycle_counter != loser_idx_reg ? $signed(_N_reg_T_2) : $signed(N_reg); // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 130:45 132:15 38:52]
  wire [19:0] _GEN_82 = cycle_counter != loser_idx_reg ? _D_reg_T_1 : D_reg; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 130:45 133:15 39:52]
  wire [2:0] _GEN_83 = _T_2 ? 3'h4 : state; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 138:36 139:15 26:56]
  wire [30:0] _keep_mask_reg_T = 31'h1 << loser_idx_reg; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 152:38]
  wire [30:0] _keep_mask_reg_T_1 = ~_keep_mask_reg_T; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 152:26]
  wire [2:0] _GEN_84 = divider_valid_out ? 3'h6 : state; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 149:31 150:15 26:56]
  wire [15:0] _GEN_85 = divider_valid_out ? divider_quotient : result_reg; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 149:31 151:20 44:57]
  wire [30:0] _GEN_86 = divider_valid_out ? _keep_mask_reg_T_1 : {{15'd0}, keep_mask_reg}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 149:31 152:23 45:60]
  wire [2:0] _GEN_88 = 3'h6 == state ? 3'h0 : state; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 158:13 74:17 26:56]
  wire [2:0] _GEN_89 = 3'h5 == state ? _GEN_84 : _GEN_88; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
  wire [15:0] _GEN_90 = 3'h5 == state ? _GEN_85 : result_reg; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17 44:57]
  wire [30:0] _GEN_91 = 3'h5 == state ? _GEN_86 : {{15'd0}, keep_mask_reg}; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17 45:60]
  wire  _GEN_92 = 3'h5 == state ? 1'h0 : 3'h6 == state; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 72:12 74:17]
  wire [2:0] _GEN_94 = 3'h4 == state ? 3'h5 : _GEN_89; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 145:13 74:17]
  wire [15:0] _GEN_95 = 3'h4 == state ? result_reg : _GEN_90; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17 44:57]
  wire [30:0] _GEN_96 = 3'h4 == state ? {{15'd0}, keep_mask_reg} : _GEN_91; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17 45:60]
  wire  _GEN_97 = 3'h4 == state ? 1'h0 : _GEN_92; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 72:12 74:17]
  wire [2:0] _GEN_101 = 3'h3 == state ? _GEN_83 : _GEN_94; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
  wire  _GEN_102 = 3'h3 == state ? 1'h0 : 3'h4 == state; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17 54:20]
  wire [30:0] _GEN_104 = 3'h3 == state ? {{15'd0}, keep_mask_reg} : _GEN_96; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17 45:60]
  wire  _GEN_105 = 3'h3 == state ? 1'h0 : _GEN_97; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 72:12 74:17]
  wire  _GEN_113 = 3'h2 == state ? 1'h0 : _GEN_102; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17 54:20]
  wire [30:0] _GEN_115 = 3'h2 == state ? {{15'd0}, keep_mask_reg} : _GEN_104; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17 45:60]
  wire  _GEN_140 = 3'h1 == state ? 1'h0 : _GEN_113; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17 54:20]
  wire [30:0] _GEN_142 = 3'h1 == state ? {{15'd0}, keep_mask_reg} : _GEN_115; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17 45:60]
  wire [30:0] _GEN_172 = 3'h0 == state ? {{15'd0}, keep_mask_reg} : _GEN_142; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17 45:60]
  ScoreCalculator score_calc ( // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 16:26]
    .q_in(score_calc_q_in),
    .k_in(score_calc_k_in),
    .score_out(score_calc_score_out)
  );
  ExpLut exp_lut ( // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 17:23]
    .delta(exp_lut_delta),
    .exp_val(exp_lut_exp_val)
  );
  FinalDivider divider ( // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 18:23]
    .clock(divider_clock),
    .reset(divider_reset),
    .valid_in(divider_valid_in),
    .numer(divider_numer),
    .denom(divider_denom),
    .quotient(divider_quotient),
    .valid_out(divider_valid_out)
  );
  assign done = done_reg; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 49:8]
  assign result = result_reg; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 50:10]
  assign keep_mask = keep_mask_reg; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 51:13]
  assign score_calc_q_in = q_reg; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 60:19]
  assign score_calc_k_in = 4'hf == cycle_counter ? k_vec_15 : _GEN_14; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 61:{19,19}]
  assign exp_lut_delta = delta[7:0]; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 64:25]
  assign divider_clock = clock; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 21:17]
  assign divider_reset = reset; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 22:17]
  assign divider_valid_in = 3'h0 == state ? 1'h0 : _GEN_140; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17 54:20]
  assign divider_numer = N_reg; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 66:26]
  assign divider_denom = D_reg; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 67:17]
  always @(posedge clock) begin
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 26:56]
      state <= 3'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 26:56]
    end else if (3'h0 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (start) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 76:19]
        state <= 3'h1; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 77:15]
      end
    end else if (3'h1 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (cycle_counter == 4'hf) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 96:36]
        state <= 3'h2; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 97:15]
      end
    end else if (3'h2 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      state <= _GEN_63;
    end else begin
      state <= _GEN_101;
    end
    if (3'h0 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (start) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 76:19]
        q_reg <= q; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 78:15]
      end
    end
    if (3'h0 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (start) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 76:19]
        k_reg <= k; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 79:15]
      end
    end
    if (3'h0 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (start) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 76:19]
        v_reg <= v; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 80:15]
      end
    end
    if (!(3'h0 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (3'h1 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
        if (4'h0 == cycle_counter) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
          score_regs_0 <= _score_regs_cycle_counter_0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
        end
      end
    end
    if (!(3'h0 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (3'h1 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
        if (4'h1 == cycle_counter) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
          score_regs_1 <= _score_regs_cycle_counter_0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
        end
      end
    end
    if (!(3'h0 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (3'h1 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
        if (4'h2 == cycle_counter) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
          score_regs_2 <= _score_regs_cycle_counter_0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
        end
      end
    end
    if (!(3'h0 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (3'h1 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
        if (4'h3 == cycle_counter) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
          score_regs_3 <= _score_regs_cycle_counter_0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
        end
      end
    end
    if (!(3'h0 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (3'h1 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
        if (4'h4 == cycle_counter) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
          score_regs_4 <= _score_regs_cycle_counter_0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
        end
      end
    end
    if (!(3'h0 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (3'h1 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
        if (4'h5 == cycle_counter) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
          score_regs_5 <= _score_regs_cycle_counter_0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
        end
      end
    end
    if (!(3'h0 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (3'h1 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
        if (4'h6 == cycle_counter) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
          score_regs_6 <= _score_regs_cycle_counter_0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
        end
      end
    end
    if (!(3'h0 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (3'h1 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
        if (4'h7 == cycle_counter) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
          score_regs_7 <= _score_regs_cycle_counter_0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
        end
      end
    end
    if (!(3'h0 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (3'h1 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
        if (4'h8 == cycle_counter) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
          score_regs_8 <= _score_regs_cycle_counter_0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
        end
      end
    end
    if (!(3'h0 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (3'h1 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
        if (4'h9 == cycle_counter) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
          score_regs_9 <= _score_regs_cycle_counter_0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
        end
      end
    end
    if (!(3'h0 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (3'h1 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
        if (4'ha == cycle_counter) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
          score_regs_10 <= _score_regs_cycle_counter_0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
        end
      end
    end
    if (!(3'h0 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (3'h1 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
        if (4'hb == cycle_counter) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
          score_regs_11 <= _score_regs_cycle_counter_0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
        end
      end
    end
    if (!(3'h0 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (3'h1 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
        if (4'hc == cycle_counter) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
          score_regs_12 <= _score_regs_cycle_counter_0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
        end
      end
    end
    if (!(3'h0 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (3'h1 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
        if (4'hd == cycle_counter) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
          score_regs_13 <= _score_regs_cycle_counter_0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
        end
      end
    end
    if (!(3'h0 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (3'h1 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
        if (4'he == cycle_counter) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
          score_regs_14 <= _score_regs_cycle_counter_0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
        end
      end
    end
    if (!(3'h0 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (3'h1 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
        if (4'hf == cycle_counter) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
          score_regs_15 <= _score_regs_cycle_counter_0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 93:33]
        end
      end
    end
    if (3'h0 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (start) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 76:19]
        h_reg <= 9'sh100; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 85:15]
      end
    end else if (!(3'h1 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (3'h2 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
        if ($signed(_GEN_31) > $signed(h_reg)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 105:35]
          h_reg <= _GEN_31; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 106:15]
        end
      end
    end
    if (3'h0 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (start) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 76:19]
        min_score_reg <= 9'shff; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 87:23]
      end
    end else if (!(3'h1 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (3'h2 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
        if ($signed(_GEN_31) <= $signed(min_score_reg)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 110:44]
          min_score_reg <= _GEN_31; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 111:23]
        end
      end
    end
    if (3'h0 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (start) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 76:19]
        loser_idx_reg <= 4'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 88:23]
      end
    end else if (!(3'h1 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (3'h2 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
        if ($signed(_GEN_31) <= $signed(min_score_reg)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 110:44]
          loser_idx_reg <= cycle_counter; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 112:23]
        end
      end
    end
    if (3'h0 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (start) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 76:19]
        N_reg <= 28'sh0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 82:15]
      end
    end else if (!(3'h1 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (!(3'h2 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
        if (3'h3 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
          N_reg <= _GEN_81;
        end
      end
    end
    if (3'h0 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (start) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 76:19]
        D_reg <= 20'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 83:15]
      end
    end else if (!(3'h1 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (!(3'h2 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
        if (3'h3 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
          D_reg <= _GEN_82;
        end
      end
    end
    if (3'h0 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (start) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 76:19]
        cycle_counter <= 4'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 81:23]
      end
    end else if (3'h1 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      cycle_counter <= _GEN_59;
    end else if (3'h2 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      cycle_counter <= _GEN_59;
    end else if (3'h3 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      cycle_counter <= next_counter; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 137:21]
    end
    if (!(3'h0 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      if (!(3'h1 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
        if (!(3'h2 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
          if (!(3'h3 == state)) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
            result_reg <= _GEN_95;
          end
        end
      end
    end
    keep_mask_reg <= _GEN_172[15:0];
    if (reset) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 46:59]
      done_reg <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 46:59]
    end else if (3'h0 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      done_reg <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 72:12]
    end else if (3'h1 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      done_reg <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 72:12]
    end else if (3'h2 == state) begin // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 74:17]
      done_reg <= 1'h0; // @[home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_20260915/rq1_global_topk/rtl_holdout_round_5/rebuild/rq1_global_topk.scala 72:12]
    end else begin
      done_reg <= _GEN_105;
    end
  end
// Register and memory initialization
`ifdef RANDOMIZE_GARBAGE_ASSIGN
`define RANDOMIZE
`endif
`ifdef RANDOMIZE_INVALID_ASSIGN
`define RANDOMIZE
`endif
`ifdef RANDOMIZE_REG_INIT
`define RANDOMIZE
`endif
`ifdef RANDOMIZE_MEM_INIT
`define RANDOMIZE
`endif
`ifndef RANDOM
`define RANDOM $random
`endif
`ifdef RANDOMIZE_MEM_INIT
  integer initvar;
`endif
`ifndef SYNTHESIS
`ifdef FIRRTL_BEFORE_INITIAL
`FIRRTL_BEFORE_INITIAL
`endif
initial begin
  `ifdef RANDOMIZE
    `ifdef INIT_RANDOM
      `INIT_RANDOM
    `endif
    `ifndef VERILATOR
      `ifdef RANDOMIZE_DELAY
        #`RANDOMIZE_DELAY begin end
      `else
        #0.002 begin end
      `endif
    `endif
`ifdef RANDOMIZE_REG_INIT
  _RAND_0 = {1{`RANDOM}};
  state = _RAND_0[2:0];
  _RAND_1 = {1{`RANDOM}};
  q_reg = _RAND_1[7:0];
  _RAND_2 = {4{`RANDOM}};
  k_reg = _RAND_2[127:0];
  _RAND_3 = {4{`RANDOM}};
  v_reg = _RAND_3[127:0];
  _RAND_4 = {1{`RANDOM}};
  score_regs_0 = _RAND_4[8:0];
  _RAND_5 = {1{`RANDOM}};
  score_regs_1 = _RAND_5[8:0];
  _RAND_6 = {1{`RANDOM}};
  score_regs_2 = _RAND_6[8:0];
  _RAND_7 = {1{`RANDOM}};
  score_regs_3 = _RAND_7[8:0];
  _RAND_8 = {1{`RANDOM}};
  score_regs_4 = _RAND_8[8:0];
  _RAND_9 = {1{`RANDOM}};
  score_regs_5 = _RAND_9[8:0];
  _RAND_10 = {1{`RANDOM}};
  score_regs_6 = _RAND_10[8:0];
  _RAND_11 = {1{`RANDOM}};
  score_regs_7 = _RAND_11[8:0];
  _RAND_12 = {1{`RANDOM}};
  score_regs_8 = _RAND_12[8:0];
  _RAND_13 = {1{`RANDOM}};
  score_regs_9 = _RAND_13[8:0];
  _RAND_14 = {1{`RANDOM}};
  score_regs_10 = _RAND_14[8:0];
  _RAND_15 = {1{`RANDOM}};
  score_regs_11 = _RAND_15[8:0];
  _RAND_16 = {1{`RANDOM}};
  score_regs_12 = _RAND_16[8:0];
  _RAND_17 = {1{`RANDOM}};
  score_regs_13 = _RAND_17[8:0];
  _RAND_18 = {1{`RANDOM}};
  score_regs_14 = _RAND_18[8:0];
  _RAND_19 = {1{`RANDOM}};
  score_regs_15 = _RAND_19[8:0];
  _RAND_20 = {1{`RANDOM}};
  h_reg = _RAND_20[8:0];
  _RAND_21 = {1{`RANDOM}};
  min_score_reg = _RAND_21[8:0];
  _RAND_22 = {1{`RANDOM}};
  loser_idx_reg = _RAND_22[3:0];
  _RAND_23 = {1{`RANDOM}};
  N_reg = _RAND_23[27:0];
  _RAND_24 = {1{`RANDOM}};
  D_reg = _RAND_24[19:0];
  _RAND_25 = {1{`RANDOM}};
  cycle_counter = _RAND_25[3:0];
  _RAND_26 = {1{`RANDOM}};
  result_reg = _RAND_26[15:0];
  _RAND_27 = {1{`RANDOM}};
  keep_mask_reg = _RAND_27[15:0];
  _RAND_28 = {1{`RANDOM}};
  done_reg = _RAND_28[0:0];
`endif // RANDOMIZE_REG_INIT
  `endif // RANDOMIZE
end // initial
`ifdef FIRRTL_AFTER_INITIAL
`FIRRTL_AFTER_INITIAL
`endif
`endif // SYNTHESIS
endmodule

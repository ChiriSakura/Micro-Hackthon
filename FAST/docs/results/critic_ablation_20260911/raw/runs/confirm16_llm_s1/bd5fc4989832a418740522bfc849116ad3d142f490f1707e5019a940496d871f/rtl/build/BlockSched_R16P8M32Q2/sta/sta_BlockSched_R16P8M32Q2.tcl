read_liberty /scratch/gz2522/gz2522/tmp/micro-hackthon/pdk/nangate45/NangateOpenCellLibrary_typical.lib
read_verilog /scratch/gz2522/gz2522/tmp/micro-hackthon/runs/critic_ablation_20260911/runs/confirm16_llm_s1/bd5fc4989832a418740522bfc849116ad3d142f490f1707e5019a940496d871f/rtl/build/BlockSched_R16P8M32Q2/synth/BlockSched_R16P8M32Q2.mapped.v
link_design BlockScheduler
create_clock -name clk -period 2.857142857142857 [get_ports clock]
set_input_delay 0.14285714285714288 -clock clk [all_inputs -no_clocks]
set_output_delay 0.14285714285714288 -clock clk [all_outputs]
report_checks -path_delay max -digits 4
set_power_activity -global -activity 0.0213 -duty 0.5
report_power -digits 6
exit
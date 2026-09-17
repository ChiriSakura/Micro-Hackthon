read_liberty /scratch/gz2522/gz2522/tmp/micro-hackthon/pdk/nangate45/NangateOpenCellLibrary_typical.lib
read_verilog /scratch/gz2522/gz2522/tmp/micro-hackthon/runs/critic_ablation_20260911/runs/main32_off_s0/f91dbcd4bfbcac962aa4988a4e0ae1028045c7d4fcd546e3decb252b65594a5b/rtl/build/BlockSched_R32P4M32Q4/synth/BlockSched_R32P4M32Q4.mapped.v
link_design BlockScheduler
create_clock -name clk -period 2.857142857142857 [get_ports clock]
set_input_delay 0.14285714285714288 -clock clk [all_inputs -no_clocks]
set_output_delay 0.14285714285714288 -clock clk [all_outputs]
report_checks -path_delay max -digits 4
set_power_activity -global -activity 0.0213 -duty 0.5
report_power -digits 6
exit
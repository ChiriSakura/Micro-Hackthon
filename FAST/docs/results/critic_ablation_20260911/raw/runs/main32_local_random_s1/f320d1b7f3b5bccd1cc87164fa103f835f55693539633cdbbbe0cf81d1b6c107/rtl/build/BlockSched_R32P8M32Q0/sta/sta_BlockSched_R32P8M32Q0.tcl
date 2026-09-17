read_liberty /scratch/gz2522/gz2522/tmp/micro-hackthon/pdk/nangate45/NangateOpenCellLibrary_typical.lib
read_verilog /scratch/gz2522/gz2522/tmp/micro-hackthon/runs/critic_ablation_20260911/runs/main32_local_random_s1/f320d1b7f3b5bccd1cc87164fa103f835f55693539633cdbbbe0cf81d1b6c107/rtl/build/BlockSched_R32P8M32Q0/synth/BlockSched_R32P8M32Q0.mapped.v
link_design BlockScheduler
create_clock -name clk -period 2.857142857142857 [get_ports clock]
set_input_delay 0.14285714285714288 -clock clk [all_inputs -no_clocks]
set_output_delay 0.14285714285714288 -clock clk [all_outputs]
report_checks -path_delay max -digits 4
set_power_activity -global -activity 0.0213 -duty 0.5
report_power -digits 6
exit
read_liberty /scratch/gz2522/gz2522/tmp/micro-hackthon/pdk/nangate45/NangateOpenCellLibrary_typical.lib
read_verilog /scratch/gz2522/gz2522/tmp/micro-hackthon/runs/fullstack_17591809/round_01/build_03/mapped.v
link_design ThresholdAttention
create_clock -name clk -period 10.0 [get_ports clock]
set_input_delay 0.5 -clock clk [all_inputs -no_clocks]
set_output_delay 0.5 -clock clk [all_outputs]
report_checks -path_delay max -digits 4
set_power_activity -global -activity 0.1 -duty 0.5
report_power -digits 6
exit
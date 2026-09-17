read_liberty /scratch/gz2522/gz2522/tmp/micro-hackthon/pdk/nangate45/NangateOpenCellLibrary_typical.lib
read_verilog /home/gz2522/Micro-Hackthon/FAST/docs/results/rq1_completion_20260917/rq1_dynax_xm/rtl_holdout_round_5/rebuild/mapped.v
link_design Rq1DynaXm
create_clock -name clk -period 3.3333333333333335 [get_ports clock]
set_input_delay 0.16666666666666669 -clock clk [all_inputs -no_clocks]
set_output_delay 0.16666666666666669 -clock clk [all_outputs]
report_checks -path_delay max -digits 4
set_power_activity -global -activity 0.1 -duty 0.5
report_power -digits 6
exit
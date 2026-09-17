define_corners setup hold
read_liberty -corner setup {/scratch/gz2522/gz2522/tmp/micro-hackthon/pdk/hammer45/lib/NangateOpenCellLibrary_typical.lib}
read_liberty -corner hold {/scratch/gz2522/gz2522/tmp/micro-hackthon/pdk/hammer45/lib/NangateOpenCellLibrary_typical.lib}
read_db {/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/rq1_completion_v1_20260917/rq1_sanger_threshold/round_05/build_01/hammer/par-rundir/pre_clock_tree_resize}
read_sdc {/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/rq1_completion_v1_20260917/rq1_sanger_threshold/round_05/build_01/hammer/par-rundir/clock_constraints_fragment.sdc}
read_sdc {/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/rq1_completion_v1_20260917/rq1_sanger_threshold/round_05/build_01/hammer/par-rundir/pin_constraints_fragment.sdc}
source {/scratch/gz2522/gz2522/tmp/micro-hackthon/pdk/hammer45/setRC.tcl}
set_input_delay 1.0 -clock clock [all_inputs -no_clocks]
set_output_delay 1.0 -clock clock [all_outputs]
set_load 5.0 [all_outputs]
set_propagated_clock [all_clocks]
estimate_parasitics -placement
set_dont_use {}
set_placement_padding -global -left 1 -right 1
puts FAST_PROBE_BEFORE
report_worst_slack -max -digits 8
help repair_timing
repair_timing -setup -setup_margin 0.05
puts FAST_PROBE_AFTER
report_worst_slack -max -digits 8
write_db {/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/rq1_completion_ppa_diagnostics/sanger_r5_repair_control4/after_repair.odb}
exit

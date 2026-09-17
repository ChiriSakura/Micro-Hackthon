define_corners setup hold
read_liberty -corner setup {/scratch/gz2522/gz2522/tmp/micro-hackthon/pdk/hammer45/lib/NangateOpenCellLibrary_typical.lib}
read_liberty -corner hold {/scratch/gz2522/gz2522/tmp/micro-hackthon/pdk/hammer45/lib/NangateOpenCellLibrary_typical.lib}
read_db {/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/rq1_completion_v1_20260917/rq1_sanger_threshold/round_04/build_02/hammer/par-rundir/routed.odb}
read_sdc {/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/rq1_completion_v1_20260917/rq1_sanger_threshold/round_04/build_02/hammer/par-rundir/clock_constraints_fragment.sdc}
read_sdc {/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/rq1_completion_v1_20260917/rq1_sanger_threshold/round_04/build_02/hammer/par-rundir/pin_constraints_fragment.sdc}
source {/scratch/gz2522/gz2522/tmp/micro-hackthon/pdk/hammer45/setRC.tcl}
set_input_delay 1.0 -clock clock [all_inputs -no_clocks]
set_output_delay 1.0 -clock clock [all_outputs]
set_load 5.0 [all_outputs]
set_propagated_clock [all_clocks]
read_spef -corner setup {/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/rq1_completion_v1_20260917/rq1_sanger_threshold/round_04/build_02/hammer/par-rundir/rq1_sanger_threshold_top.par.spef}
read_spef -corner hold {/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/rq1_completion_v1_20260917/rq1_sanger_threshold/round_04/build_02/hammer/par-rundir/rq1_sanger_threshold_top.par.spef}
report_worst_slack -max -digits 8
report_worst_slack -min -digits 8
report_checks -sort_by_slack -path_delay max -corner setup -group_count 3 -digits 8 -fields {slew cap input nets fanout}
exit

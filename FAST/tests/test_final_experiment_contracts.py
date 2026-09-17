from fast.agents.codesign import CoDesignPoint, to_schedule
from fast.adapters.timing import TimingResult


def test_exported_schedule_preserves_searched_hardware():
    p = CoDesignPoint(tile_q=32, tile_k=32, tile_d=64, parallelism=8,
                      double_buffer=False, num_rows=16, pe_per_row=8,
                      reg_width=16, data_width=16, sram_bytes=131072,
                      queue_depth=4, divider_stages=12, bank_count=16)
    s = to_schedule(p, (), .8, block_m=32, kept_per_block=8)
    for key in ('num_rows', 'pe_per_row', 'reg_width', 'data_width', 'sram_bytes',
                'queue_depth', 'divider_stages', 'bank_count'):
        assert getattr(s, key) == getattr(p, key)
    assert (s.block_m, s.kept_per_block) == (32, 8)


def test_arrival_below_period_does_not_imply_timing_closure():
    t = TimingResult(success=True, top_module='X', technology='test',
                     clock_period_ns=2.0, critical_path_ns=1.99, slack_ns=-.03)
    assert t.max_frequency_mhz < 500


def test_banked_memory_preserves_depth_when_macros_are_wider():
    from scripts.run_final_inventory import banked_memory
    m = banked_memory({'bank_count':16, 'data_width':16, 'sram_bytes':131072})
    assert m['logical_depth_per_bank'] == 4096
    assert m['deep_per_bank'] * m['macro_depth'] >= 4096
    assert m['across_per_bank'] * m['macro_width'] >= 16
    assert m['macros'] == 16 * m['deep_per_bank'] * m['across_per_bank']


def test_heldout_failure_cannot_select_another_algorithm():
    from scripts.select_confirmed_candidate import select
    a = dict(label='xm:16:8:32:0.75:0.05',calibration={'relative_ppl_loss':.02},heldout={'relative_ppl_loss':.08})
    b = dict(label='xm:32:8:32:1.5:0.05',calibration={'relative_ppl_loss':.01},heldout={'relative_ppl_loss':.01})
    assert select([a,b]) == a

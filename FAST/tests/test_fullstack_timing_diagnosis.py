"""STA feedback parser tests with synthetic reports, not physical evidence."""
from fast.fullstack.physical import extract_timing_diagnosis


def test_extracts_reported_endpoint_nets_without_guessing_an_operator():
    log = '''old output
FAST_CRITICAL_PATHS_BEGIN
Startpoint: _10_ (rising edge-triggered flip-flop clocked by clock)
Endpoint: _20_ (rising edge-triggered flip-flop clocked by clock)
Path Type: max
 -1.80 slack (VIOLATED)
FAST_CRITICAL_PATHS_END
'''
    netlist = 'DFF_X2 _10_ (.D(a), .CK(clock), .Q(scores_reg_0));\nDFF_X1 _20_ (.D(b), .CK(clock), .Q(h_reg));'
    result = extract_timing_diagnosis(log, netlist)
    assert result['paths'][0]['startpoint'] == '_10_'
    assert 'scores_reg_0' in result['paths'][0]['start_cell']
    assert 'h_reg' in result['paths'][0]['end_cell']
    assert 'h_reg' in result['endpoint_mapping']
    assert '-1.80 slack (VIOLATED)' in result['report_excerpt']
    assert extract_timing_diagnosis('report missing', netlist) is None


def test_port_endpoint_remains_unmapped_and_latest_report_is_used():
    log = 'FAST_CRITICAL_PATHS_BEGIN\nStartpoint: obsolete\nEndpoint: obsolete\nFAST_CRITICAL_PATHS_END\n'
    log += '\x1b[37mFAST_CRITICAL_PATHS_BEGIN\nStartpoint: input_a\nEndpoint: output_z\nFAST_CRITICAL_PATHS_END\x1b[0m'
    result = extract_timing_diagnosis(log, '')
    assert result['paths'] == [{'startpoint': 'input_a', 'endpoint': 'output_z', 'start_cell': None, 'end_cell': None}]

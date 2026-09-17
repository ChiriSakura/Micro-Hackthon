"""A tool timeout must retain logs and terminate its child process group."""
import time

from fast.fullstack.tools import RtlTools


def test_timeout_retains_output_and_stops_descendant(tmp_path):
    marker = tmp_path/'escaped_child'
    # /bin/sh avoids Python environment startup latency on the shared filesystem.
    parent = 'echo before-timeout; (sleep 2; echo escaped > "$1") & wait'
    tools = RtlTools(tmp_path, timeout=.5)
    result = tools.command(['/bin/sh', '-c', parent, 'timeout-test', str(marker)], tmp_path, tmp_path/'tool.log')
    assert result['timed_out'] and not result['passed']
    assert 'before-timeout' in (tmp_path/'tool.log').read_text()
    time.sleep(2.1)
    assert not marker.exists()

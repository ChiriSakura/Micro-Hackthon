#!/usr/bin/env python3
"""Probe immutable third-party IP, separately from any generated FAST design."""
import argparse
import json
import os
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fast.fullstack.library import save
from fast.fullstack.tools import RtlTools


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--tool-root', type=Path, required=True)
    args = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    work = args.output.resolve(); work.mkdir(parents=True, exist_ok=False)
    inventory = json.loads((root / 'libraries/third_party/manifest.json').read_text())
    repo = lambda name: root / inventory[name]['local_directory']
    tools = RtlTools(args.tool_root, 900)
    results = {'scope': 'upstream component probes only, NOT generated RQ1 E2E or PPA', 'checks': {}}
    def record(name, checked):
        results['checks'][name] = checked
        save(work / 'summary.json', results)
    def verify(name, sources, tb, cases):
        dest = work / name; dest.mkdir()
        checked = tools.verify(None, sources, {'testbench': tb, 'expected_cases': cases, 'coverage': name}, dest)
        record(name, checked)
    rng = random.Random(913)
    packed = lambda xs, w: sum((x & ((1 << w)-1)) << (w*i) for i, x in enumerate(xs))
    # Independent software sort -> unmodified upstream comparator network.
    cases = [[-256,255,0,-1,1,5,-5,17], [7]*8, list(range(8)), list(reversed(range(8)))]
    cases += [[rng.randrange(-256,256) for _ in range(8)] for _ in range(96)]
    for pipeline in (0, 1):
        latency = 0 if pipeline == 0 else 6
        commands = [f"a=72'h{packed(v,9):x}; " + (f'repeat({latency}) begin @(posedge clk); #1; end ' if latency else '#1; ') +
                    f"if(z !== 72'h{packed(sorted(v,reverse=True),9):x}) $fatal(1,\"sort case {i}\"); " +
                    '$display("FAST_CASE cycles=1"); @(negedge clk);' for i,v in enumerate(cases)]
        tb = f'''module FASTTestbench;
reg clk=0; always #5 clk=~clk;
reg [71:0] a=0; wire [71:0] z;
bitonic_sort #(.DATA_WIDTH(9),.CHAN_NUM(8),.DIR(1),.SIGNED(1),.PIPE_REG({pipeline})) dut(clk,a,z);
initial begin @(negedge clk);
{chr(10).join(commands)}
$display("FAST_PASS cases=100");$finish;end
endmodule
'''
        verify('bitonic_signed8_pipeline_' + str(pipeline), sorted((repo('bitonic_sorter')/'hdl/basic').glob('*.v')), tb, 100)
    # Entire FlexCiM publication bundle: lint records defects without rewriting it.
    dest = work / 'flexcim_lint'; dest.mkdir()
    record('flexcim_full_bundle_lint', tools.command(tools.verilator() + ['--lint-only', '--language', '1800-2017',
        '-Wno-fatal', '--top-module', 'flexcim', *map(str, sorted((repo('flexcim')/'hw').glob('*.v')))], dest, dest/'lint.log'))
    commands = []
    for i in range(100):
        data = [rng.randrange(256) for _ in range(16)]
        first = [rng.randrange(4) for _ in range(4)]; second = [rng.randrange(4) for _ in range(4)]
        want = [data[4*second[j]+first[second[j]]] for j in range(4)]
        commands.append(f"a=128'h{packed(data,8):x}; sel=16'h{packed(first+second,2):x}; valid={i%2}; #1; "
                        f"if(z !== 32'h{packed(want,8):x} || ov !== valid) $fatal(1,\"distribution {i}\"); $display(\"FAST_CASE cycles=1\");")
    tb = '''module FASTTestbench;
reg [127:0] a=0; reg [15:0] sel=0; reg valid=0; wire ov; wire [31:0] z;
distribution #(.DATA_WIDTH(8),.NUM_INPUT_DATA(4),.NUM_SUB_MACROS(4)) dut(
 .clk(1'b0),.rst_n(1'b1),.i_valid(valid),.i_data_bus(a),.i_en(1'b1),.i_sparse_select(sel),.o_valid(ov),.o_data_bus(z));
initial begin
''' + '\n'.join(commands) + '\n$display("FAST_PASS cases=100");$finish;end\nendmodule\n'
    verify('flexcim_distribution', [repo('flexcim')/'hw/distribution.v'], tb, 100)
    env = dict(os.environ)
    env['COURSIER_CACHE'] = str(args.tool_root/'cache/coursier')
    env['SCALA_CLI_HOME'] = str(args.tool_root/'cache/scala-cli')
    for name, sources, tops in [
        ('sanger_elaboration', sorted((repo('sanger')/'hardware/src/main/scala').rglob('*.scala')),
         ['new pe_row.Pack(8,4,4,3,3,8)', 'new pe_row.Dense_PE_Array(20,8,0,11,8,8)',
          'new pe_row.Sparse_PE_Array(4,32,16,8,8,4,4,4)']),
        ('legacy_topk_elaboration', [root/'hardware/chisel/src/main/scala/predict_unit/topk.scala'],
         ['new predict_unit.TopK(8,7,16,0)'])]:
        dest = work / name; dest.mkdir()
        driver = dest/'Probe.scala'
        driver.write_text('''//> using scala "2.13.12"
//> using dep "edu.berkeley.cs::chisel3:3.6.1"
//> using plugin "edu.berkeley.cs:::chisel3-plugin:3.6.1"
import chisel3.stage.ChiselStage
object Probe extends App {
''' + '\n'.join(f'(new ChiselStage).emitVerilog({top}, Array("--target-dir", args(0)))' for top in tops) + '\n}\n')
        checked = tools.command([str(args.tool_root/'tools/scala-cli'), 'run', *map(str,sources), str(driver),
            '--workspace', str(dest/'scala_build'), '--server=false', '--main-class', 'Probe', '--', str(dest/'emitted')],
            dest, dest/'elaboration.log', env=env)
        record(name, checked)
    emitted = work/'legacy_topk_elaboration/emitted/TopK.v'
    if emitted.exists():
        ports = ','.join(f'.io_idx_{i}(idx[{3*i}+:3]),.io_idxValid_{i}(vld[{i}])' for i in range(7))
        values = [4,8,1,7,2,6,3,5]
        commands = '\n'.join(f'tick(1,16\'d{x});' for x in values) + '\nrepeat(8) tick(0,0);'
        checks = '\n'.join(f'if(vld[{i}]) begin if(cycles!={8+i} || idx[{3*i}+:3]!={values.index(8-i)}) $fatal(1,"rank {i} timing/index"); hits=hits+1; $display("RANK {i} cycle=%0d",cycles); end' for i in range(7))
        tb = f'''module FASTTestbench;
reg clock=0; always #5 clock=~clock;
reg reset=1,en=0;reg [15:0] data=0;wire [20:0] idx;wire [6:0] vld;
TopK dut(.clock(clock),.reset(reset),.io_enable(en),.io_inData(data),{ports});
integer cycles=0,hits=0;
task tick(input integer enable,input [15:0] value);begin
 @(negedge clock); en=enable;data=value; @(posedge clock); #1;cycles=cycles+1;
 {checks}
end endtask
initial begin repeat(3) @(negedge clock);reset=0;
{commands}
if(hits!=7) $fatal(1,"missing ranks");
$display("FAST_CASE cycles=14");$display("FAST_PASS cases=1");$finish;end
endmodule
'''
        verify('legacy_topk_8_7_latency', [emitted], tb, 1)
    print(json.dumps({name: r['passed'] for name,r in results['checks'].items()}))


if __name__ == '__main__':
    main()

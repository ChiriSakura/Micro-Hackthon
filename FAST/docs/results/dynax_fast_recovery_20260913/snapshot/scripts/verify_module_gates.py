#!/usr/bin/env python3
"""Real-tool regression: reject a lint-clean arithmetic error, then accept its repair."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fast.fullstack.contracts import Module, Port
from fast.fullstack.behavior import compile_tests
from fast.fullstack.library import save
from fast.fullstack.tools import RtlTools, check_source


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    tools=RtlTools(args.tool_root)
    combinational=Module('Increment','unsigned increment',(Port('a','input',4),Port('b','output',5)),(),'',
        tests=({'name':'bounds','steps':[{'inputs':{'a':0},'expected':{'b':1}},
                                        {'inputs':{'a':15},'expected':{'b':16}}]},))
    registered=Module('Register','synchronous reset',(Port('clock','input',1),Port('reset','input',1),
        Port('a','input',4),Port('b','output',4)),(),'',tests=({'name':'reset_and_capture','steps':[
            {'inputs':{'reset':1,'a':15},'cycles':1,'expected':{'b':0}},
            {'inputs':{'reset':0,'a':15},'cycles':1,'expected':{'b':15}},
            {'inputs':{'a':0},'cycles':1,'expected':{'b':0}}]},))
    cases=[('wrong',combinational,'module Increment(input [3:0] a, output [4:0] b); assign b=a; endmodule'),
           ('repaired',combinational,"module Increment(input [3:0] a, output [4:0] b); assign b={1'b0,a}+5'd1; endmodule"),
           ('registered',registered,'module Register(input clock, input reset, input [3:0] a, output reg [3:0] b); always @(posedge clock) if(reset) b<=0; else b<=a; endmodule')]
    ports=(Port('clock','input',1),Port('reset','input',1),Port('iv','input',1),
           Port('a','input',4),Port('ov','output',1),Port('b','output',5))
    behavior={'latency':3,'reset':'reset','valid_input':'iv','valid_output':'ov',
              'outputs':{'b':'a+1'},'vectors':[{'a':0},{'a':15},{'a':7}]}
    pipe=Module('Pipe','three-register increment',ports,(),'',behavior=behavior,
                tests=tuple(compile_tests(ports,behavior)))
    pipe_source="""module Pipe(input clock,input reset,input iv,input [3:0] a,output ov,output [4:0] b);
reg v1,v2,v3; reg [4:0] d1,d2,d3;
always @(posedge clock) begin
 if(reset) begin v1<=0;v2<=0;v3<=0;d1<=0;d2<=0;d3<=0;end
 else begin v1<=iv;v2<=v1;v3<=v2;d1<={1'b0,a}+5'd1;d2<=d1;d3<=d2;end
end
assign ov=v3; assign b=d3; endmodule"""
    cases.extend([('behavior_pipe',pipe,pipe_source),
                  ('wrong_latency',pipe,pipe_source.replace('ov=v3','ov=v2').replace('b=d3','b=d2'))])
    def execute(case):
        name,module,source=case
        work=args.output/name
        work.mkdir()
        path=work/f'{module.name}.v';path.write_text(source)
        check_source(source,module)
        result=tools.module(module,[path.resolve()],work.resolve())
        save(work/'result.json',{'module':asdict(module),'gate':result})
        return name,result
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=dict(pool.map(execute,cases))
    passed=(not results['wrong']['passed'] and results['wrong'].get('functional',{}).get('stage')=='simulation'
            and results['repaired']['passed'] and results['registered']['passed']
            and results['behavior_pipe']['passed'] and not results['wrong_latency']['passed']
            and results['wrong_latency'].get('functional',{}).get('stage')=='simulation')
    save(args.output/'summary.json',{'passed':passed,'llm_calls':0,
        'scope':'real Verilator gate regression with handwritten fixtures, not autonomous generation or PPA',
        'results':results})
    print(f'module gate regression passed={passed}')
    return 0 if passed else 1


if __name__=='__main__':
    raise SystemExit(main())

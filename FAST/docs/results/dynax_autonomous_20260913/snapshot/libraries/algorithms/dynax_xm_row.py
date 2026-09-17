"""Bounded fixed-point X:M row contract, derived from DynaX's is_quant=False path.

Not a whole-model or low-precision-predictor implementation. Arithmetic and tie
refinements are explicit, and are audited separately against actual DynaX Python.
"""
import math
import random


EXP = tuple(round(65535 * math.exp(-i/16)) for i in range(256))
EXP_PACKED = sum(x << (16*i) for i,x in enumerate(EXP))


def trunc(n, d):
    return (1 if n >= 0 else -1) * (abs(n)//d) if d else 0


def packed(values, bits):
    return sum((x & ((1 << bits)-1)) << (bits*i) for i,x in enumerate(values))


class DynaxXMRow:
    def describe(self):
        ports = [('clock','input',1),('reset','input',1),('start','input',1),
                 ('q','input',8),('k','input',64),('v','input',64),
                 ('done','output',1),('result','output',16),('keep_mask','output',8)]
        return {'id':'dynax_xm_row',
            'semantics':('DynaX X:M attention, is_quant=False, bounded one-query integration contract. '
                '8 keys, head_dim=2, value_dim=1. q[2], k[8][2] signed 4-bit ticks Q*.2; '
                'v[8] signed 8-bit ticks Q*.4. scale_factor=1. All 8 keys visible (one decode row). '
                's[i]=q[0]*k[i][0]+q[1]*k[i][1], signed full precision; floating score=s[i]/16. '
                'h=max(s); e[i]=EXP[h-s[i]], where EXP[d]=round(65535*exp(-d/16)), EXACT table supplied. '
                'S=sum(e). Two contiguous blocks of m=4; B[b]=sum(e[4*b:4*b+4]). '
                'If 8*B[b] > t0_quarters*S keep n1=2; elif 8*B[b] < t1_quarters*S keep 0; else keep n2=1. '
                'Strict comparisons match DynaX (sum probability mass * sequence_length / m). '
                'Within each block choose highest signed score first, ties choose SMALLER original key index. '
                'keep_mask bit i marks selected key. Reuse e for selected weights; '
                'D=sum(e[i] for selected i), N=sum(e[i]*v[i] for selected i). '
                'result=trunc_toward_zero((N*16)/D), signed 16-bit Q*.8; D=0 =>0. '
                'This implements a declared LUT approximation of softmax, not exact float softmax. '
                'Tie rule is a deterministic refinement of torch.topk unspecified tie ordering. '
                'All scores, block masses and indices MUST be computed on chip from q/k/v; no external oracle ports.'),
            'config_space':{'t0_quarters':[5,6], 't1_quarters':[1,2]},
            'numeric_bounds':{'score_min':-112,'score_max':128,'exp_delta_max':240,
                              'exponent_max':65535,'all_weight_sum_max':524280,
                              'abs_weighted_value_sum_max':67107840,'abs_scaled_numerator_max':1073725440},
            'exp_table':list(EXP), 'exp_table_packed_hex':hex(EXP_PACKED),
            'exp_behavior_example':'lane('+hex(EXP_PACKED)+', delta, 16)',
            'ports':[{'name':n,'direction':d,'width':w} for n,d,w in ports],
            'protocol':('Synchronous active-high reset. Accept one-cycle start while idle. Inputs remain stable until done. '
                        'done is a one-cycle pulse within 1024 edges, result and keep_mask valid with done. '
                        'First capture edge counts as cycle 1. Repeated transactions without reset. '
                        'Pack q[d] at 4*d, k[i][d] at 4*(2*i+d), v[i] at 8*i, all two-complement bit patterns.')}

    def validate_config(self, config):
        if set(config) != {'t0_quarters','t1_quarters'} or any(type(v) is not int for v in config.values()):
            raise ValueError('Expected integer t0_quarters/t1_quarters')
        if config['t0_quarters'] not in (5,6) or config['t1_quarters'] not in (1,2):
            raise ValueError('Invalid X:M thresholds')

    def cases(self, seed, count):
        rng=random.Random(seed)
        cases=[([0,0],[[0,0]]*8,list(range(-4,4))),
               ([-8,-8],[[-8,-8]]*4+[[7,7]]*4,[-128]*4+[127]*4),
               ([7,-8],[[7,-8],[-8,7],[0,0],[1,1]]*2,list(range(-4,4))),
               ([4,0],[[i,0] for i in range(-4,4)],[0]*8)]
        cases.extend(([rng.randrange(-8,8) for _ in range(2)],
                      [[rng.randrange(-8,8) for _ in range(2)] for _ in range(8)],
                      [rng.randrange(-128,128) for _ in range(8)]) for _ in range(count))
        return cases

    def reference(self, config, case):
        q,k,v=case;s=[sum(a*b for a,b in zip(q,key)) for key in k]
        e=[EXP[max(s)-x] for x in s];total=sum(e);mask=0
        for b in range(2):
            indices=list(range(4*b,4*b+4));mass=sum(e[i] for i in indices)
            keep=2 if 8*mass > config['t0_quarters']*total else (0 if 8*mass < config['t1_quarters']*total else 1)
            for i in sorted(indices,key=lambda i:(-s[i],i))[:keep]:mask |= 1 << i
        denom=sum(e[i] for i in range(8) if mask >> i & 1)
        numer=sum(e[i]*v[i] for i in range(8) if mask >> i & 1)
        return {'result':trunc(numer*16,denom),'keep_mask':mask,'scores':s,'weights':e}

    def profile(self, config, seed):
        self.validate_config(config);cases=self.cases(seed,256);error=0;hist={str(i):0 for i in range(9)}
        for case in cases:
            r=self.reference(config,case);v=case[2];s=r['scores'];e=[math.exp((x-max(s))/16) for x in s]
            dense=sum(a*b for a,b in zip(e,v))*16/sum(e)
            error += abs(r['result']-dense)/2048
            hist[str(r['keep_mask'].bit_count())] += 1
        return {'config':config,'quality_loss':error/len(cases),
                'quality_metric':'mean absolute Q8 output error / 2048 versus floating dense attention on same quantized inputs',
                'quality_scope':'260 synthetic decode-row queries; no model perplexity',
                'sparsity':1-sum(int(k)*v for k,v in hist.items())/(8*len(cases)),
                'active_keys_histogram':hist,'samples':len(cases),'seed':seed}

    def verification(self, config, seed, top):
        self.validate_config(config);cases=self.cases(seed ^ 0x5A17,96)
        vectors=[{'q':packed(q,4),'k':packed([x for row in k for x in row],4),'v':packed(v,8),
                  **{n:x for n,x in self.reference(config,(q,k,v)).items() if n in ('result','keep_mask')}} for q,k,v in cases]
        commands=[]
        for i,c in enumerate(vectors):
            commands.append(f"run_case(8'h{c['q']:x},64'h{c['k']:x},64'h{c['v']:x},16'h{c['result']&65535:x},8'h{c['keep_mask']:x},{i});")
            if i==49:commands.append('@(negedge clock); reset=1; repeat(2) @(negedge clock); reset=0;')
        tb='''module FASTTestbench;
reg clock=0; always #5 clock=~clock;
reg reset=1, start=0; reg [7:0] q=0; reg [63:0] k=0,v=0;
wire done; wire [15:0] result; wire [7:0] keep_mask;
TOP dut(.clock(clock),.reset(reset),.start(start),.q(q),.k(k),.v(v),.done(done),.result(result),.keep_mask(keep_mask));
integer cycles;
task run_case(input [7:0] iq,input [63:0] ik,input [63:0] iv,input [15:0] want,input [7:0] mask,input integer idx);
begin
 @(negedge clock); q=iq;k=ik;v=iv;start=1;
 @(posedge clock); #1;cycles=1;
 @(negedge clock);start=0;
 while(!done && cycles<1024) begin @(posedge clock);#1;cycles=cycles+1;end
 if(!done) $fatal(1,"timeout case %0d",idx);
 if(result !== want || keep_mask !== mask) $fatal(1,"case %0d result=%0d expected=%0d mask=%h expected_mask=%h",idx,$signed(result),$signed(want),keep_mask,mask);
 $display("FAST_CASE cycles=%0d",cycles);
 @(posedge clock);#1;if(done) $fatal(1,"done must pulse");
end endtask
initial begin repeat(3) @(negedge clock);reset=0;
COMMANDS
$display("FAST_PASS cases=100");$finish;end
initial begin #2000000;$fatal(1,"global timeout");end
endmodule
'''.replace('TOP',top).replace('COMMANDS','\n'.join(commands))
        return {'vectors':vectors,'testbench':tb,'expected_cases':len(vectors),
                'coverage':'signed Q/K/V, two X:M blocks, zero/ties/extremes, mask AND numeric output, repeated transactions and reset; bit-exact declared LUT contract'}

"""RQ1 v1: four sparse softmax mechanisms on an identical bounded decode row.

This file is standalone because Library imports an immutable copy. No RTL,
microarchitecture, or previous generated design is supplied by this plugin.
"""
import hashlib
import json
import math
import random

EXP = tuple(round(65535 * math.exp(-i / 16)) for i in range(256))
EXP_PACKED = sum(x << (16 * i) for i, x in enumerate(EXP))
CALIBRATION_SEED = 20260915
CALIBRATION_COUNT = 2048
HOLDOUT_SEED = 20260916
HOLDOUT_COUNT = 4096


def packed(values, bits):
    return sum((x & ((1 << bits) - 1)) << (bits * i) for i, x in enumerate(values))


def trunc(n, d):
    return (1 if n >= 0 else -1) * (abs(n) // d) if d else 0


class SparseRow:
    def describe(self):
        ports = [('clock', 'input', 1), ('reset', 'input', 1), ('start', 'input', 1),
                 ('q', 'input', 8), ('k', 'input', 128), ('v', 'input', 128),
                 ('done', 'output', 1), ('result', 'output', 16), ('keep_mask', 'output', 16)]
        return {
            'id': self.name,
            'semantics': (
                'One fully visible decode row: 16 keys, head_dim=2, value_dim=1. '
                'q[2], k[16][2] signed 4-bit ticks Q*.2; v[16] signed 8-bit ticks Q*.4. '
                'Scale factor=1. s[i]=q[0]*k[i][0]+q[1]*k[i][1], signed full precision; '
                'floating score=s[i]/16. h=max(s); e[i]=EXP[h-s[i]], EXACT supplied LUT. '
                'EXP[d]=round(65535*exp(-d/16)); S=sum(e). ' + self.selection +
                ' All Top-k ties select SMALLER original key index. keep_mask bit i marks key i. '
                'D=sum(e[i] for selected i); N=sum(e[i]*v[i] for selected i). '
                'result=trunc_toward_zero((N*16)/D), signed 16-bit Q*.8; D=0 gives 0. '
                'Compute ALL scores, exponentials, selection and normalization on chip from Q/K/V. '
                'No oracle ports, host preprocessing, replacing softmax with raw scores, or changing math. '
                'This is a declared fixed-point approximation of a sparse attention mechanism, '
                'not a whole-model implementation or a reproduction of a paper accelerator.'),
            'config_space': self.space,
            'numeric_bounds': {'score_min': -112, 'score_max': 128, 'exp_delta_max': 240,
                'exponent_max': 65535, 'all_weight_sum_max': 1048560,
                'abs_weighted_value_sum_max': 134215680, 'abs_scaled_numerator_max': 2147450880},
            'exp_table': list(EXP), 'exp_table_packed_hex': hex(EXP_PACKED),
            'exp_behavior_example': 'lane(' + hex(EXP_PACKED) + ', delta, 16)',
            'ports': [{'name': n, 'direction': d, 'width': w} for n, d, w in ports],
            'protocol': ('Synchronous active-high reset. Accept one-cycle start while idle. '
                'Inputs remain stable until done. done is a one-cycle pulse within 1024 edges, '
                'result and keep_mask valid with done. First capture edge counts as cycle 1. '
                'Repeated transactions without reset. Pack q[d] at 4*d, k[i][d] at 4*(2*i+d), '
                'v[i] at 8*i; all two-complement bit patterns.')}

    def validate_config(self, config):
        if set(config) != set(self.space) or any(type(v) is not int or v not in self.space[k]
                                                for k, v in config.items()):
            raise ValueError('Configuration outside the frozen algorithm search space')

    def cases(self, seed, count):
        rng = random.Random(seed)
        cases = [([0, 0], [[0, 0]] * 16, list(range(-8, 8))),
                 ([-8, -8], [[-8, -8]] * 8 + [[7, 7]] * 8, [-128] * 8 + [127] * 8),
                 ([7, -8], [[7, -8], [-8, 7], [0, 0], [1, 1]] * 4, list(range(-8, 8))),
                 ([4, 0], [[i, 0] for i in range(-8, 8)], [0] * 16)]
        cases.extend(([rng.randrange(-8, 8) for _ in range(2)],
                      [[rng.randrange(-8, 8) for _ in range(2)] for _ in range(16)],
                      [rng.randrange(-128, 128) for _ in range(16)]) for _ in range(count))
        return cases

    def reference(self, config, case):
        self.validate_config(config)
        q, k, v = case
        s = [sum(a * b for a, b in zip(q, key)) for key in k]
        e = [EXP[max(s) - x] for x in s]
        selected = self.select(config, s, e)
        mask = sum(1 << i for i in selected)
        return {'result': trunc(16 * sum(e[i] * v[i] for i in selected), sum(e[i] for i in selected)),
                'keep_mask': mask, 'scores': s, 'weights': e}

    def measure(self, config, seed, count, *, boundaries=True):
        self.validate_config(config)
        cases = self.cases(seed, count)
        if not boundaries:
            cases = cases[4:]
        error = dense_energy = floor_error = 0.0
        hist = {str(i): 0 for i in range(17)}
        for case in cases:
            r = self.reference(config, case)
            v = case[2]
            scores = r['scores']
            weights = [math.exp((x - max(scores)) / 16) for x in scores]
            dense = 16 * sum(a * b for a, b in zip(weights, v)) / sum(weights)
            fixed_dense = trunc(16 * sum(a * b for a, b in zip(r['weights'], v)), sum(r['weights']))
            error += (r['result'] - dense) ** 2
            floor_error += (fixed_dense - dense) ** 2
            dense_energy += dense ** 2
            hist[str(r['keep_mask'].bit_count())] += 1
        relative = lambda value: math.sqrt(value / dense_energy) if dense_energy else (0.0 if value == 0 else float('inf'))
        return {'config': config, 'quality_loss': relative(error),
                'quality_metric': 'sqrt(sum((sparse_fixed_output-dense_float_output)^2)/sum(dense_float_output^2))',
                'quality_scope': 'synthetic quantized decode rows; NOT downstream model accuracy',
                'dense_fixedpoint_relative_rmse': relative(floor_error),
                'squared_error_sum': error, 'dense_squared_output_sum': dense_energy,
                'sparsity': 1 - sum(int(k) * v for k, v in hist.items()) / (16 * len(cases)),
                'fully_dense_query_fraction': hist['16'] / len(cases),
                'active_keys_histogram': hist, 'samples': len(cases), 'seed': seed,
                'includes_shared_boundary_cases': boundaries,
                'workload_sha256': hashlib.sha256(json.dumps(cases, separators=(',', ':')).encode()).hexdigest()}

    def profile(self, config, seed):
        # The flow seed controls implementation/test randomness, never which
        # quality workload an algorithm sees. Held-out data are not profiled.
        return self.measure(config, CALIBRATION_SEED, CALIBRATION_COUNT)


    def verification(self, config, seed, top):
        self.validate_config(config);cases=self.cases(seed ^ 0x5A17,96)
        vectors=[{'q':packed(q,4),'k':packed([x for row in k for x in row],4),'v':packed(v,8),
                  **{n:x for n,x in self.reference(config,(q,k,v)).items() if n in ('result','keep_mask')}} for q,k,v in cases]
        commands=[]
        for i,c in enumerate(vectors):
            commands.append(f"run_case(8'h{c['q']:x},128'h{c['k']:x},128'h{c['v']:x},16'h{c['result']&65535:x},16'h{c['keep_mask']:x},{i});")
            if i==49:commands.append('@(negedge clock); reset=1; repeat(2) @(negedge clock); reset=0;')
        tb='''module FASTTestbench;
reg clock=0; always #5 clock=~clock;
reg reset=1, start=0; reg [7:0] q=0; reg [127:0] k=0,v=0;
wire done; wire [15:0] result; wire [15:0] keep_mask;
TOP dut(.clock(clock),.reset(reset),.start(start),.q(q),.k(k),.v(v),.done(done),.result(result),.keep_mask(keep_mask));
integer cycles;
task run_case(input [7:0] iq,input [127:0] ik,input [127:0] iv,input [15:0] want,input [15:0] mask,input integer idx);
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
                'coverage':'signed Q/K/V, 16-key sparse row, zero/ties/extremes, mask AND numeric output, repeated transactions and reset; bit-exact declared LUT contract'}


class DynaxXM(SparseRow):
    name = 'rq1_dynax_xm'
    space = {'n1': [7, 8], 'n2': [4, 6, 7], 't0_quarters': [2, 4, 6], 't1_quarters': [0, 1]}
    selection = ('DynaX dynamic X:M: two contiguous m=8 blocks. For each block B=sum(e in block). '
                 'If 8*B > t0_quarters*S retain n1; elif 8*B < t1_quarters*S retain zero; '
                 'else retain n2. Retain highest signed scores within the block. '
                 'Threshold units are quarters: normalized mass is B/S * sequence_length/m = 2*B/S. ')

    def select(self, c, s, e):
        selected = []
        for b in (0, 8):
            mass, total = sum(e[b:b + 8]), sum(e)
            n = c['n1'] if 8 * mass > c['t0_quarters'] * total else (0 if 8 * mass < c['t1_quarters'] * total else c['n2'])
            selected.extend(sorted(range(b, b + 8), key=lambda i: (-s[i], i))[:n])
        return selected


class BlockNM(SparseRow):
    name = 'rq1_block_nm'
    space = {'n': [4, 5, 6, 7]}
    selection = 'Fixed N:M cardinality, dynamic indices: each contiguous m=8 block retains its n highest signed scores. '

    def select(self, c, s, e):
        return sum((sorted(range(b, b + 8), key=lambda i: (-s[i], i))[:c['n']] for b in (0, 8)), [])


class GlobalTopK(SparseRow):
    name = 'rq1_global_topk'
    space = {'k': [8, 10, 12, 14, 15]}
    selection = 'Global Top-k: retain exactly k highest signed scores across ALL 16 keys, without block quotas. '

    def select(self, c, s, e):
        return sorted(range(16), key=lambda i: (-s[i], i))[:c['k']]


class SangerThreshold(SparseRow):
    name = 'rq1_sanger_threshold'
    space = {'threshold_256': [1, 2, 3, 4, 6, 8]}
    selection = ('Sanger probability threshold mechanism: retain key i iff 256*e[i] > threshold_256*S '
                 '(strict >, NOT raw-score threshold). No fixed cardinality or block quota. ')

    def select(self, c, s, e):
        return [i for i in range(16) if 256 * e[i] > c['threshold_256'] * sum(e)]

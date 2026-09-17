"""Executable reference for a small, exact unsigned threshold-attention workload.

This is a framework integration workload, NOT DynaX or softmax attention.
All quality/reference/testbench generation is trusted library code.
"""
import random


class ThresholdAttention:
    def describe(self):
        return {
            'id': 'threshold_attention',
            'semantics': ('One query q[2], four keys k[4][2], four scalar values v[4], '
                'all unsigned 4-bit. score[i]=sum(q[d]*k[i][d]); '
                'weight[i]=score[i] if score[i]>=threshold else 0; '
                'result=floor(sum(weight[i]*v[i])/sum(weight[i])), or 0 if denominator=0. '
                'No softmax, no signed math. This is an integration workload, not DynaX.'),
            'config_space': {'threshold': [0, 64, 128, 192]},
            'numeric_bounds': {'score': 450, 'weight_sum': 1800, 'weighted_value_sum': 27000, 'result': 15},
            'ports': [
                {'name': 'clock', 'direction': 'input', 'width': 1},
                {'name': 'reset', 'direction': 'input', 'width': 1},
                {'name': 'start', 'direction': 'input', 'width': 1},
                {'name': 'q', 'direction': 'input', 'width': 8},
                {'name': 'k', 'direction': 'input', 'width': 32},
                {'name': 'v', 'direction': 'input', 'width': 16},
                {'name': 'done', 'direction': 'output', 'width': 1},
                {'name': 'result', 'direction': 'output', 'width': 4},
            ],
            'protocol': ('Synchronous active-high reset. Accept start on a rising edge while idle. '
                'Inputs held stable until done. done must pulse high for one cycle, within 128 cycles '
                'after acceptance; result valid with done. Support repeated transactions without reset. '
                'Pack q[d] at bits 4*d +:4, k[i][d] at 4*(2*i+d) +:4, v[i] at 4*i +:4. '
                'Measure latency from the start acceptance edge (completion on that edge counts as 1).'),
        }

    def validate_config(self, config):
        if set(config) != {'threshold'} or type(config['threshold']) is not int or config['threshold'] not in (0, 64, 128, 192):
            raise ValueError('Expected threshold in [0,64,128,192]')

    def cases(self, seed, count):
        rng = random.Random(seed)
        cases = [([0, 0], [[0, 0]]*4, [0]*4),
                 ([15, 15], [[15, 15]]*4, [15]*4),
                 ([8, 0], [[8, 0], [7, 0], [9, 0], [0, 0]], [1, 2, 14, 15]),
                 ([8, 8], [[8, 8], [12, 12], [0, 0], [1, 1]], [15, 1, 0, 3])]
        cases += [([rng.randrange(16) for _ in range(2)],
                   [[rng.randrange(16) for _ in range(2)] for _ in range(4)],
                   [rng.randrange(16) for _ in range(4)]) for _ in range(count)]
        return cases

    def reference(self, config, case):
        q, k, v = case
        scores = [sum(a*b for a,b in zip(q, key)) for key in k]
        weights = [s if s >= config['threshold'] else 0 for s in scores]
        denominator = sum(weights)
        return sum(w*x for w,x in zip(weights, v)) // denominator if denominator else 0

    def profile(self, config, seed):
        self.validate_config(config)
        cases = self.cases(seed, 256)
        active = [sum(sum(a*b for a,b in zip(q, key)) >= config['threshold']
                      and sum(a*b for a,b in zip(q, key)) != 0 for key in k) for q,k,v in cases]
        error = sum(abs(self.reference(config, c) - self.reference({'threshold': 0}, c)) / 15 for c in cases) / len(cases)
        histogram = {str(i): active.count(i) for i in range(5)}
        return {'config': config, 'quality_loss': error, 'quality_metric': 'mean absolute output error / 15 vs threshold=0',
                'quality_scope': '260 deterministic synthetic profiling queries; not model perplexity',
                'sparsity': 1 - sum(active)/(4*len(cases)), 'active_keys_histogram': histogram,
                'samples': len(cases), 'seed': seed}

    def verification(self, config, seed, top):
        # Different seed/distribution from Kernel profiling; expected values never come from RTL/LLM.
        cases = self.cases(seed ^ 0x5A17, 96)
        def pack(xs):
            return sum(x << (4*i) for i,x in enumerate(xs))
        vectors = [{'q': pack(q), 'k': pack([x for key in k for x in key]), 'v': pack(v),
                    'expected': self.reference(config, (q,k,v))} for q,k,v in cases]
        commands = []
        for i, case in enumerate(vectors):
            commands.append(f"run_case(8'd{case['q']},32'd{case['k']},16'd{case['v']},4'd{case['expected']},{i});")
            if i == len(vectors)//2:
                commands.append('@(negedge clock); reset=1; repeat(2) @(negedge clock); reset=0;')
        tb = '''module FASTTestbench;
reg clock=0; always #5 clock=~clock;
reg reset=1, start=0;
reg [7:0] q=0; reg [31:0] k=0; reg [15:0] v=0;
wire done; wire [3:0] result;
TOP dut(.clock(clock),.reset(reset),.start(start),.q(q),.k(k),.v(v),.done(done),.result(result));
integer cycles;
task run_case(input [7:0] iq,input [31:0] ik,input [15:0] iv,input [3:0] expected,input integer idx);
begin
 @(negedge clock); q=iq; k=ik; v=iv; start=1;
 @(posedge clock); #1; cycles=1;
 @(negedge clock); start=0;
 while (!done && cycles<128) begin @(posedge clock); #1; cycles=cycles+1; end
 if (!done) $fatal(1,"timeout case %0d",idx);
 if (result !== expected) $fatal(1,"mismatch case %0d actual=%0d expected=%0d",idx,result,expected);
 $display("FAST_CASE cycles=%0d",cycles);
 @(posedge clock); #1;
 if (done) $fatal(1,"done must be a one-cycle pulse");
end endtask
initial begin
 repeat(3) @(negedge clock); reset=0;
 COMMANDS
 $display("FAST_PASS cases=COUNT"); $finish;
end
initial begin #200000; $fatal(1,"global timeout"); end
endmodule
'''.replace('TOP',top).replace('COMMANDS','\n '.join(commands)).replace('COUNT',str(len(vectors)))
        return {'vectors': vectors, 'testbench': tb, 'expected_cases': len(vectors),
                'coverage': '100 integer-reference queries, threshold boundaries, all-zero/max, repeated transactions, mid-run reset'}

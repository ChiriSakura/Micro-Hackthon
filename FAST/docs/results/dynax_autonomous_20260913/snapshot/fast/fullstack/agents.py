"""Five distinct roles; all raw requests/replies are recorded before parsing."""
from __future__ import annotations

import json
from pathlib import Path
import time

from .library import save


class JsonAgent:
    def __init__(self, llm, role: str, audit: Path):
        self.llm, self.role, self.audit = llm, role, audit
        self.calls = 0

    def ask(self, instruction: str, context: dict) -> dict:
        self.calls += 1
        path = self.audit / self.role / f'{self.calls:04d}.json'
        prompt = (f'You are FAST {self.role} Agent. Return exactly one JSON object, no markdown.\n'
                  + instruction + '\nCONTEXT:\n' + json.dumps(context, ensure_ascii=False))
        record = {'role': self.role, 'prompt': prompt, 'started_unix': time.time()}
        save(path, record)
        try:
            reply = self.llm.prompt(prompt)
            record.update(response=reply.result, success=reply.success, stderr=reply.stderr,
                          wall_seconds=time.time()-record['started_unix'])
            save(path, record)
            if not reply.success:
                raise ValueError(f'{self.role} LLM failed: {reply.stderr}')
            body = reply.result.strip()
            if body.startswith('```'):
                body = body.split('\n', 1)[1].rsplit('```', 1)[0].strip()
            result = json.loads(body)
            if not isinstance(result, dict):
                raise ValueError('Expected a JSON object')
            return result
        except Exception as exc:
            record['error'] = f'{type(exc).__name__}: {exc}'
            save(path, record)
            raise


class KernelAgent(JsonAgent):
    def run(self, context):
        return self.ask('Select a legal algorithm configuration from config_space using the task prompt and measured_config_profiles. '
            'Do not change the specified algorithm. Return {"config": {...}, "rationale": "..."}. '
            'The trusted plugin will execute profiling and measure quality/sparsity; never invent measurements.', context)


class CompilerAgent(JsonAgent):
    def run(self, context):
        if not context.get('library_read_completed'):
            return self.ask('This is the library selection phase, before system planning. '
                'Inspect hardware_catalog and select the relevant reference code for the task. '
                'Return ONLY {"read_templates":["catalog_id"]}; use [] if none is appropriate. '
                'Do not return a system plan or simulate tool results. The actual code will be supplied '
                'on the next call, when you will design and assign module-specific references.', context)
        return self.ask('Design a COMPLETE synthesizable RTL system for the specified algorithm contract. '
            'The context config is the AUTHORITATIVE Kernel-approved algorithm configuration. '
            'Critic suggestions are advisory and may have been rejected for quality; NEVER implement a '
            'different parameter value mentioned in critic.reason, history, old plans or reference code. '
            'Choose decomposition, dataflow, scheduling, buffer organization and numeric widths. '
            'Library retrieval is complete. reference_code contains the actual code you requested. '
            'Return ONLY one final system-plan object. Do not output or echo read_templates or any other object. '
            'If rejected_plan is supplied, repair that plan using response_errors; preserve already valid contracts. '
            'If plan_awaiting_reference_review is supplied, its interfaces and behavior have already validated; '
            'review the newly supplied reference code and preserve that plan unless a concrete incompatibility requires a change. '
            'The modules array MUST include the top wrapper entry as well as all non-top modules. '
            'Do not put top ports or top implementation in a separate top-level field. '
            'Assign reference_ids separately for each module. '
            'reference_tests contains the frozen golden models and testbench examples associated with those IDs. '
            'Read them when planning numeric formats, reset, latency, valid timing and corner cases. '
            'In each design_prompt explain which tests apply, how ports/widths/signedness differ, and '
            'which additional behavior vectors cover your adaptation. Existing C++ tests are guidance, not '
            'automatically compatible or executed against a new interface. Never weaken the independent algorithm E2E. '
            'Assign only IDs you have read; UArch receives only the references you bind to its module. '
            'Use [] only when no supplied template is appropriate and explain the from-scratch design. '
            'Reference templates are read-only examples; you may design new modules and topology. '
            'reference_support_code contains the frozen dependency closure for full design bundles. '
            'PREFER preserving compatible existing library modules and their native Module/Bundle/FixedPoint '
            'interfaces inside thin generated adapters. To compile a reference bundle unchanged, assign '
            'linked_reference_ids:["catalog_id"] on that module (must be a subset of its reference_ids). '
            'The runner links those original read-only Scala files and their support_sources. '
            'hardware_catalog.native_library_symbols lists classes/packages available for such linking. '
            'The generated adapter can instantiate these parameterized native classes and connect their '
            'original io Bundle, converting widths/FixedPoint formats only at the boundary. '
            'Do not paste or rewrite the linked library class. You still own and generate the new adapter, '
            'connections, control and any algorithm-specific missing pieces. Old full-system references '
            'may have external scores/masses or approximate math: respect their documented limitations. '
            'Unlinked references are guidance only: inline their logic or declare separately generated children. '
            'Reference numeric formats may differ: explicitly account for unsigned/signed ranges, binary '
            'points, carry growth and zero-extension when adapting them to the task numeric bounds. '
            'Choose language chisel or verilog; obey task.hdl when not auto. Chisel backend is Scala 2.13.12/Chisel 3.6.1; '
            'Verilog backend is Verilog-2005. No external IP or blackboxes. Every dependency is a child module '
            'that must be instantiated; every module must be reachable from top. Use a few well-defined modules. '
            'All top ports must EXACTLY match algorithm ports. Declare each port separately with concrete numeric widths. '
            'Specify concrete child connections/protocol and cycle timing in implementation. '
            'You are the planner: prepare a separate design_prompt for EVERY module before dispatch. '
            'Independent non-top modules have isolated UArch sessions; task.module_workers controls concurrency. '
            'The top is reserved for a SEPARATE assembly UArch after all non-top modules pass. '
            'Make the top an integration/control wrapper around the planned compute modules. '
            'For EVERY non-top module supply an executable behavior contract instead of handwritten expected values. '
            'Behavior is PURE INPUT/OUTPUT MATHEMATICS, independent of microarchitecture. Do not encode pipeline '
            'registers, per-stage states, or partial hardware iterations in it. For an unsigned divider, use '
            'outputs:{"quot":"0 if denom == 0 else numer // denom"}; the same expression applies whether the '
            'hardware is combinational, pipelined or uses radix-2 logic. Only latency describes the timing. '
            'Return tests:[]; the runner computes and freezes numerical and cycle expectations before UArch starts. '
            'behavior={"test_generation_version":2,"latency":0,"let":{},"outputs":{"out":"expression"},'
            '"vectors":[{"in":0},{"in":1},{"in":15}]}. Set test_generation_version=2 for new contracts: '
            'the runner adds legal packed-lane signed minimum/maximum combinations to the frozen tests. '
            'Include explicit corner vectors for extreme signed dot products (e.g. both products positive '
            'at the signed minimum inputs), tie-breaking, and pipeline valid alignment. '
            'Expressions use input names, integer literals (decimal or 0x hex), + - * // % & | ^ << >>, comparisons, '
            'and/or/not, conditional a if condition else b, lane(word,index,width), pack(lane_width,low_lane,...,high_lane), '
            'The FIRST argument to pack/spack is the width of EACH LANE, never the total packed port width. '
            'For N lanes of W bits the port width is N*W: two signed 4-bit values in an 8-bit port use '
            'spack(4,-8,7), NEVER spack(8,-8,7). Eight 9-bit scores in a 72-bit port use spack(9,...), '
            'eight 16-bit weights in 128 bits use pack(16,...), and eight 8-bit values in 64 bits use spack(8,...). '
            'spack(width,signed_low_lane,...), signed(word,width), trunc_div(n,d), abs/min/max. '
            'trunc_div implements signed division TOWARD ZERO and returns zero for a zero denominator. '
            'Python-style // rounds negative quotients DOWN, so it is wrong for a signed hardware divider. '
            'For (signed numerator * 16)/unsigned denominator use '
            'trunc_div(signed(numerator,27)*16, denominator), with the actual declared numerator width. '
            'For SIGNED modules ports still carry unsigned bit patterns: decode signed(a,8) or signed(lane(p,i,8),8). '
            'Use spack for negative constant lanes, e.g. spack(4,-8,7) produces an 8-bit word. '
            'A scalar negative vector must be encoded, e.g. "(-100) & 0xffffffff" for a 32-bit input. '
            'NEVER guess a packed decimal value; use pack/spack with exactly the declared lane count and width. '
            'No arbitrary Python, attributes, strings inside expressions, loops or comprehensions. '
            'let is an ordered map of at most 256 intermediate expressions; outputs maps EVERY data output to an expression. '
            'Final outputs are masked to their port width, modeling unsigned bit patterns. Guard division by zero explicitly. '
            'Combinational behavior has latency=0 and no clock, reset or valid metadata. '
            'For pipelined behavior choose latency=1..64 and ALSO specify reset, valid_input, valid_output port names. '
            'All three control inputs clock/reset/valid_input and valid_output must be one bit. '
            'It accepts ONE transaction on EVERY edge with valid_input=1; latency L means the output appears after '
            'L edges INCLUDING the capture edge (L=1 is one register). Reset clears all data outputs and validity to zero. '
            'Do not hide extra capture/output registers outside that latency. All data registers and intermediate '
            'pipeline registers must clear on reset. Data when out_valid=0 is otherwise unspecified. '
            'The runner generates reset, isolated pulses, back-to-back traffic, bubbles and full pipeline drain tests. '
            'vectors contains 3..12 input maps initializing ALL data inputs, excluding clock/reset/valid. '
            'Values can be integers or CONSTANT expressions like "pack(9,60,70,80,90)"; use pack rather than guessing '
            'large packed decimals. NO expected fields. Include zero, maximum legal values and ordinary nonzero values. '
            'Runner adds 12 reproducible random vectors within optional input_bounds={"port":[min,max]} and '
            'input_condition="predicate over data inputs". These must describe legitimate module preconditions, '
            'not exclude inconvenient tests. Equations and protocol must match the assigned implementation. '
            'Prefer a few simple, independently checkable arithmetic modules. Complex control belongs in the top wrapper. '
            'Address any UArch/verification feedback; do not change the algorithm math or trusted top contract. '
            'For Chisel, every named module is a zero-argument RawModule class, with individually named IO vals '
            '(no io Bundle prefix); explicitly plan clock/reset connections and use withClockAndReset for registers. '
            'Return {"language":"chisel|verilog", "top":"Name", "rationale":"...", "modules":[{"name":"...", "purpose":"...", '
            '"ports":[{"name":"...", "direction":"input|output", "width":1}], '
            '"dependencies":["Child"], "reference_ids":["catalog_id"], "linked_reference_ids":[], '
            '"implementation":"detailed architecture, arithmetic, connections, and how to adapt selected references", '
            '"design_prompt":"self-contained module assignment with function, protocol, timing and reference adaptation", '
            '"tests":[], "behavior":{"latency":0,"outputs":{"b":"a"},'
            '"vectors":[{"a":0},{"a":1},{"a":15}]}}]}. '
            'For top use tests:[] and behavior:null; its tests come from the trusted algorithm plugin.', context)



class CompilerDiagnosisAgent(JsonAgent):
    """Planner review of a failed assembly, before another implementation attempt."""
    def run(self, context):
        answer = self.ask('Diagnose the failed module or system assembly using the actual source, accepted child '
            'contracts, tool diagnostics and independent failing vector in context. You are the Compiler '
            'planner reviewing correctness, not the post-PPA optimization Critic. Do not write RTL or '
            'change tests, algorithm, config or accepted children. Trace the first observed failure '
            'through concrete expressions and cycle timing. Distinguish measured failure from hypotheses. '
            'A UArch replan_reason is an UNVERIFIED CLAIM. Check its arithmetic against computed_behavior_examples '
            'before accepting it. Signed ports use two\'s-complement bit patterns; a large positive encoded '
            'input is not automatically out of range. If the claim contradicts the computed examples, '
            'choose repair and explain the correct values to UArch, without changing the frozen tests. '
            'Audit arithmetic signedness and intermediate widths, lane packing, last-item accumulation, '
            'counter range/termination, reset and child valid latency. A k-bit counter cannot reach 2**k; '
            'Chisel dynamic shifts widen their result, so packed lanes need explicit slicing; UInt.asSInt '
            'does not zero-extend. Registers retain values without self-assignment. '
            'Both UInt and SInt + truncate carry to the operand width; a wider destination cannot recover '
            'that lost bit. Derive signed intermediate ranges from the failing input, including products '
            'of signed minima. Verilator runs here in two-state mode: do not assert X propagation merely '
            'because a data register lacks reset. Prove a concrete wrong value or valid/data misalignment. '
            'Passing sampled child tests is NOT proof of exhaustive correctness. Inspect child source '
            'for failures outside the sampled cases. If a previous diagnosis did not change the observed '
            'failure, explicitly reconsider it rather than repeating the same unsupported explanation. '
            'Return {"action":"repair|replan", "reason":"specific root-cause hypothesis", '
            '"evidence":["exact source expression or supplied diagnostic"], '
            '"instructions":"minimal concrete changes and checks for the assigned UArch"}. '
            'Choose repair when changes inside the assigned module suffice. Choose replan for a concrete '
            'defect in an immutable child IMPLEMENTATION, interface, or behavior: Compiler can dispatch a '
            'corrected child with stronger tests. Do not work around a known wrong child in the parent. '
            'Never claim verification passed.', context)
        if answer.get('action') not in ('repair', 'replan'):
            raise ValueError('Compiler diagnosis requires repair or replan')
        for key in ('reason', 'instructions'):
            if not isinstance(answer.get(key), str) or not answer[key].strip():
                raise ValueError(f'Compiler diagnosis requires {key}')
        if not isinstance(answer.get('evidence'), list) or not answer['evidence'] or any(
                not isinstance(e, str) or not e.strip() for e in answer['evidence']):
            raise ValueError('Compiler diagnosis requires source/diagnostic evidence')
        return answer


class UArchAgent(JsonAgent):
    def run(self, context):
        return self.ask('Implement exactly the requested module of the Compiler system plan. '
            'The context config is the authoritative algorithm configuration; stale Critic suggestions cannot override it. '
            'Follow compiler_prompt. You own only this module; accepted dependency sources are immutable. '
            'previous_failed_attempt, when present, is the rejected source and tool failure from the prior '
            'Compiler build. Diagnose and correct it under the CURRENT interface/math/timing contract; '
            'do not repeat the defect or treat that candidate as verified. '
            'Planner tests cannot be changed by you. If their expectations contradict the math or timing, request replanning. '
            'computed_behavior_examples are produced by the trusted DSL interpreter from the frozen behavior. '
            'Use their masked values, signed interpretations and arithmetic intermediates to check numerical claims '
            'before requesting a test change. An unsigned encoded value can represent a negative signed operand. '
            'If you conclude that a test expects the wrong result or wrong valid timing, return ONLY '
            '{"replan_reason":"identify test name/step, actual expected math or timing, and required correction"}. '
            'Do not submit another implementation you already know will fail the same inconsistent test. '
            'Return {"source":"complete module source in system_plan.language", "rationale":"..."}. '
            'If language is chisel: use only chisel3 imports, one zero-argument class with the exact module name '
            'extending RawModule; internal Bundle/Record helper types are allowed. Do not redefine child modules. '
            'If module.linked_reference_ids is nonempty, linked_library_symbols lists native classes that '
            'the runner compiles from the immutable reference bundle. PREFER instantiating those original '
            'classes with their native io Bundle and FixedPoint types inside your one generated RawModule '
            'adapter. You may import their listed packages. Never copy their class definitions into your file. '
            'For unlinked references, translate needed logic into the assigned RawModule or request planning '
            'of an explicit library link/generated child. Do not paste a second hardware class and add a wrapper. '
            'Use individually named IO vals (no io Bundle), Clock() for clock, Bool() for reset; '
            'use withClockAndReset(clock, reset) for ALL Reg/RegInit/RegNext/RegEnable creation and updates, '
            'RegEnable overloads are RegEnable(next, enable) and RegEnable(next, init, enable), '
            'with enable LAST in the three-argument form. For explicit reset and gating you may instead '
            'use RegInit(init) followed by when(enable) { reg := next }. '
            'and Module(new Child) for dependencies. Chisel UInt + truncates carry: use +& for widening sums '
            'and explicitly size each lane before packing with Cat. Assignment to a wider output does not '
            'recover carry bits lost inside intermediate expressions or concatenations. '
            'Dynamic shifts widen their result: slice each packed lane to its declared width BEFORE Cat. '
            'For a loop of N items, prove counter range and termination: compare the current index to N-1 '
            'or widen the increment before comparing to N. Include the final item in accumulators before '
            'starting a dependent operation. Review compiler_diagnosis when supplied; it is a hypothesis '
            'to check against the source and frozen tests, not permission to change the contract. '
            'UInt.asSInt reinterprets the top bit as a sign; for a nonnegative unsigned operand '
            'in signed arithmetic, prepend a zero bit before asSInt (for example Cat(0.U(1.W), weight).asSInt). '
            'For Enum destructuring, use lowercase state variable names. Registers retain their value '
            'when not assigned in a branch; do not misdiagnose this as an undriven combinational wire. '
            'No package declaration, standalone App/main, file/process/network APIs, BlackBox, inline Verilog, '
            'compiler directives, dontTouch, print, assertion, or unlisted external libraries. Registers and IO must be fully assigned. '
            'For Chisel combinational modules without a clock port, use only combinational hardware. '
            'For Verilog: '
            'Use synthesizable Verilog-2005, explicit ports exactly as specified; no includes, testbench, '
            'system tasks, initial blocks, blackboxes, external modules or preprocessor conditionals. '
            'Instantiate declared generated dependencies and, for Chisel, explicitly linked native library classes. '
            'Widen unsigned expressions before addition/multiplication to avoid silent truncation; '
            'respect finite numeric bounds and synchronous reset/handshake contract. '
            'Implement the entire function, never placeholder outputs. '
            'Compiler has assigned reference_code and reference_provenance specifically for this module. '
            'reference_tests includes corresponding golden/testbench code. Use its arithmetic and handshake lessons '
            'and the Compiler adaptation notes to implement correctly on the first attempt. '
            'Explain which unchanged library classes are linked and what your new adapter implements; return your new file. '
            'Critic UArch instructions may revise internal scheduling/latency while preserving the external handshake. '
            'If that conflicts with a fixed-cycle dependency in the plan, request a Compiler replan. '
            'If the plan is inconsistent, return {"replan_reason":"specific interface/architecture conflict"}. '
            'After a failed check, use the diagnostics to repair this module.', context)


class AssemblyUArchAgent(UArchAgent):
    def run(self, context):
        return super().run({**context, 'assignment':
            'You are the single SYSTEM ASSEMBLY UArch. All non-top modules have passed their frozen '
            'planner tests. Implement only the top integration/control wrapper. Connect accepted children '
            'using their actual ports and protocols. You cannot rewrite children. Whole-system golden '
            'verification failures are returned here for local top repair. If a child or plan must change, '
            'return replan_reason with the specific failing interface/function; do not conceal it in the top.'})


class CriticAgent(JsonAgent):
    def run(self, context):
        return self.ask('Analyze only the completed whole-system numerical verification and physical results. '
            'Minimize latency and MAXIMIZE energy_efficiency_queries_per_joule subject to quality, cell area and clock constraints. '
            'Use the SAME query workload and energy accounting for comparisons; never increase reported efficiency '
            'by changing the definition of useful work. Separate measurement from hypothesis. Read power_method '
            'and ppa_backend in the evaluation to determine fidelity; even post-route power remains a modeled estimate. '
            'A single measured design cannot establish a Pareto improvement or optimality. '
            'Changing a fixed-latency or II=1 module behavior requires compiler reentry to revise the contract. '
            'Assign one actionable cross-layer intervention: kernel (legal sparse config), compiler '
            '(topology/scheduling), uarch (implementation under same module interfaces), or stop. '
            'Use history and retained Pareto designs; a regressing last round does not erase earlier best designs. '
            'Return {"layer":"kernel|compiler|uarch|stop", "reason":"...", '
            '"evidence":["evaluation.area_um2"], "instructions":"concrete change and expected effect"}. '
            'For layer=kernel ALSO return proposed_config containing the COMPLETE legal configuration. '
            'It will be profiled and rejected if quality exceeds the constraint before any design is rebuilt. '
            'Read measured_config_profiles and do not propose configurations already measured infeasible. '
            'Choose evidence strings VERBATIM from available_evidence; include at least one. '
            'Do not prepend current. Do not invent a path or cite system_plan as a measured metric. '
            'Address validation_feedback if a previous reply was rejected.', context)


def validate_critique(value: dict, current: dict) -> dict:
    if value.get('layer') not in ('kernel', 'compiler', 'uarch', 'stop'):
        raise ValueError('Critic returned an invalid reentry layer')
    if not value.get('reason') or not value.get('instructions') or not value.get('evidence'):
        raise ValueError('Critic must provide reasoning, instructions and evidence')
    for path in value['evidence']:
        cursor = current
        if not isinstance(path, str) or not path.startswith(('evaluation.', 'profile.')):
            raise ValueError('Critic evidence must reference measured evaluation/profile')
        for part in path.split('.'):
            if not isinstance(cursor, dict) or part not in cursor:
                raise ValueError(f'Unknown Critic evidence path: {path}')
            cursor = cursor[part]
        if cursor is None:
            raise ValueError(f'Critic cites absent evidence: {path}')
    return value

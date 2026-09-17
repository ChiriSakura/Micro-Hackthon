"""Bounded executable module contracts, independent of generated HDL.

Compiler declares math/protocol; this interpreter computes vectors and expected
values. The declaration is still planner-authored, NOT the trusted algorithm
oracle. Whole-system verification remains mandatory.
"""
from __future__ import annotations

import ast
from functools import lru_cache
import operator
import random
import re


@lru_cache(maxsize=1024)
def _parse(expression):
    if not isinstance(expression, str) or len(expression) > 8192:
        raise ValueError('Behavior expression must be a string of at most 8192 characters')
    try:
        tree = ast.parse(expression, mode='eval')
    except SyntaxError as exc:
        raise ValueError(f'Invalid behavior expression: {expression}') from exc
    if len(list(ast.walk(tree))) > 512:
        raise ValueError('Behavior expression too complex')
    return tree.body


def _lane(word, index, width):
    if any(type(v) is not int for v in (word,index,width)) or word < 0 or not 0 <= index < 256 or not 1 <= width <= 65536:
        raise ValueError(f'lane(word,index,width) arguments out of bounds: index={index}, width={width}; '
                         'word must be nonnegative, index must be 0..255, width must be 1..65536. '
                         'Guard a lookup outside its declared range or specify a legitimate input precondition.')
    return (word >> (index*width)) & ((1 << width)-1)


def _pack(width, *values):
    if type(width) is not int or not 1 <= width <= 65536 or not 1 <= len(values) <= 32:
        raise ValueError('pack(width,low_lane,...,high_lane) arguments out of bounds')
    if width*len(values) > 65536 or any(type(v) is not int or not 0 <= v < (1 << width) for v in values):
        raise ValueError(f'Packed lane exceeds its width ({width} bits per lane). '
                         'pack requires nonnegative lane bit patterns; use spack for signed lanes, '
                         'or explicitly mask each signed lane before pack.')
    return sum(v << (i*width) for i,v in enumerate(values))


def _signed(word, width):
    if type(word) is not int or type(width) is not int or not 1 <= width <= 65536:
        raise ValueError('signed(word,width) requires bounded integer arguments')
    word &= (1 << width)-1
    return word-(1 << width) if word & (1 << (width-1)) else word


def _spack(width, *values):
    if type(width) is not int or not 1 <= width <= 65536 or any(
            type(v) is not int or not -(1 << (width-1)) <= v < (1 << (width-1)) for v in values):
        raise ValueError('Signed packed lane exceeds its width')
    return _pack(width, *(v & ((1 << width)-1) for v in values))


def _trunc_div(numerator, denominator):
    if denominator == 0:
        return 0
    magnitude = abs(numerator) // abs(denominator)
    return -magnitude if (numerator < 0) != (denominator < 0) else magnitude


def evaluate(expression, values):
    """No eval/exec, attributes, imports, loops, arbitrary calls or host access."""
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, bool):
            result = node.value
        elif isinstance(node, ast.Name) and node.id in values:
            result = values[node.id]
        elif isinstance(node, ast.Name):
            raise ValueError(f'Unknown behavior name {node.id!r}; use an input or an earlier let binding. '
                             'let entries are eagerly evaluated expressions, not functions or pseudocode; '
                             'remove unused pseudo-function bindings with unbound parameters.')
        elif isinstance(node, ast.BinOp):
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, (ast.LShift, ast.RShift)) and not 0 <= right <= 65536:
                raise ValueError('Shift out of bounds')
            op = {ast.Add:operator.add, ast.Sub:operator.sub, ast.Mult:operator.mul,
                  ast.FloorDiv:operator.floordiv, ast.Mod:operator.mod,
                  ast.BitAnd:operator.and_, ast.BitOr:operator.or_, ast.BitXor:operator.xor,
                  ast.LShift:operator.lshift, ast.RShift:operator.rshift}.get(type(node.op))
            if op is None:
                raise ValueError('Unsupported behavior operator')
            result = op(left, right)
        elif isinstance(node, ast.UnaryOp):
            op = {ast.USub:operator.neg,ast.UAdd:operator.pos,ast.Invert:operator.invert,ast.Not:operator.not_}.get(type(node.op))
            if op is None:
                raise ValueError('Unsupported unary operator')
            result = op(visit(node.operand))
        elif isinstance(node, ast.IfExp):
            result = visit(node.body if visit(node.test) else node.orelse)
        elif isinstance(node, ast.BoolOp) and isinstance(node.op,(ast.And,ast.Or)):
            # Preserve short-circuiting for guards such as d == 0 or n // d < 16.
            result = True if isinstance(node.op,ast.And) else False
            for item in node.values:
                result = bool(visit(item))
                if result != isinstance(node.op,ast.And):
                    break
        elif isinstance(node, ast.Compare):
            left, result = visit(node.left), True
            for op,right_node in zip(node.ops,node.comparators):
                right=visit(right_node)
                fn={ast.Eq:operator.eq,ast.NotEq:operator.ne,ast.Lt:operator.lt,
                    ast.LtE:operator.le,ast.Gt:operator.gt,ast.GtE:operator.ge}.get(type(op))
                if fn is None:
                    raise ValueError('Unsupported comparison')
                result = result and fn(left,right)
                left=right
        elif isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and not node.keywords:
            funcs={'lane':_lane,'pack':_pack,'spack':_spack,'signed':_signed,'trunc_div':_trunc_div,
                   'abs':abs,'min':min,'max':max}
            if node.func.id not in funcs or not 1 <= len(node.args) <= 33:
                raise ValueError('Only lane, pack, spack, signed, trunc_div, abs, min and max calls are supported')
            result=funcs[node.func.id](*(visit(arg) for arg in node.args))
        else:
            raise ValueError(f'Unsupported behavior syntax: {type(node).__name__}')
        if type(result) not in (int,bool) or abs(result).bit_length() > 131072:
            raise ValueError('Behavior result is not a bounded integer')
        return result
    try:
        return int(visit(_parse(expression)))
    except (ValueError,ZeroDivisionError,TypeError,RecursionError) as exc:
        raise ValueError(f'Behavior evaluation failed for {expression[:240] if isinstance(expression,str) else expression}: {exc}') from exc


def port_layouts(module):
    """Infer unambiguous lane widths from the frozen mathematical expressions."""
    return _port_layouts(module.ports, module.behavior or {})


def _port_layouts(ports, behavior):
    layouts, inputs = {}, {p.name for p in ports if p.direction == 'input'}
    observed = {}
    for expression in [*behavior.get('let', {}).values(), *behavior.get('outputs', {}).values()]:
        for node in ast.walk(_parse(expression)):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'lane'
                    and len(node.args) == 3 and isinstance(node.args[0], ast.Name)
                    and node.args[0].id in inputs and isinstance(node.args[2], ast.Constant)):
                observed.setdefault(node.args[0].id, set()).add(node.args[2].value)
    for name, widths in observed.items():
        if len(widths) == 1:
            layouts[name] = next(iter(widths))
    for name, expression in behavior.get('outputs', {}).items():
        node = _parse(expression)
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in ('pack', 'spack') and isinstance(node.args[0], ast.Constant)):
            layouts[name] = node.args[0].value
    return {p.name: layouts[p.name] for p in ports if p.name in layouts
            and type(layouts[p.name]) is int and 0 < layouts[p.name] <= p.width
            and p.width % layouts[p.name] == 0}


def explain_module_failure(module, gate):
    """Decode actual simulator counterexamples; never modify the oracle or verdict."""
    log = gate.get('functional', {}).get('simulation', {}).get('diagnostics', '')
    match = re.search(r'module case=(\d+) step=(\d+) output=(\w+) expected=(\d+) actual=(\d+)', log)
    if not match:
        return None
    case, step = int(match[1]), int(match[2])
    if case >= len(module.tests) or step >= len(module.tests[case]['steps']):
        return None
    widths = {p.name: p.width for p in module.ports}
    layouts = port_layouts(module)
    def word(name, value):
        width = widths[name]
        result = {'width': width, 'hex': hex(value), 'signed_twos_complement': _signed(value, width)}
        if name in layouts:
            lane_width = layouts[name]
            # Bound diagnostic size, independently of accepted port width.
            lanes = [(value >> (i*lane_width)) & ((1 << lane_width)-1)
                     for i in range(min(32, width//lane_width))]
            result.update(lane_width=lane_width, low_to_high_lanes=lanes,
                          signed_lanes=[_signed(v, lane_width) for v in lanes])
        return result
    stimulus = module.tests[case]['steps'][step]
    name, expected, actual = match[3], int(match[4]), int(match[5])
    if name not in widths:
        return None
    return {'test': module.tests[case]['name'], 'case': case, 'step': step, 'output': name,
            'inputs': {n: word(n, v) for n, v in stimulus['inputs'].items() if n in widths},
            'expected': word(name, expected), 'actual': word(name, actual),
            'frozen_expected_matches_log': stimulus['expected'].get(name) == expected,
            'scope': 'decoded simulator failure and frozen stimulus; signed lanes are interpretations, not a change of port semantics'}


def explain_behavior(module):
    """Machine-computed arithmetic examples; explanatory, never a replacement gate."""
    behavior = module.behavior
    if not behavior:
        return []
    widths = {p.name: p.width for p in module.ports}
    def compact(value):
        return value if abs(value).bit_length() <= 128 else {'bit_length': abs(value).bit_length()}
    examples = []
    for raw in behavior['vectors'][:6]:
        values = {name: evaluate(value, {}) if isinstance(value, str) else value for name, value in raw.items()}
        inputs = {name: {'width': widths[name], 'unsigned': compact(value),
                         'hex': hex(value) if widths[name] <= 128 else None,
                         'masked_to_port': compact(value & ((1 << widths[name])-1)),
                         'signed_twos_complement': compact(_signed(value, widths[name]))}
                  for name, value in values.items()}
        intermediates = {}
        for name, expression in behavior.get('let', {}).items():
            values[name] = evaluate(expression, values)
            intermediates[name] = compact(values[name])
        outputs = {}
        for name, expression in behavior['outputs'].items():
            value = evaluate(expression, values)
            outputs[name] = {'mathematical_value': compact(value),
                             'port_bit_pattern': compact(value & ((1 << widths[name])-1))}
        examples.append({'inputs': inputs, 'intermediates': intermediates, 'outputs': outputs})
    return examples


def compile_tests(ports, behavior):
    """Generate reset, single-pulse, pipeline-drain and back-to-back checks."""
    if not isinstance(behavior,dict):
        raise ValueError('behavior must be an object')
    ins={p.name:p.width for p in ports if p.direction=='input'}
    outs={p.name:p.width for p in ports if p.direction=='output'}
    latency=behavior.get('latency',0)
    if type(latency) is not int or not 0 <= latency <= 64:
        raise ValueError('Behavior latency must be 0..64')
    valid_in=behavior.get('valid_input')
    valid_out=behavior.get('valid_output')
    reset=behavior.get('reset')
    control={'clock',reset,valid_in}-{None}
    if latency:
        if any(ins.get(n)!=1 for n in ('clock',reset,valid_in)) or outs.get(valid_out)!=1:
            raise ValueError('Pipeline requires one-bit clock/reset/valid_input and valid_output ports')
        if len({'clock',reset,valid_in})!=3:
            raise ValueError('Pipeline control ports must be distinct')
    elif valid_in or valid_out or reset or 'clock' in ins:
        raise ValueError('Combinational behavior has no clock/reset/valid metadata; express data outputs directly')
    data_ins={k:v for k,v in ins.items() if k not in control}
    data_outs={k:v for k,v in outs.items() if k!=valid_out}
    expressions=behavior.get('outputs')
    bindings=behavior.get('let',{})
    if not isinstance(expressions,dict) or set(expressions)!=set(data_outs) or not data_outs:
        raise ValueError('behavior.outputs must define every data output exactly once')
    if not isinstance(bindings,dict) or len(bindings)>256:
        raise ValueError('behavior.let must be an ordered map of at most 256 expressions')
    for name in bindings:
        if not isinstance(name,str) or not name.isidentifier() or name in ins:
            raise ValueError('Invalid/shadowed behavior binding')
    condition=behavior.get('input_condition','1')
    def oracle(vector):
        env=dict(vector)
        for name,expression in bindings.items():
            env[name]=evaluate(expression,env)
        return {name:evaluate(expr,env)&((1<<data_outs[name])-1) for name,expr in expressions.items()}
    raw_vectors=behavior.get('vectors')
    if not isinstance(raw_vectors,list) or not 3 <= len(raw_vectors) <= 12:
        raise ValueError('Provide 3..12 behavior input vectors (zero, boundaries, ordinary cases); no expected values')
    vectors=[]
    for raw in raw_vectors:
        if not isinstance(raw,dict) or set(raw)!=set(data_ins):
            raise ValueError(f'Each behavior vector initializes exactly {sorted(data_ins)}')
        vector={name:evaluate(value,{}) if isinstance(value,str) else value for name,value in raw.items()}
        for name, value in vector.items():
            if type(value) is not int or not 0 <= value < (1 << data_ins[name]):
                hint = ('pack(w,...) and spack(w,...) take the width of EACH LANE, not the port. '
                        f'For N lanes packed into this {data_ins[name]}-bit input, use lane width '
                        f'{data_ins[name]}/N; e.g. two 4-bit lanes in 8 bits use pack(4,a,b), not pack(8,a,b). ')
                if type(value) is int and value < 0:
                    hint = ('Ports carry unsigned bit patterns, including signed arithmetic ports. '
                            f'If this is a legal signed value, encode it explicitly as the expression '
                            f'"({value}) & 0x{(1 << data_ins[name])-1:x}" or spack({data_ins[name]}, {value}). ')
                raise ValueError(f'Behavior vector {name}={value} exceeds {data_ins[name]}-bit input; '
                                 f'allowed integers 0..{(1 << data_ins[name])-1}. '
                                 + hint +
                                 f'Original expression: {str(raw[name])[:200]}')
        if not evaluate(condition,vector):
            raise ValueError('Explicit behavior vector violates input_condition')
        vectors.append(vector)
    # Measured against the declared model, not samples guessed by the HDL writer.
    bounds=behavior.get('input_bounds',{})
    if not isinstance(bounds,dict) or set(bounds)-set(data_ins):
        raise ValueError('Unknown behavior input_bounds')
    for name,pair in bounds.items():
        if (not isinstance(pair,list) or len(pair)!=2 or any(type(v) is not int for v in pair)
                or not 0<=pair[0]<=pair[1]<(1<<data_ins[name])):
            raise ValueError('Invalid behavior input bounds')
    if any(not lo <= vector[name] <= hi for name,(lo,hi) in bounds.items() for vector in vectors):
        raise ValueError('Explicit vector violates input_bounds')
    rng=random.Random(31)
    for _ in range(2048):
        if len(vectors)>=len(raw_vectors)+12:
            break
        candidate={n:rng.randint(*bounds.get(n,[0,(1<<w)-1])) for n,w in data_ins.items()}
        if evaluate(condition,candidate):
            vectors.append(candidate)
    if len(vectors)<len(raw_vectors)+12:
        raise ValueError('Could not sample 12 legal behavior vectors; review bounds and input_condition')
    version = behavior.get('test_generation_version', 1)
    if type(version) is not int or version not in (1, 2):
        raise ValueError('Unsupported behavior test_generation_version')
    if version == 2:
        # Versioned so archived plans retain their exact frozen stimuli. Packed
        # signed minima are not all-ones words and are rarely hit by randomness.
        layouts = {n:w for n,w in _port_layouts(ports,behavior).items() if n in data_ins}
        def fill(name, high):
            lane_width = layouts[name]
            value = (1 << (lane_width-1)) - int(high)
            return sum(value << shift for shift in range(0,data_ins[name],lane_width))
        base = vectors[0]
        corners = [{**base, **{n:fill(n, high) for n in layouts}} for high in (False,True)]
        for name in list(layouts)[:8]:
            corners.append({**base, **{n:fill(n,n != name) for n in layouts}})
            corners.append({**base, **{n:fill(n,n == name) for n in layouts}})
        seen = {tuple(sorted(v.items())) for v in vectors}
        for candidate in corners:
            key = tuple(sorted(candidate.items()))
            if (key not in seen and all(lo <= candidate[n] <= hi for n,(lo,hi) in bounds.items())
                    and evaluate(condition,candidate)):
                vectors.append(candidate)
                seen.add(key)
    if not latency:
        return [{'name':'behavior_combinational','steps':[
            {'inputs':v,'cycles':0,'expected':oracle(v)} for v in vectors]}]
    zeros={n:0 for n in data_ins}
    def scenario(name, transactions):
        pipeline=[None]*latency
        steps=[{'inputs':{reset:1,valid_in:0,**zeros},'cycles':1,
                'expected':{valid_out:0,**{n:0 for n in data_outs}}}]
        for vector in transactions:
            pipeline=[oracle(vector) if vector is not None else None]+pipeline[:-1]
            current=pipeline[-1]
            expected={valid_out:int(current is not None)}
            if current is not None:
                expected.update(current)
            steps.append({'inputs':{reset:0,valid_in:int(vector is not None),**(vector or zeros)},
                          'cycles':1,'expected':expected})
        # Check reset after nonzero activity, not just simulator initial zeros.
        steps.append({'inputs':{reset:1,valid_in:0,**zeros},'cycles':1,
                      'expected':{valid_out:0,**{n:0 for n in data_outs}}})
        return {'name':name,'steps':steps}
    tests=[scenario(f'behavior_isolated_{i}',[v]+[None]*latency) for i,v in enumerate(vectors[:3])]
    # One stream with bubbles and complete drain exercises alignment and throughput.
    stream=[]
    for index,vector in enumerate(vectors):
        stream.append(vector)
        if index%3==2:
            stream.append(None)
    tests.append(scenario('behavior_stream',stream+[None]*latency))
    return tests

"""Small KiCad S-expression helpers used by the stack design checks."""
from pathlib import Path
import copy
import json
import math
import uuid
import sexpdata as sx

S = sx.Symbol

def kids(n, key):
    return [x for x in n if isinstance(x, list) and x and str(x[0]) == key]

def one(n, key):
    return next(x for x in kids(n, key))

def prop(n, key):
    return next(x for x in kids(n, 'property') if x[1] == key)

def uid(tag):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'elevation-controller-stack/p4/' + tag))

def fmt(n, depth=0):
    if not isinstance(n, list):
        return sx.dumps(n)
    if not any(isinstance(x, list) for x in n):
        return sx.dumps(n)
    head, tail = [], []
    for x in n:
        (tail if isinstance(x, list) or tail else head).append(x)
    return '(' + ' '.join(sx.dumps(x) for x in head) + ''.join('\n' + '  '*(depth+1) + fmt(x, depth+1) for x in tail) + ')'

def read(path):
    return sx.loads(Path(path).read_text(encoding='utf-8-sig'))

def save(path, doc):
    Path(path).write_text(fmt(doc) + '\n', encoding='utf-8')

def instance(doc, ref):
    return next(n for n in kids(doc, 'symbol') if prop(n, 'Reference')[2] == ref)

def library(doc, instance):
    return next(n for n in kids(one(doc, 'lib_symbols'), 'symbol') if n[1] == one(instance, 'lib_id')[1])

def pins(lib, inst):
    at = one(inst, 'at'); angle = math.radians(at[3]); result = {}
    unit = one(inst, 'unit')[1] if kids(inst, 'unit') else 1
    for group in kids(lib, 'symbol'):
        if int(group[1].split('_')[-2]) not in (0, unit):
            continue
        for p in kids(group, 'pin'):
            a = one(p, 'at'); x, y = a[1:3]
            if kids(inst, 'mirror'):
                if one(inst, 'mirror')[1] == S('x'): y = -y
                else: x = -x
            result[one(p, 'number')[1]] = (round(at[1] + x*math.cos(angle)-y*math.sin(angle), 4), round(at[2]-x*math.sin(angle)-y*math.cos(angle), 4))
    return result

def translate(n, dx, dy):
    if not isinstance(n, list): return
    if n and str(n[0]) in ('at', 'xy'):
        n[1], n[2] = round(n[1]+dx, 4), round(n[2]+dy, 4)
    else:
        for x in n: translate(x, dx, dy)

def add(doc, tag, source):
    n = sx.loads(source)
    n.append([S('uuid'), uid(tag)])
    doc.append(n)
    return n

def wire(doc, tag, a, b):
    return add(doc, tag, f'(wire (pts (xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})) (stroke (width 0) (type default)))')

def note(doc, tag, text, x, y, size=1.27):
    return add(doc, tag, f'(text {json.dumps(text)} (at {x} {y} 0) (effects (font (size {size} {size})) (justify left top)))')

def label(doc, tag, text, pos, angle=0, kind='global_label', shape='bidirectional'):
    shape_text = f'(shape {shape})' if kind != 'label' else ''
    justify = 'left' if angle == 0 else 'right'
    return add(doc, tag, f'({kind} {json.dumps(text)} {shape_text} (at {pos[0]} {pos[1]} {angle}) (effects (font (size 1.27 1.27)) (justify {justify})))')

def nc(doc, tag, pos):
    return add(doc, tag, f'(no_connect (at {pos[0]} {pos[1]}))')

def rename(doc, mapping):
    def walk(n):
        if not isinstance(n, list): return
        for i, x in enumerate(n):
            if isinstance(x, str) and x in mapping: n[i] = mapping[x]
            elif isinstance(x, list): walk(x)
    walk(doc)

def retain_parts(doc, refs):
    """Keep physical drawing branches attached to retained components."""
    retained = [n for n in kids(doc, 'symbol') if prop(n, 'Reference')[2] in refs]
    seeds = {p for n in retained for p in pins(library(doc,n),n).values()}
    edges = [(n, [tuple(p[1:]) for p in one(n, 'pts')[1:]]) for n in kids(doc,'wire')]
    seen = set(seeds)
    while True:
        prev = len(seen)
        for _, (a,b) in edges:
            if a in seen or b in seen: seen.update((a,b))
        if len(seen) == prev: break
    out = []
    for n in doc:
        if not isinstance(n,list): out.append(n); continue
        k = str(n[0])
        if k == 'symbol' and n not in retained: continue
        if k == 'wire' and tuple(one(n,'pts')[1][1:]) not in seen: continue
        if k in ('label','global_label','hierarchical_label','no_connect','junction') and tuple(one(n,'at')[1:3]) not in seen: continue
        if k == 'text': continue
        out.append(n)
    doc[:] = out
    ids = {one(n,'lib_id')[1] for n in retained}
    lib = one(doc,'lib_symbols'); lib[:] = [lib[0]] + [n for n in lib[1:] if n[1] in ids]

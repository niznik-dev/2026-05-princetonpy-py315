"""Generate python_315_features.ipynb. Run once; the .ipynb is the artifact."""

import nbformat as nbf

nb = nbf.v4.new_notebook()
nb.metadata["kernelspec"] = {
    "display_name": "Python 3.15",
    "language": "python",
    "name": "py315",
}
nb.metadata["language_info"] = {
    "name": "python",
    "version": "3.15.0b1",
    "mimetype": "text/x-python",
    "file_extension": ".py",
    "pygments_lexer": "ipython3",
}

cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s))
code = lambda s: cells.append(nbf.v4.new_code_cell(s))


md(r"""# What's New in Python 3.15 — A Notebook Tour

This notebook walks through the headline features of **Python 3.15.0b1** with runnable examples. Each section explains *what* the feature is, *why* it matters, and shows it in action.

Built on a real 3.15.0b1 install via `pyenv` — the kernel for this notebook is `py315`.

> **Note on honesty:** Some cells use brand-new syntax (lazy imports, unpacking-in-comprehensions). Those cells will *fail to parse* on any Python < 3.15, so the notebook itself is a 3.15 artifact.""")


# 0 — version sanity check
md("## 0. Version check\n\nMake sure we're actually on 3.15.")
code("""import sys
print(sys.version)
assert sys.version_info[:2] == (3, 15), "This notebook expects Python 3.15"
""")


# 1 — Lazy Imports (PEP 810)
md("""## 1. Lazy Imports (PEP 810)

**What:** A new `lazy` keyword that defers the actual import work until the imported name is first *used*. Imports become free at module load time.

**Why it matters:** Big CLI tools and frameworks have long paid startup cost for imports they never touch on a given run. Tools like Mercurial, AWS CLI, and IPython have all hand-rolled lazy-import machinery. PEP 810 makes it a first-class language feature, with the heavy work done by the import system rather than user code.

**How to use:** Three ways — `lazy import X`, `lazy from M import N`, or process-wide via the `-X lazy_imports` flag / `sys.set_lazy_imports()`. The deferred object is indistinguishable from the real module until first attribute access.""")

code("""import sys, time

# Time a lazy import — should be effectively free
t0 = time.perf_counter()
lazy import json
elapsed_lazy = time.perf_counter() - t0

# Now trigger the real load by using something from the module
t0 = time.perf_counter()
json.dumps({"hello": "world"})
elapsed_first_use = time.perf_counter() - t0

print(f"lazy import statement:  {elapsed_lazy*1e6:8.1f} µs")
print(f"first use of json:      {elapsed_first_use*1e6:8.1f} µs   <-- real work happens here")
print(f"sys.set_lazy_imports available: {hasattr(sys, 'set_lazy_imports')}")
""")

code("""# Lazy `from ... import ...` works too
lazy from pathlib import Path

# Path isn't actually loaded yet — but it acts like it is
p = Path("/tmp/example.txt")
print(type(p), p)
""")


# 2 — frozendict (PEP 814)
md("""## 2. frozendict (PEP 814)

**What:** An immutable, hashable `dict`. Python finally has an official answer to "I want a dict I can use as a `dict` key or `set` member."

**Why it matters:** Folks have been rolling their own frozen-dict types for over a decade. Having one in builtins means library authors can return immutable mappings without inventing yet another type, and config systems can pass dicts around with structural sharing guarantees.

**API surface:** Constructor mirrors `dict`. No `__setitem__`, `__delitem__`, `update`, `clear`, etc. Hash is order-insensitive on the *items*. JSON serializes it as a regular object.""")

code("""# It's a builtin in 3.15 — no import needed
fd = frozendict({"name": "Mordin", "species": "salarian"})
print(fd)
print(type(fd).__name__)
""")

code("""# Mutation attempts raise TypeError
try:
    fd["role"] = "scientist"
except TypeError as e:
    print(f"setitem  -> TypeError: {e}")

try:
    del fd["name"]
except TypeError as e:
    print(f"delitem  -> TypeError: {e}")

# No mutating methods
print("has 'update'?", hasattr(fd, "update"))
print("has 'clear'?", hasattr(fd, "clear"))
""")

code("""# Hashable -> usable as dict key or in a set
catalog = {
    frozendict({"x": 0, "y": 0}): "origin",
    frozendict({"x": 1, "y": 0}): "east",
}
print(catalog[frozendict({"y": 0, "x": 0})])  # equality is order-insensitive
""")

code("""# JSON works out of the box
import json
print(json.dumps(frozendict({"a": 1, "b": [1, 2, 3]})))
""")


# 3 — sentinel (PEP 661)
md("""## 3. Sentinel values (PEP 661)

**What:** A standard way to create sentinel objects — distinct, identity-comparable, type-checkable singletons used as default values when `None` isn't sufficient (because `None` is a meaningful value the caller might pass).

**Why it matters:** Every library has its own `_MISSING = object()` or `_UNSET = type("_unset", (), {"__repr__": lambda s: "UNSET"})()` somewhere. Now there's one canonical way that also plays nice with type checkers and repr.

**Note:** In 3.15.0b1 this lands as a **lowercase `sentinel` builtin**, not as a module. The PEP discussion had been about `sentinel.sentinel("MISSING")` but the final landed form is just `sentinel("NAME")` from builtins.""")

code("""MISSING = sentinel("MISSING")
print(MISSING)              # repr is the name
print(MISSING is MISSING)   # identity-stable

def get(d, key, default=MISSING):
    if key not in d:
        if default is MISSING:
            raise KeyError(key)
        return default
    return d[key]

# Distinguishes "no default given" from "default is None"
print(get({"a": 1}, "a"))
print(get({"a": 1}, "b", default=None))   # explicit None -> returned
try:
    get({"a": 1}, "b")                     # MISSING default -> raise
except KeyError as e:
    print(f"raised KeyError: {e}")
""")


# 4 — Unpacking in comprehensions (PEP 798)
md("""## 4. Unpacking in comprehensions (PEP 798)

**What:** `*` and `**` unpacking now work inside list, set, dict, and generator comprehensions.

**Why it matters:** Today you'd write `[x for L in lists for x in L]` to flatten — readable, but the double-`for` always reads slightly awkward. With PEP 798 you can write `[*L for L in lists]`, which mirrors `[*L1, *L2, *L3]` for the comprehension case. Similarly for sets and dicts.""")

code("""lists = [[1, 2], [3, 4], [5]]
print("flatten:", [*L for L in lists])

# Set unpacking
sets = [{1, 2}, {2, 3}, {3, 4}]
print("union:  ", {*s for s in sets})

# Dict unpacking — later keys win, as with normal {**a, **b}
dicts = [{"a": 1}, {"b": 2}, {"a": 99}]
print("merge:  ", {**d for d in dicts})

# Generator expression form
gen = (*L for L in lists)
print("gen:    ", list(gen))
""")


# 5 — Tachyon Sampling Profiler (PEP 799)
md("""## 5. Tachyon Sampling Profiler (PEP 799)

**What:** A new low-overhead, in-tree sampling profiler shipped as the `profiling` package, with separate `sampling` and `tracing` submodules.

**Why it matters:** Until now, the stdlib offered `cProfile` (deterministic, but biased for short-running fast functions due to per-call overhead) and `profile` (pure-Python, even slower). Sampling profilers like py-spy and Austin have been the industry standard for production use. Tachyon brings that approach into the stdlib.

**Modes:** `wall`, `cpu`, `gil`, `exception`. **Output formats:** `pstats`, `flamegraph` (via `CollapsedStackCollector`), `heatmap`, `gecko` (Firefox profiler), `jsonl`, plus a live TUI.

The package exposes two submodules:

- **`profiling.tracing`** — in-process, cProfile-shaped API (`tracing.Profile`, `tracing.run`). Good for "profile this function I'm about to call."
- **`profiling.sampling`** — sampling-based collectors (`PstatsCollector`, `HeatmapCollector`, `GeckoCollector`, `JsonlCollector`, `CollapsedStackCollector`). Good for attaching to a long-running process and exporting in a format your favourite viewer (speedscope, Firefox Profiler, etc.) can read.""")

code("""from profiling import tracing

def busy(n):
    s = 0
    for i in range(n):
        s += i * i
    return s

# tracing.Profile is shaped like the old cProfile.Profile
prof = tracing.Profile()
prof.enable()
busy(500_000)
prof.disable()

prof.create_stats()
prof.print_stats()
""")

code("""# A peek at the sampling collectors — these are what you'd use to capture
# samples from a long-running process and export to a viewer.
from profiling import sampling
print("Collectors available:")
for name in ["PstatsCollector", "CollapsedStackCollector", "HeatmapCollector",
             "GeckoCollector", "JsonlCollector"]:
    cls = getattr(sampling, name)
    print(f"  {name:25s} - {(cls.__doc__ or '').strip().splitlines()[0] if cls.__doc__ else '(no doc)'}")
""")


# 6 — Improved error messages
md("""## 6. Better error messages

**What:** Two themes —

1. **Cross-language suggestions:** type a JavaScript or Java method on a Python object and the traceback now suggests the Python equivalent (`list.append` for `[].push`, `str.upper` for `'x'.toUpperCase`, `dict.__setitem__` for `{}.put`, etc.).
2. **Nested attribute suggestions:** for chained attribute errors like `obj.foo.bar`, the suggestion engine now looks across the nesting, not just at the leaf.

**Why it matters:** Lowers the "I'm new to this language" tax. The error-message work in 3.10–3.13 was already excellent; 3.15 just keeps pushing.""")

code("""import traceback

def show(callable_):
    try:
        callable_()
    except (AttributeError, TypeError) as e:
        # Format the traceback the same way the REPL would — this is where
        # the "Did you mean ...?" suggestions live.
        print("".join(traceback.format_exception_only(type(e), e)).rstrip())
        print("-" * 60)

show(lambda: [].push(4))
show(lambda: "hello".toUpperCase())
show(lambda: {}.put("a", 1))
""")

code("""from dataclasses import dataclass

@dataclass
class Inner:
    payload: int = 42

@dataclass
class Outer:
    inner: Inner = None

o = Outer(inner=Inner())

try:
    print(o.inner.paylod)    # typo two levels deep
except AttributeError as e:
    print("".join(traceback.format_exception_only(type(e), e)).rstrip())
""")


# 7 — UTF-8 default encoding
md("""## 7. UTF-8 default encoding

**What:** The default text encoding for `open()` is now UTF-8 system-wide, regardless of the locale. Formally completes the PEP 686 transition.

**Why it matters:** Cross-platform text handling was a persistent source of `UnicodeDecodeError` because Windows defaulted to cp1252 / a regional codepage, while Linux/macOS defaulted to UTF-8. Subtle bugs only surfaced on the wrong platform. 3.15 makes UTF-8 the universal default.""")

code("""import locale, sys
print("locale.getencoding():     ", locale.getencoding())
print("sys.getfilesystemencoding:", sys.getfilesystemencoding())

# open() without an explicit encoding -> UTF-8 everywhere
from pathlib import Path
p = Path("/tmp/py315_utf8_demo.txt")
p.write_text("héllo, 世界, 🐍")     # no encoding= needed
print("roundtrip:", p.read_text())
p.unlink()
""")


# 8 — typing improvements
md("""## 8. typing improvements

Two notable additions:

- **`TypeForm` (PEP 747)**: a type that represents *type expressions themselves*. Where `type[X]` means "an instance of X", `TypeForm[X]` means "the type expression X" — useful for libraries that introspect or transform types at runtime (think pydantic, dataclasses, FastAPI).
- **`TypedDict(..., closed=True)` (PEP 728)**: opt-in strict mode that rejects extra keys at type-check time. Combined with `extra_items=T`, you can also type the *unknown* keys.""")

code("""from typing import TypeForm, TypedDict

# TypeForm — accept a "type expression" parameter
def is_optional_int(tf: TypeForm) -> bool:
    import typing
    return tf == typing.Optional[int] or tf == (int | None)

print(is_optional_int(int | None))
print(is_optional_int(str | None))
""")

code("""# TypedDict with closed=True — a typechecker would reject extras
class StrictUser(TypedDict, closed=True):
    name: str
    age: int

# At runtime it's still a dict — the strictness is enforced by type checkers (mypy, pyright).
u: StrictUser = {"name": "Mordin", "age": 1500}
print(u)

# extra_items typed
class FlexConfig(TypedDict, extra_items=int):
    name: str
    # any other key must map to int at type-check time

c: FlexConfig = {"name": "main", "retries": 3, "timeout": 30}
print(c)
""")


# 9 — GC reversion
md("""## 9. Garbage Collection: reverted to generational (from incremental)

**What:** Python 3.14 introduced an *incremental* garbage collector — it spread collection work across many small pauses instead of doing one big pause. Python 3.15 **reverts** to the classic generational GC.

**Why the reversion:** the incremental collector showed memory-usage regressions in workloads with high churn — more retained-but-collectable objects between cycles. The 3.15 team decided the latency-vs-memory tradeoff wasn't worth it, and reverted while the team works on a better design.

**Implication for you:** if you upgraded 3.13 → 3.14 and noticed memory creep, 3.15 should fix it. If you tuned your app's GC thresholds based on 3.14's behavior, you'll want to revisit.""")

code("""import gc
# Generational GC is back — 3 generations, classic thresholds
print("thresholds:", gc.get_threshold())
print("counts:    ", gc.get_count())
print("generations:", len(gc.get_count()))
""")


# 10 — JIT improvements
md("""## 10. JIT compiler improvements

**What:** The copy-and-patch JIT introduced in 3.13 is still experimental but, in 3.15, ships with 8–13% performance gains on the standard benchmark suite compared to 3.14.

**How to use:** Build with `--enable-experimental-jit`, or use a build that has it enabled. At runtime it's transparent — code just runs faster.

**A note:** The pyenv build above used default flags, so the JIT is likely *not* compiled in. To explicitly enable, you'd want `CONFIGURE_OPTS="--enable-experimental-jit=yes-off" PYTHON_CONFIGURE_OPTS=... pyenv install 3.15.0b1` and then opt in at runtime via `PYTHON_JIT=1`. We won't benchmark here — for a real comparison you'd need controlled hardware and the same workload.""")

code("""import sys
# Check whether the current interpreter has the JIT
jit_status = "unknown"
try:
    # 3.15 exposes JIT info via sys._jit (provisional API)
    jit_status = sys._jit.is_available()
except AttributeError:
    jit_status = "sys._jit not present in this build"
print("JIT available:", jit_status)
""")


# 11 — stdlib highlights
md("""## 11. stdlib highlights

A grab-bag of small but useful additions.""")

md("### 11a. `math` — IEEE-754 floating point helpers")
code("""import math
print("isnormal(1.0):       ", math.isnormal(1.0))         # True
print("isnormal(0.0):       ", math.isnormal(0.0))         # False (zero is not normal)
print("issubnormal(1e-310): ", math.issubnormal(1e-310))   # True (denormal)
print("fmax(1.0, float('nan')):", math.fmax(1.0, float('nan')))  # 1.0 (NaN-quieting max)
print("fmin(1.0, -2.0):     ", math.fmin(1.0, -2.0))       # -2.0
print("signbit(-0.0):       ", math.signbit(-0.0))         # True
""")

md("""### 11b. `asyncio.TaskGroup.cancel()` — cancel an in-flight group

Jupyter already runs an event loop, so we `await` directly instead of using `asyncio.run()`.""")
code("""import asyncio

async def slow(name, n):
    try:
        await asyncio.sleep(n)
        print(f"{name} finished")
    except asyncio.CancelledError:
        print(f"{name} cancelled")
        raise

async def demo():
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(slow("A", 0.05))
            tg.create_task(slow("B", 10))   # would block for 10s
            await asyncio.sleep(0.1)
            tg.cancel()                      # NEW in 3.15
    except* asyncio.CancelledError:
        print("group was cancelled cleanly")

await demo()
""")

md("""### 11c. `re.prefixmatch()` replaces `re.match()`

`re.match()` has always been mildly confusing — it matches at the start of a string but doesn't require the entire string to match (unlike `re.fullmatch`). The name `prefixmatch` says what it actually does. `re.match()` is now soft-deprecated.""")
code("""import re
m = re.prefixmatch(r"\\d+", "42 cats")
print(m.group() if m else None)
""")

md("### 11d. `difflib.unified_diff(color=True)` — colorized terminal diffs")
code("""import difflib
a = "the quick brown fox\\njumps over\\nthe lazy dog\\n".splitlines(keepends=True)
b = "the quick red fox\\njumps over\\nthe sleepy dog\\n".splitlines(keepends=True)

for line in difflib.unified_diff(a, b, fromfile="a", tofile="b", color=True):
    print(line, end="")
""")

md("""### 11e. `threading.serialize_iterator` & `synchronized_iterator`

Two related additions:

- **`serialize_iterator(iterable)`** — a class that wraps an existing iterator instance with a lock, so concurrent `next()` calls are serialized.
- **`synchronized_iterator(callable)`** — a decorator for *iterator-returning callables* (e.g. `itertools.count`, generator functions). Wrapped calls produce iterators that are themselves serialized.""")
code("""import threading, itertools

# Pattern 1: wrap an existing iterator instance with serialize_iterator
shared = threading.serialize_iterator(iter(range(10)))
seen = []
seen_lock = threading.Lock()

def worker():
    for v in shared:
        with seen_lock:
            seen.append((threading.current_thread().name, v))

ts = [threading.Thread(target=worker, name=f"t{i}") for i in range(3)]
for t in ts: t.start()
for t in ts: t.join()

# Every value 0..9 should appear exactly once across all threads
print("values seen:", sorted(v for _, v in seen))
print("by thread:  ", {n: [v for tn, v in seen if tn == n] for n in {n for n, _ in seen}})
""")
code("""# Pattern 2: synchronized_iterator as a decorator on a generator function
@threading.synchronized_iterator
def counter():
    n = 0
    while n < 6:
        yield n
        n += 1

it = counter()           # each call gives a thread-safe iterator
print("first three:", [next(it), next(it), next(it)])

# Or wrap a stateful factory like itertools.count
atomic_count = threading.synchronized_iterator(itertools.count)
c = atomic_count()
print("atomic counter:", [next(c) for _ in range(4)])
""")

md("""### 11f. `tomllib` — TOML 1.1 support (partial / status uncertain)

The 3.15 changelog advertises TOML 1.1 support in tomllib. Probing the b1 build:""")
code("""import tomllib
# What works in 3.15.0b1:
print(tomllib.loads('fruit.apple.color = "red"'))   # nested-key syntax (works in 1.0 too)

# TOML 1.1 specific features — uncertain in b1
def try_parse(label, src):
    try:
        print(f"  ✅ {label}: {tomllib.loads(src)}")
    except tomllib.TOMLDecodeError as e:
        print(f"  ❌ {label}: {e}")

try_parse("trailing comma in inline table", '{a = 1, b = 2,}')
try_parse("newline in inline table",        '{a = 1,\\nb = 2}')
""")

md("### 11g. `unicodedata` — Unicode 17.0.0 + grapheme iteration")
code("""import unicodedata
print("Unicode version:", unicodedata.unidata_version)

# Iterate over user-perceived characters (grapheme clusters), not codepoints
# Family emoji is multiple codepoints joined by ZWJ — one grapheme.
s = "café 👨‍👩‍👧‍👦 🇯🇵"
for g in unicodedata.iter_graphemes(s):
    print(repr(g))
""")


# 12 — Deprecations & Removals
md("""## 12. Deprecations and removals

- **`profile` module removed** — superseded by the new `profiling` package (Tachyon, PEP 799). If you were using `import profile`, migrate to `profiling.tracing`.
- **`re.match()` soft-deprecated** — still works, but `re.prefixmatch()` is the new spelling. A DeprecationWarning will be emitted in 3.17.
- **`.pth` import lines** — the long-quirky feature where `.pth` files in site-packages could execute arbitrary code via lines starting with `import` is now removed. `.pth` files can still extend `sys.path`, but can't execute code.""")

code("""# Demonstrate the deprecation warning if any
import warnings, re
with warnings.catch_warnings(record=True) as ws:
    warnings.simplefilter("always")
    re.match(r"\\d+", "42")
    for w in ws:
        print(f"{w.category.__name__}: {w.message}")
    if not ws:
        print("(no warning raised in b1 — may arrive in a later release)")
""")


# Footer
md("""## Further reading

- Official what's new: <https://docs.python.org/3.15/whatsnew/3.15.html>
- PEP 810 (lazy imports): <https://peps.python.org/pep-0810/>
- PEP 814 (frozendict): <https://peps.python.org/pep-0814/>
- PEP 661 (sentinel): <https://peps.python.org/pep-0661/>
- PEP 798 (unpacking in comprehensions): <https://peps.python.org/pep-0798/>
- PEP 799 (Tachyon profiler): <https://peps.python.org/pep-0799/>
- PEP 747 (TypeForm): <https://peps.python.org/pep-0747/>
- PEP 728 (TypedDict closed): <https://peps.python.org/pep-0728/>

— Built on 3.15.0b1, May 2026.""")


nb.cells = cells
nbf.write(nb, "python_315_features.ipynb")
print(f"Wrote python_315_features.ipynb with {len(cells)} cells")

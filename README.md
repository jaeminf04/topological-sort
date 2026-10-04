# topological_sort

A small, dependency-free Python library for ordering items by their dependencies, with cycle errors that name the exact nodes involved.

```python
from topological_sort import topological_sort, CycleError

pairs = [("app", "config"), ("config", "base"), ("app", "base")]
try:
    order = list(topological_sort(pairs))
    print(order)  # ['base', 'config', 'app']
except CycleError as err:
    print(err.cycle)
```

## Why this exists

Most topological sort implementations tell you *that* a cycle exists but not *which* nodes form it. When a dependency graph is large and machine-generated (build systems, migration planners, feature-flag rollouts), "cycle detected" without the offending nodes is nearly useless. This library reports the cycle as an ordered list on `CycleError.cycle`, closed with the repeated start node so the loop is explicit.

The trade-off: ordering among independent nodes is deterministic but not configurable. Independent nodes are emitted in sorted order of their string representation. This keeps output reproducible across runs and platforms, at the cost of letting callers influence tie-breaking by reordering input edges. If you need custom tie-breaking, sort the result yourself afterward.

## Edge cases worth knowing

- **Mixed-type nodes** (e.g., ints and strings together) are supported. They are ordered by `str()` representation, since Python does not define `<` across unrelated types.
- **Duplicate edges** are ignored for in-degree purposes; declaring `(a, b)` twice has the same effect as declaring it once.
- **Self-loops** (`a` depends on `a`) are cycles and are reported as `[a, a]`.
- **No partial output**: if a cycle exists, `CycleError` is raised before any node is yielded, so you never get a misleading prefix of a broken order.

## Running the tests

```
PYTHONPATH=src python -m unittest discover -s tests
```

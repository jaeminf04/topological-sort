"""Topological sort with cycle reporting that names the cycle.

The implementation uses Kahn's algorithm (iterative in-degree reduction) for
the ordering itself, but falls back to a DFS-based cycle search when a cycle
is detected. We do this because Kahn's algorithm detects *that* a cycle exists
but not *which* nodes form it; DFS naturally produces the cycle path as a
side effect of walking edges until it revisits a node on the current stack.
"""

from __future__ import annotations

from typing import Dict, Hashable, Iterable, Iterator, List, Set, Tuple, TypeVar

T = TypeVar("T", bound=Hashable)


class CycleError(ValueError):
    """Raised when the graph contains a cycle.

    Attributes:
        cycle: The list of nodes forming the cycle, ordered so that each node
            depends on the next, and the last depends on the first. The first
            node is repeated at the end to make the cyclic dependency
            explicit.
    """

    def __init__(self, cycle: List[object]) -> None:
        self.cycle = list(cycle)
        # Format the cycle as a -> b -> c -> a so the message is readable
        # without requiring callers to inspect the attribute.
        rendered = " -> ".join(str(node) for node in self.cycle)
        super().__init__(f"cycle detected: {rendered}")


def _build_adjacency(
    pairs: Iterable[Tuple[T, T]]
) -> Tuple[Dict[T, Set[T]], Dict[T, Set[T]], Set[T]]:
    """Build adjacency lists and the set of all nodes from edge pairs.

    Each pair ``(a, b)`` means *a depends on b* — equivalently, *b must come
    before a*. We store both forward (dependents) and reverse (dependencies)
    adjacency because Kahn's algorithm consumes in-degree while cycle-finding
    DFS walks dependents.
    """
    dependents: Dict[T, Set[T]] = {}
    dependencies: Dict[T, Set[T]] = {}
    nodes: Set[T] = set()

    for a, b in pairs:
        nodes.add(a)
        nodes.add(b)
        dependents.setdefault(b, set()).add(a)
        dependencies.setdefault(a, set()).add(b)
        # Ensure every node has an entry in both maps even if it has no
        # edges on one side, so later lookups never KeyError.
        dependents.setdefault(a, set())
        dependencies.setdefault(b, set())

    return dependents, dependencies, nodes


def _find_cycle(
    dependents: Dict[T, Set[T]], nodes: Set[T]
) -> List[T]:
    """Return a cycle as an ordered node list, or an empty list if none.

    We run a DFS over the *dependents* graph (edges point from a dependency to
    the things that depend on it). When we encounter a node already on the
    current recursion stack, the slice of the stack from that node to the
    current node is the cycle. We append the repeated start node so the cycle
    reads as a closed loop.

    Nodes are visited in sorted order of their string representation. This is
    a deliberate choice: it makes cycle reporting deterministic across runs
    and platforms, which matters for tests and for diff-stable error messages.
    The cost is a minor sort on each visit, acceptable because cycle-finding
    only runs once and only when the sort has already failed.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[T, int] = {node: WHITE for node in nodes}
    stack: List[T] = []

    # Sort by str() so the chosen cycle is stable across runs. Plain sorted()
    # would fail on mixed-type node sets; str() gives a total order.
    ordered = sorted(nodes, key=lambda n: str(n))

    def visit(node: T) -> List[T]:
        color[node] = GRAY
        stack.append(node)
        for nxt in sorted(dependents.get(node, ()), key=lambda n: str(n)):
            if color[nxt] == GRAY:
                # Found a back edge: slice the stack from the first occurrence
                # of nxt to the current end, then close the loop.
                start = stack.index(nxt)
                return stack[start:] + [nxt]
            if color[nxt] == WHITE:
                found = visit(nxt)
                if found:
                    return found
        stack.pop()
        color[node] = BLACK
        return []

    for root in ordered:
        if color[root] == WHITE:
            found = visit(root)
            if found:
                return found
    return []


def topological_sort(
    pairs: Iterable[Tuple[T, T]],
) -> Iterator[T]:
    """Yield nodes in dependency-respecting order.

    Each input pair ``(a, b)`` declares that *a depends on b* — b must appear
    before a in the output. Nodes that never appear in any pair are not part
    of the graph and are not yielded.

    If the graph contains a cycle, ``CycleError`` is raised before any node
    is yielded. The error's ``cycle`` attribute lists the offending nodes in
    dependency order, with the first node repeated at the end.

    The order among nodes that are mutually independent is deterministic:
    they are emitted in sorted order of their string representation. This
    makes the output reproducible across runs, which is useful for caching
    and for tests. The trade-off is that callers cannot influence tie-breaking
    by reordering the input edges.
    """
    dependents, dependencies, nodes = _build_adjacency(pairs)

    # Kahn's algorithm: repeatedly emit nodes whose dependency count has
    # dropped to zero. We sort the ready set by str() so independent nodes
    # come out in a stable, platform-independent order.
    in_degree: Dict[T, int] = {node: len(dependencies.get(node, ())) for node in nodes}
    ready: List[T] = sorted(
        (node for node in nodes if in_degree[node] == 0),
        key=lambda n: str(n),
    )

    emitted = 0
    while ready:
        node = ready.pop(0)
        yield node
        emitted += 1
        for dependent in sorted(dependents.get(node, ()), key=lambda n: str(n)):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                ready.append(dependent)
        # Re-sort to keep the deterministic emission order. The ready list is
        # small in practice (bounded by the graph width), so this is cheap.
        ready.sort(key=lambda n: str(n))

    if emitted != len(nodes):
        cycle = _find_cycle(dependents, nodes)
        raise CycleError(cycle)

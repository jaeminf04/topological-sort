import unittest

from topological_sort import CycleError, topological_sort


class TestTopologicalSort(unittest.TestCase):
    def test_empty_input(self):
        self.assertEqual(list(topological_sort([])), [])

    def test_single_edge(self):
        # a depends on b -> b before a
        result = list(topological_sort([("a", "b")]))
        self.assertEqual(result, ["b", "a"])

    def test_chain(self):
        # a depends on b, b depends on c -> c, b, a
        result = list(topological_sort([("a", "b"), ("b", "c")]))
        self.assertEqual(result, ["c", "b", "a"])

    def test_diamond(self):
        # a depends on b and c; b and c both depend on d
        pairs = [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")]
        result = list(topological_sort(pairs))
        # d first, then b and c (sorted), then a
        self.assertEqual(result, ["d", "b", "c", "a"])

    def test_independent_nodes_sorted(self):
        # No edges between a, b, c — they should come out sorted by str().
        pairs = [("a", "x"), ("b", "x"), ("c", "x")]
        result = list(topological_sort(pairs))
        self.assertEqual(result, ["x", "a", "b", "c"])

    def test_cycle_simple(self):
        with self.assertRaises(CycleError) as ctx:
            list(topological_sort([("a", "b"), ("b", "a")]))
        cycle = ctx.exception.cycle
        self.assertEqual(cycle[0], cycle[-1])
        self.assertEqual(set(cycle), {"a", "b"})

    def test_cycle_self_loop(self):
        with self.assertRaises(CycleError) as ctx:
            list(topological_sort([("a", "a")]))
        self.assertEqual(ctx.exception.cycle, ["a", "a"])

    def test_cycle_three_nodes(self):
        # a -> b -> c -> a (each depends on the next)
        pairs = [("a", "b"), ("b", "c"), ("c", "a")]
        with self.assertRaises(CycleError) as ctx:
            list(topological_sort(pairs))
        cycle = ctx.exception.cycle
        self.assertEqual(cycle[0], cycle[-1])
        self.assertEqual(len(cycle), 4)
        self.assertEqual(set(cycle), {"a", "b", "c"})

    def test_cycle_with_tail(self):
        # d depends on a; a, b, c form a cycle
        pairs = [("d", "a"), ("a", "b"), ("b", "c"), ("c", "a")]
        with self.assertRaises(CycleError) as ctx:
            list(topological_sort(pairs))
        cycle = ctx.exception.cycle
        self.assertEqual(cycle[0], cycle[-1])
        self.assertIn("a", cycle)
        self.assertIn("b", cycle)
        self.assertIn("c", cycle)
        self.assertNotIn("d", cycle)

    def test_cycle_message_readable(self):
        with self.assertRaises(CycleError) as ctx:
            list(topological_sort([("a", "b"), ("b", "a")]))
        self.assertIn("cycle detected", str(ctx.exception))
        self.assertIn("a", str(ctx.exception))
        self.assertIn("b", str(ctx.exception))

    def test_no_yield_before_cycle_error(self):
        # The contract is that CycleError is raised before any node is
        # yielded. We collect into a list so a partial yield is observable.
        pairs = [("a", "b"), ("b", "a")]
        collected = []
        gen = topological_sort(pairs)
        with self.assertRaises(CycleError):
            for node in gen:
                collected.append(node)
        self.assertEqual(collected, [])

    def test_integer_nodes(self):
        pairs = [(1, 2), (2, 3)]
        result = list(topological_sort(pairs))
        self.assertEqual(result, [3, 2, 1])

    def test_mixed_type_nodes(self):
        # Nodes of different types are ordered by str() representation.
        pairs = [(1, "two"), ("two", 3)]
        result = list(topological_sort(pairs))
        # 3 has no dependencies, then "two", then 1
        self.assertEqual(result, [3, "two", 1])

    def test_duplicate_edges(self):
        # Duplicate edges should not affect in-degree counting.
        pairs = [("a", "b"), ("a", "b"), ("b", "c")]
        result = list(topological_sort(pairs))
        self.assertEqual(result, ["c", "b", "a"])

    def test_disconnected_components(self):
        # Two independent chains in one graph.
        pairs = [("a", "b"), ("c", "d")]
        result = list(topological_sort(pairs))
        # b, d sorted; then a becomes ready before c, so a, then d, then c
        self.assertEqual(result, ["b", "a", "d", "c"])


if __name__ == "__main__":
    unittest.main()

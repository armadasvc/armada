import numpy as np

from fantomas.virtual_cursor_path import VirtualCursorPath


class TestAvoidBounds:
    def test_replaces_min(self):
        result = VirtualCursorPath._avoid_bounds([0, 500, 1000], 0, 1000)
        assert result[0] == 1

    def test_replaces_max(self):
        result = VirtualCursorPath._avoid_bounds([0, 500, 1000], 0, 1000)
        assert result[2] == 999

    def test_middle_unchanged(self):
        result = VirtualCursorPath._avoid_bounds([0, 500, 1000], 0, 1000)
        assert result[1] == 500

    def test_empty_array(self):
        result = VirtualCursorPath._avoid_bounds([], 0, 1000)
        assert result == []

    def test_all_bounds(self):
        result = VirtualCursorPath._avoid_bounds([0, 0, 1000, 1000], 0, 1000)
        assert result == [1, 1, 999, 999]


class TestCalculatePath:
    def test_returns_two_arrays(self):
        path = VirtualCursorPath._calculate_path(0, 0, 100, 200, 1000, 1000)
        assert len(path) == 2

    def test_arrays_same_length(self):
        path = VirtualCursorPath._calculate_path(0, 0, 100, 200, 1000, 1000)
        assert len(path[0]) == len(path[1])

    def test_path_has_points(self):
        path = VirtualCursorPath._calculate_path(0, 0, 500, 500, 1000, 1000)
        assert len(path[0]) > 1

    def test_coords_within_bounds(self):
        path = VirtualCursorPath._calculate_path(0, 0, 800, 600, 1000, 1000)
        for x in path[0]:
            assert 0 <= x <= 1000
        for y in path[1]:
            assert 0 <= y <= 1000

    def test_ends_near_destination(self):
        path = VirtualCursorPath._calculate_path(0, 0, 500, 500, 1000, 1000)
        if len(path[0]) > 0:
            assert abs(path[0][-1] - 500) < 50
            assert abs(path[1][-1] - 500) < 50

    def test_reproducible_with_seed(self):
        np.random.seed(42)
        path1 = VirtualCursorPath._calculate_path(0, 0, 100, 200, 1000, 1000)
        np.random.seed(42)
        path2 = VirtualCursorPath._calculate_path(0, 0, 100, 200, 1000, 1000)
        assert path1 == path2


class TestGetVirtualCursorPath:
    def test_basic_path(self):
        vcp = VirtualCursorPath()
        path = vcp.get_virtual_cursor_path([0, 0], [500, 500], 1000, 1000)
        assert len(path) == 2
        assert len(path[0]) == len(path[1])

    def test_bounds_avoided(self):
        vcp = VirtualCursorPath()
        path = vcp.get_virtual_cursor_path([0, 0], [999, 999], 1000, 1000)
        for x in path[0]:
            assert x != 0 or x == 1
            assert x != 1000
        for y in path[1]:
            assert y != 0 or y == 1
            assert y != 1000

    def test_extremes(self):
        vcp = VirtualCursorPath()
        path = vcp.get_virtual_cursor_path([0, 0], [999, 999], 1000, 1000)
        assert len(path[0]) > 0

    def test_same_start_and_end(self):
        """Same start/end should produce empty or very short path."""
        vcp = VirtualCursorPath()
        path = vcp.get_virtual_cursor_path([100, 100], [100, 100], 1000, 1000)
        assert isinstance(path, list)
        assert len(path) == 2


class TestPathPhysicsQuality:
    """Tests that the cursor simulation behaves like a real cursor,
    not like a random walk or a teleportation."""

    def test_no_teleportation(self):
        """Consecutive points must not jump more than a reasonable distance."""
        vcp = VirtualCursorPath()
        for _ in range(5):
            path = vcp.get_virtual_cursor_path([0, 0], [800, 600], 1000, 1000)
            xs, ys = path
            for i in range(1, len(xs)):
                dx = abs(xs[i] - xs[i - 1])
                dy = abs(ys[i] - ys[i - 1])
                jump = (dx ** 2 + dy ** 2) ** 0.5
                assert jump < 100, f"Teleportation detected: jump of {jump:.0f}px at step {i}"

    def test_convergence_many_destinations(self):
        """The path must converge near the destination for various targets."""
        vcp = VirtualCursorPath()
        targets = [(100, 100), (900, 100), (500, 500), (100, 900), (900, 900)]
        for dx, dy in targets:
            path = vcp.get_virtual_cursor_path([500, 500], [dx, dy], 1000, 1000)
            xs, ys = path
            if len(xs) > 0:
                final_dist = ((xs[-1] - dx) ** 2 + (ys[-1] - dy) ** 2) ** 0.5
                assert final_dist < 60, (
                    f"Path to ({dx},{dy}) ended at ({xs[-1]},{ys[-1]}), "
                    f"distance={final_dist:.0f}px"
                )

    def test_path_length_scales_with_distance(self):
        """A longer physical distance should produce a longer path (more points)."""
        vcp = VirtualCursorPath()
        np.random.seed(123)
        short = vcp.get_virtual_cursor_path([0, 0], [50, 50], 1000, 1000)
        np.random.seed(123)
        long = vcp.get_virtual_cursor_path([0, 0], [900, 900], 1000, 1000)
        assert len(long[0]) > len(short[0])

    def test_no_negative_coordinates(self):
        """Coordinates must never be negative after bounds avoidance."""
        vcp = VirtualCursorPath()
        for _ in range(10):
            path = vcp.get_virtual_cursor_path([0, 0], [500, 500], 1000, 1000)
            for x in path[0]:
                assert x >= 0
            for y in path[1]:
                assert y >= 0

    def test_small_viewport(self):
        """Path should work correctly with a very small viewport."""
        vcp = VirtualCursorPath()
        path = vcp.get_virtual_cursor_path([0, 0], [5, 5], 10, 10)
        for x in path[0]:
            assert 0 <= x <= 10
        for y in path[1]:
            assert 0 <= y <= 10

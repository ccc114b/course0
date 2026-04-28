"""Tests for Line class."""

import pytest
import geom4py as geom


class TestLineCreation:
    def test_create_line(self):
        p = geom.Point(0, 0, 0)
        v = geom.Vector(1, 0, 0)
        line = geom.Line(p, v)
        assert line.point == p
        assert line.direction == v.normalize()

    def test_from_points(self):
        p1 = geom.Point(0, 0, 0)
        p2 = geom.Point(1, 0, 0)
        line = geom.Line.from_points(p1, p2)
        assert line.direction == geom.Vector(1, 0, 0)


class TestLineMethods:
    def test_point_at(self):
        p = geom.Point(0, 0, 0)
        v = geom.Vector(1, 0, 0)
        line = geom.Line(p, v)
        pt = line.point_at(5)
        assert pt == geom.Point(5, 0, 0)

    def test_distance_to_point(self):
        line = geom.Line(geom.Point(0,0,0), geom.Vector(1,0,0))
        p = geom.Point(0, 1, 0)
        assert abs(line.distance_to_point(p) - 1.0) < 1e-9

    def test_closest_point(self):
        line = geom.Line(geom.Point(0,0,0), geom.Vector(1,0,0))
        p = geom.Point(0, 2, 0)
        closest = line.closest_point(p)
        assert closest == geom.Point(0, 0, 0)


class TestLineRelations:
    def test_is_parallel(self):
        v = geom.Vector(1, 0, 0)
        line1 = geom.Line(geom.Point(0,0,0), v)
        line2 = geom.Line(geom.Point(0,1,0), v)
        assert line1.is_parallel_to(line2)

    def test_is_perpendicular(self):
        v1 = geom.Vector(1, 0, 0)
        v2 = geom.Vector(0, 1, 0)
        line1 = geom.Line(geom.Point(0,0,0), v1)
        line2 = geom.Line(geom.Point(0,0,0), v2)
        assert line1.is_perpendicular_to(line2)
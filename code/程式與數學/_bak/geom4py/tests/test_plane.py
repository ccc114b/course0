"""Tests for Plane class."""

import pytest
import geom4py as geom


class TestPlaneCreation:
    def test_create_plane(self):
        p = geom.Point(0, 0, 0)
        n = geom.Vector(0, 0, 1)
        plane = geom.Plane(p, n)
        assert plane.point == p
        assert plane.normal == n.normalize()

    def test_from_points(self):
        p1 = geom.Point(0, 0, 0)
        p2 = geom.Point(1, 0, 0)
        p3 = geom.Point(0, 1, 0)
        plane = geom.Plane.from_points(p1, p2, p3)
        assert plane.normal == geom.Vector(0, 0, 1)


class TestPlaneMethods:
    def test_contains_point(self):
        plane = geom.Plane(geom.Point(0,0,0), geom.Vector(0,0,1))
        p = geom.Point(1, 1, 0)
        assert plane.contains_point(p)

    def test_distance_to_point(self):
        plane = geom.Plane(geom.Point(0,0,0), geom.Vector(0,0,1))
        p = geom.Point(1, 1, 1)
        assert abs(plane.distance_to_point(p) - 1.0) < 1e-9

    def test_project_point(self):
        plane = geom.Plane(geom.Point(0,0,0), geom.Vector(0,0,1))
        p = geom.Point(1, 1, 5)
        projected = plane.project_point(p)
        assert projected == geom.Point(1, 1, 0)

    def test_line_intersection(self):
        plane = geom.Plane(geom.Point(0,0,0), geom.Vector(0,0,1))
        line = geom.Line(geom.Point(0,0,1), geom.Vector(1,0,-1))
        pt = plane.line_intersection(line)
        assert pt == geom.Point(1, 0, 0)


class TestPlaneRelations:
    def test_is_parallel(self):
        n = geom.Vector(0, 0, 1)
        plane1 = geom.Plane(geom.Point(0,0,0), n)
        plane2 = geom.Plane(geom.Point(0,0,1), n)
        assert plane1.is_parallel_to(plane2)

    def test_is_perpendicular(self):
        n1 = geom.Vector(0, 0, 1)
        n2 = geom.Vector(1, 0, 0)
        plane1 = geom.Plane(geom.Point(0,0,0), n1)
        plane2 = geom.Plane(geom.Point(0,0,0), n2)
        assert plane1.is_perpendicular_to(plane2)
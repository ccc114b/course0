"""Line Intersection Examples - Example for geom4py."""

import geom4py as geom


def main():
    print("=== Line Distance and Closest Point ===\n")

    line = geom.Line.from_points(
        geom.Point(0, 0, 0),
        geom.Point(1, 0, 0)
    )
    print(f"Line: {line}")

    p = geom.Point(0, 2, 0)
    print(f"Point: {p}")

    dist = line.distance_to_point(p)
    print(f"Distance from point to line: {dist}")

    closest = line.closest_point(p)
    print(f"Closest point on line: {closest}")

    print("\n--- 3D Example ---")
    line2 = geom.Line.from_points(
        geom.Point(0, 0, 0),
        geom.Point(1, 1, 1)
    )
    print(f"Line: {line2}")

    p2 = geom.Point(1, 0, 0)
    print(f"Point: {p2}")

    dist2 = line2.distance_to_point(p2)
    print(f"Distance from point to line: {dist2:.4f}")

    closest2 = line2.closest_point(p2)
    print(f"Closest point on line: {closest2}")


if __name__ == "__main__":
    main()
# geom4py

A lightweight 3D geometry library for Python.

## Installation

```bash
pip install geom4py
```

## Quick Start

```python
import geom4py as geom

# Create vectors
v1 = geom.Vector(1, 0, 0)
v2 = geom.Vector(0, 1, 0)

# Vector operations
print(v1.cross(v2))  # Vector(0, 0, 1)
print(v1.dot(v2))    # 0

# Create points and lines
line = geom.Line.from_points(geom.Point(0, 0, 0), geom.Point(1, 0, 0))
print(line.distance_to_point(geom.Point(0, 1, 0)))  # 1.0

# Create planes
plane = geom.Plane(geom.Point(0, 0, 0), geom.Vector(0, 0, 1))
print(plane.distance_to_point(geom.Point(1, 1, 1)))  # 1.0
```

## Features

- **Vector**: dot product, cross product, normalization, angle calculation
- **Point**: distance calculation, vector conversion
- **Line**: point projection, closest point, distance to point
- **Plane**: point projection, distance calculation, line intersection

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
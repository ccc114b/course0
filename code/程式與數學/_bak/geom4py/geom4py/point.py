"""Point class for 3D points."""

import numpy as np
from .vector import Vector


class Point:
    """A 3D point class supporting basic geometric operations."""

    def __init__(self, x: float, y: float, z: float):
        """Initialize a 3D point.

        Args:
            x: x coordinate
            y: y coordinate
            z: z coordinate
        """
        self._data = np.array([x, y, z], dtype=float)

    @property
    def x(self) -> float:
        return self._data[0]

    @property
    def y(self) -> float:
        return self._data[1]

    @property
    def z(self) -> float:
        return self._data[2]

    def __repr__(self) -> str:
        return f"Point({self.x}, {self.y}, {self.z})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Point):
            return False
        return np.allclose(self._data, other._data)

    def __add__(self, other: Vector) -> "Point":
        if not isinstance(other, Vector):
            return NotImplemented
        return Point(*(self._data + other._data))

    def __sub__(self, other: "Point | Vector") -> "Point | Vector":
        if isinstance(other, Vector):
            return Point(*(self._data - other._data))
        if isinstance(other, Point):
            return Vector(*(self._data - other._data))
        return NotImplemented

    def distance_to(self, other: "Point") -> float:
        """Compute distance to another point."""
        if not isinstance(other, Point):
            return NotImplemented
        return float(np.linalg.norm(self._data - other._data))

    def to_vector(self) -> Vector:
        """Convert to vector from origin."""
        return Vector(self.x, self.y, self.z)

    def to_array(self) -> np.ndarray:
        """Return as numpy array."""
        return self._data.copy()
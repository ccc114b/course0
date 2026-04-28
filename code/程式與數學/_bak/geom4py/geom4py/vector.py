"""Vector class for 3D vectors."""

import numpy as np


class Vector:
    """A 3D vector class supporting basic vector operations."""

    def __init__(self, x: float, y: float, z: float):
        """Initialize a 3D vector.

        Args:
            x: x component
            y: y component
            z: z component
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
        return f"Vector({self.x}, {self.y}, {self.z})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector):
            return False
        return np.allclose(self._data, other._data)

    def __add__(self, other: "Vector") -> "Vector":
        if not isinstance(other, Vector):
            return NotImplemented
        return Vector(*(self._data + other._data))

    def __sub__(self, other: "Vector") -> "Vector":
        if not isinstance(other, Vector):
            return NotImplemented
        return Vector(*(self._data - other._data))

    def __mul__(self, scalar: float) -> "Vector":
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        return Vector(*(self._data * scalar))

    def __rmul__(self, scalar: float) -> "Vector":
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> "Vector":
        if not isinstance(scalar, (int, float)):
            return NotImplemented
        if scalar == 0:
            raise ValueError("Division by zero")
        return Vector(*(self._data / scalar))

    def __neg__(self) -> "Vector":
        return Vector(*(-self._data))

    def dot(self, other: "Vector") -> float:
        """Compute dot product with another vector."""
        if not isinstance(other, Vector):
            return NotImplemented
        return float(np.dot(self._data, other._data))

    def cross(self, other: "Vector") -> "Vector":
        """Compute cross product with another vector."""
        if not isinstance(other, Vector):
            return NotImplemented
        result = np.cross(self._data, other._data)
        return Vector(result[0], result[1], result[2])

    def norm(self) -> float:
        """Return the magnitude (length) of the vector."""
        return float(np.linalg.norm(self._data))

    def normalize(self) -> "Vector":
        """Return the unit vector (normalized)."""
        n = self.norm()
        if n == 0:
            raise ValueError("Cannot normalize zero vector")
        return self / n

    def angle_to(self, other: "Vector") -> float:
        """Return angle in radians to another vector."""
        if not isinstance(other, Vector):
            return NotImplemented
        dot_prod = self.dot(other)
        norms = self.norm() * other.norm()
        if norms == 0:
            raise ValueError("Cannot compute angle with zero vector")
        cos_angle = np.clip(dot_prod / norms, -1.0, 1.0)
        return float(np.arccos(cos_angle))

    def is_parallel(self, other: "Vector", tol: float = 1e-9) -> bool:
        """Check if vectors are parallel."""
        if not isinstance(other, Vector):
            return False
        return self.cross(other).norm() < tol

    def is_perpendicular(self, other: "Vector", tol: float = 1e-9) -> bool:
        """Check if vectors are perpendicular."""
        if not isinstance(other, Vector):
            return False
        return abs(self.dot(other)) < tol

    def to_array(self) -> np.ndarray:
        """Return as numpy array."""
        return self._data.copy()
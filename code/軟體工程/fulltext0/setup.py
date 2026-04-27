"""Setup for fulltext0 package."""
from setuptools import setup

setup(
    name='fulltext0',
    version='0.1.0',
    packages=['fulltext0'],
    package_dir={'': 'src'},
    package_data={'fulltext0': ['py.typed']},
    zip_safe=False,
)
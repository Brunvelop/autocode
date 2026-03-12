"""
Autocode - Minimalistic framework for code quality tools
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("autocode")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"

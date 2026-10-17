"""Cauce: celdas inmutables, tipos estáticos y publicación validada."""

from .runtime import run, check
from .syntax import CauceError

__all__ = ["run", "check", "CauceError"]
__version__ = "0.1.0"

"""Geometric position of a state on the editor canvas.

Summary (UA): Координати стану на canvas редактора.
Summary (EN): 2-D coordinate for placing a state in the GUI editor.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Position(BaseModel):
    """Canvas coordinates in logical (scene) units."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    x: float = 0.0
    y: float = 0.0

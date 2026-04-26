"""Shared test fixtures.

The integration's package (``custom_components/sec_smart``) imports
Home Assistant modules at package import time (in ``__init__.py``,
``coordinator.py``, ``fan.py``). To exercise the leaf modules that do
not depend on Home Assistant — currently ``api.py`` and ``models.py`` —
we add the integration directory to ``sys.path`` so they can be
imported as top-level modules. Tests that require Home Assistant
itself will need a heavier setup and are out of scope here.
"""
from __future__ import annotations

import sys
from pathlib import Path

INTEGRATION = Path(__file__).resolve().parents[1] / "custom_components" / "sec_smart"
if str(INTEGRATION) not in sys.path:
    sys.path.insert(0, str(INTEGRATION))

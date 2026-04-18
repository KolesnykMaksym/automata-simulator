"""Qt translation assets (.ts / .qm) and the runtime language switcher."""

from __future__ import annotations

from automata_simulator.gui.i18n.translations import TRANSLATIONS_UA
from automata_simulator.gui.i18n.translator import DictTranslator, Locale, apply_locale

__all__ = ["DictTranslator", "Locale", "TRANSLATIONS_UA", "apply_locale"]

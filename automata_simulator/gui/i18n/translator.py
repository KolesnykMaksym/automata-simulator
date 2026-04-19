"""Dict-backed QTranslator + locale manager for the GUI.

Summary (UA): Легкий QTranslator, що бере переклади зі словника Python, без
потреби в ``lrelease`` і ``.qm``-файлах. ``Locale`` — перелічення доступних
мов; ``apply_locale`` хот-свопує перекладач у ``QApplication``.
Summary (EN): A lightweight ``QTranslator`` backed by a plain Python dict, so
we can ship translations without the ``lrelease`` / ``.qm`` toolchain.
``apply_locale`` hot-swaps the active translator on the given QApplication.
"""

from __future__ import annotations

from enum import StrEnum

from PySide6.QtCore import QTranslator
from PySide6.QtWidgets import QApplication

from automata_simulator.gui.i18n.translations import TRANSLATIONS_UA


class Locale(StrEnum):
    """Supported GUI locales."""

    EN = "en"
    UA = "ua"


class DictTranslator(QTranslator):
    """QTranslator whose source is a plain ``dict[str, str]``."""

    def __init__(self, mapping: dict[str, str]) -> None:
        super().__init__()
        self._mapping = mapping

    def translate(
        self,
        context: str,  # noqa: ARG002 — Qt callback shape
        source_text: str,
        disambiguation: str | None = None,  # noqa: ARG002 — Qt callback shape
        n: int = -1,  # noqa: ARG002 — Qt callback shape
    ) -> str:
        """Return the Ukrainian rendering of ``source_text`` or the source as fallback.

        PySide6 treats an empty return as a valid (empty) translation — so we
        must fall back to the source text when a key is missing, otherwise
        every un-translated widget silently loses its label.
        """
        return self._mapping.get(source_text, source_text)


_CURRENT_TRANSLATOR: QTranslator | None = None


def apply_locale(app: QApplication, locale: Locale) -> None:
    """Install the translator for ``locale`` on ``app``.

    Sends a ``LanguageChange`` event to every widget so they can refresh
    their displayed strings.
    """
    global _CURRENT_TRANSLATOR  # noqa: PLW0603 — one process-wide active translator
    if _CURRENT_TRANSLATOR is not None:
        app.removeTranslator(_CURRENT_TRANSLATOR)
        _CURRENT_TRANSLATOR = None
    if locale is Locale.UA:
        translator = DictTranslator(TRANSLATIONS_UA)
        app.installTranslator(translator)
        _CURRENT_TRANSLATOR = translator
    # Locale.EN: no translator → self.tr() returns source text unchanged.

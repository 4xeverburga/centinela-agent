from types import ModuleType

from app.domain.prompts import es, en

_LOCALES: dict[str, ModuleType] = {
    "es": es,
    "en": en,
}


def get_locale(locale: str) -> ModuleType:
    return _LOCALES.get(locale, es)

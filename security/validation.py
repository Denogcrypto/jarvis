import re
import unicodedata


SENSITIVE_TERMS = re.compile(
    r"\b(contrase(?:ñ|n)a|password|api[ -]?key|clave secreta|token|cvv|cvc|"
    r"tarjeta de cr[eé]dito|n[uú]mero de tarjeta|dato bancario)\b",
    re.IGNORECASE,
)


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.casefold())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def contains_sensitive_data(text: str) -> bool:
    return bool(SENSITIVE_TERMS.search(text))


def safe_note_name(name: str) -> str:
    cleaned = re.sub(r"[^\w -]", "", name, flags=re.UNICODE).strip(" .-")[:56]
    return cleaned or "Nota"

class TranslationError(RuntimeError):
    pass


class TextTranslator:
    def translate(self, text: str, target_language: str) -> str:
        if not text.strip():
            raise TranslationError("No text to translate.")
        try:
            from deep_translator import GoogleTranslator
        except ImportError as exc:
            raise TranslationError("Install translation dependency: pip install deep-translator") from exc

        chunks = _split_text(text, max_chars=3500)
        translated = []
        for chunk in chunks:
            translated.append(GoogleTranslator(source="auto", target=target_language).translate(chunk))
        return "\n\n".join(translated)


def _split_text(text: str, max_chars: int) -> list[str]:
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(paragraph) <= max_chars:
            current = paragraph
        else:
            for start in range(0, len(paragraph), max_chars):
                chunks.append(paragraph[start : start + max_chars])
            current = ""
    if current:
        chunks.append(current)
    return chunks


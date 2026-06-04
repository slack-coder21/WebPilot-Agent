from webpilot.models import ResearchItem


class ResultVerifier:
    def verify(self, items: list[ResearchItem], min_items: int) -> tuple[bool, str]:
        if len(items) < min_items:
            return False, f"expected at least {min_items} items, got {len(items)}"
        missing = [item.title for item in items if not item.title or not item.url]
        if missing:
            return False, "some items are missing title or url"
        return True, "ok"


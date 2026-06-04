from playwright.sync_api import Page

from webpilot.models import InteractiveElement, PageObservation


INTERACTIVE_SELECTOR = "a, button, input, textarea, select"


def observe_page(page: Page, max_text_chars: int = 4000, max_elements: int = 80) -> PageObservation:
    """Convert a browser page into a compact, model-friendly observation."""
    visible_text = page.locator("body").inner_text(timeout=5000) if page.locator("body").count() else ""
    elements: list[InteractiveElement] = []

    locators = page.locator(INTERACTIVE_SELECTOR)
    count = min(locators.count(), max_elements)
    for idx in range(count):
        locator = locators.nth(idx)
        try:
            if not locator.is_visible(timeout=500):
                continue
            tag = locator.evaluate("el => el.tagName.toLowerCase()")
            text = (locator.inner_text(timeout=500) if tag not in {"input", "textarea"} else "")[:120]
            placeholder = locator.get_attribute("placeholder") or ""
            role = locator.get_attribute("role") or ""
            selector = _selector_for(idx)
            elements.append(
                InteractiveElement(
                    element_id=f"e{len(elements) + 1}",
                    tag=tag,
                    text=" ".join(text.split()),
                    placeholder=placeholder,
                    role=role,
                    selector=selector,
                )
            )
        except Exception:
            continue

    return PageObservation(
        url=page.url,
        title=page.title(),
        visible_text=visible_text[:max_text_chars],
        interactive_elements=elements,
    )


def _selector_for(index: int) -> str:
    return f"{INTERACTIVE_SELECTOR} >> nth={index}"


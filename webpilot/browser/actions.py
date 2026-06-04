from playwright.sync_api import Page

from webpilot.models import BrowserAction, PageObservation


def execute_action(page: Page, action: BrowserAction, observation: PageObservation) -> str:
    if action.action == "goto":
        if not action.url:
            raise ValueError("goto action requires url")
        page.goto(action.url, wait_until="domcontentloaded", timeout=60000)
        return f"goto {action.url}"

    if action.action in {"click", "type", "select"}:
        element = _find_element(observation, action.target_id)
        if action.action == "click":
            page.locator(element.selector).click(timeout=5000)
            return f"click {action.target_id}"
        if action.action == "type":
            page.locator(element.selector).fill(action.value or "", timeout=5000)
            return f"type {action.target_id}"
        page.locator(element.selector).select_option(action.value or "", timeout=5000)
        return f"select {action.target_id}"

    if action.action == "scroll":
        direction = action.value or "down"
        delta = 900 if direction == "down" else -900
        page.mouse.wheel(0, delta)
        return f"scroll {direction}"

    if action.action == "wait":
        seconds = float(action.value or 1)
        page.wait_for_timeout(int(seconds * 1000))
        return f"wait {seconds}"

    if action.action in {"extract", "finish"}:
        return action.action

    raise ValueError(f"Unsupported action: {action.action}")


def _find_element(observation: PageObservation, target_id: str | None):
    for element in observation.interactive_elements:
        if element.element_id == target_id:
            return element
    raise ValueError(f"Unknown target element: {target_id}")

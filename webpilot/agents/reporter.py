from webpilot.models import ResearchItem


class MarkdownReporter:
    def render(self, task: str, items: list[ResearchItem], verification_note: str) -> str:
        lines = [
            "# WebPilot Research Report",
            "",
            f"Task: {task}",
            "",
            f"Verification: {verification_note}",
            "",
            "| # | Title | Authors | URL |",
            "|---|---|---|---|",
        ]
        for idx, item in enumerate(items, start=1):
            title = item.title.replace("|", "\\|")
            authors = item.authors.replace("|", "\\|")
            lines.append(f"| {idx} | {title} | {authors} | {item.url} |")
        return "\n".join(lines) + "\n"

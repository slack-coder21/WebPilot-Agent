from pathlib import Path

import click
from rich.console import Console

from webpilot.sites import SUPPORTED_SITES
from webpilot.workflows.research import ResearchWorkflow

console = Console()


@click.group()
def cli() -> None:
    """WebPilot Agent command line interface."""


@cli.command()
@click.option("--task", required=True, help="Natural language research task.")
@click.option("--site", default="arxiv", type=click.Choice(SUPPORTED_SITES), show_default=True)
@click.option("--limit", default=5, show_default=True, help="Maximum number of items to return.")
@click.option("--planner", default="rule", type=click.Choice(["rule", "llm"]), show_default=True)
@click.option("--llm-provider", default="openai", type=click.Choice(["openai", "deepseek"]), show_default=True)
@click.option("--llm-model", default=None, help="Override the provider default model.")
@click.option("--headless/--headed", default=True, show_default=True)
@click.option("--output-dir", default="runs", show_default=True, type=click.Path(path_type=Path))
def run(
    task: str,
    site: str,
    limit: int,
    planner: str,
    llm_provider: str,
    llm_model: str | None,
    headless: bool,
    output_dir: Path,
) -> None:
    """Run one browser research task."""
    workflow = ResearchWorkflow(
        output_dir=output_dir,
        planner_name=planner,
        llm_provider=llm_provider,
        llm_model=llm_model,
    )
    result = workflow.run(task=task, site=site, limit=limit, headless=headless)
    console.print(f"[green]Task finished[/green]: {result.report_path}")
    console.print(f"Items: {len(result.items)}")


if __name__ == "__main__":
    cli()

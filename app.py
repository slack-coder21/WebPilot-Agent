from pathlib import Path

import streamlit as st

from webpilot.i18n import EXAMPLE_TASKS, SITE_LABELS, t
from webpilot.sites import SUPPORTED_SITES
from webpilot.workflows.research import ResearchWorkflow


st.set_page_config(page_title="WebPilot Agent", page_icon="WP", layout="wide")


def main() -> None:
    if "language" not in st.session_state:
        st.session_state["language"] = "zh"
    language = st.session_state["language"]

    title_col, action_col = st.columns([5, 1])
    with title_col:
        st.title(t(language, "page_title"))
        st.caption(t(language, "subtitle"))
    with action_col:
        target_language = "en" if language == "zh" else "zh"
        button_label = "Translate" if language == "zh" else "中文"
        if st.button(button_label, use_container_width=True):
            st.session_state["language"] = target_language
            st.rerun()

    with st.sidebar:
        st.header(t(language, "settings"))
        st.info(t(language, "browser_note"))
        site = st.selectbox(
            t(language, "site"),
            options=list(SUPPORTED_SITES),
            format_func=lambda value: SITE_LABELS[language][value],
        )
        limit = st.slider(t(language, "limit"), min_value=1, max_value=10, value=5)
        planner = st.selectbox(t(language, "planner"), options=["rule", "llm"], index=0)
        headed = st.toggle(t(language, "headed"), value=False)

    task_key = f"task_{language}_{site}"
    if task_key not in st.session_state:
        st.session_state[task_key] = EXAMPLE_TASKS[language][site]

    task = st.text_area(t(language, "task"), key=task_key, height=120)

    top_left, top_right = st.columns([1, 3])
    with top_left:
        run_clicked = st.button(t(language, "run"), type="primary", use_container_width=True)
    with top_right:
        st.code(t(language, "open_hint"), language="text")

    if run_clicked:
        _run_task(task=task, site=site, limit=limit, planner=planner, headed=headed, language=language)

    _render_latest_result(language)


def _run_task(task: str, site: str, limit: int, planner: str, headed: bool, language: str) -> None:
    workflow = ResearchWorkflow(output_dir=Path("runs"), planner_name=planner)
    with st.status(t(language, "running"), expanded=True) as status:
        try:
            result = workflow.run(task=task, site=site, limit=limit, headless=not headed)
        except Exception as exc:
            status.update(label=t(language, "failed"), state="error")
            st.error(str(exc))
        else:
            status.update(label=t(language, "done"), state="complete")
            st.session_state["latest_result"] = result


def _render_latest_result(language: str) -> None:
    result = st.session_state.get("latest_result")
    if not result:
        return

    report_path = Path(result.report_path)
    trace_path = Path(result.trace_path)
    results_path = Path(result.results_path)
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""

    overview, results_tab, report_tab, trace_tab = st.tabs(
        [t(language, "overview"), t(language, "results"), t(language, "report"), t(language, "trace")]
    )

    with overview:
        left, middle, right = st.columns(3)
        left.metric(t(language, "items"), len(result.items))
        middle.metric(t(language, "source"), _source_label(result))
        right.metric(t(language, "output"), str(results_path.parent))

        with st.expander(t(language, "files"), expanded=True):
            st.write(f"Report: `{report_path}`")
            st.write(f"Results: `{results_path}`")
            st.write(f"Trace: `{trace_path}`")

    with results_tab:
        st.dataframe(
            [item.model_dump(mode="json") for item in result.items],
            use_container_width=True,
            hide_index=True,
        )

    with report_tab:
        st.markdown(report_text)

    with trace_tab:
        if trace_path.exists():
            st.json(trace_path.read_text(encoding="utf-8"))


def _source_label(result) -> str:
    sources = sorted({item.source for item in result.items if item.source})
    return ", ".join(sources) if sources else "-"


if __name__ == "__main__":
    main()

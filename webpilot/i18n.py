LANGUAGE_LABELS = {
    "zh": "中文",
    "en": "English",
}


TEXT = {
    "zh": {
        "page_title": "WebPilot Agent",
        "subtitle": "面向技术调研的浏览器自动化 Agent",
        "settings": "任务配置",
        "language": "界面语言",
        "site": "检索站点",
        "limit": "返回数量",
        "planner": "Planner",
        "headed": "显示浏览器窗口",
        "task": "调研任务",
        "run": "运行任务",
        "running": "Agent 正在操作浏览器并抽取结果...",
        "done": "任务完成",
        "failed": "任务失败",
        "overview": "概览",
        "results": "结构化结果",
        "report": "报告",
        "trace": "执行轨迹",
        "files": "运行文件",
        "items": "结果数量",
        "source": "来源",
        "output": "输出目录",
        "translate": "翻译",
        "translation": "翻译结果",
        "translation_settings": "翻译设置",
        "translate_report": "翻译报告",
        "translate_task": "翻译任务",
        "target_language": "目标语言",
        "translation_input": "待翻译文本",
        "translation_placeholder": "输入任意技术文本，或运行任务后翻译报告。",
        "translation_error": "翻译失败",
        "translation_empty": "没有可翻译的文本。",
        "open_hint": "前端运行地址：http://127.0.0.1:8501",
        "browser_note": "站点页面加载失败时，arXiv 会自动使用官方 API 兜底。",
    },
    "en": {
        "page_title": "WebPilot Agent",
        "subtitle": "Browser automation agent for technical research",
        "settings": "Task Settings",
        "language": "UI Language",
        "site": "Search Site",
        "limit": "Result Limit",
        "planner": "Planner",
        "headed": "Show Browser Window",
        "task": "Research Task",
        "run": "Run Task",
        "running": "Agent is operating the browser and extracting results...",
        "done": "Task Complete",
        "failed": "Task Failed",
        "overview": "Overview",
        "results": "Structured Results",
        "report": "Report",
        "trace": "Trace",
        "files": "Run Files",
        "items": "Items",
        "source": "Source",
        "output": "Output",
        "translate": "Translate",
        "translation": "Translation",
        "translation_settings": "Translation Settings",
        "translate_report": "Translate Report",
        "translate_task": "Translate Task",
        "target_language": "Target Language",
        "translation_input": "Text To Translate",
        "translation_placeholder": "Enter technical text, or run a task and translate the report.",
        "translation_error": "Translation failed",
        "translation_empty": "No text to translate.",
        "open_hint": "Frontend URL: http://127.0.0.1:8501",
        "browser_note": "If a site page fails to load, arXiv falls back to its official API.",
    },
}


SITE_LABELS = {
    "zh": {
        "arxiv": "arXiv 论文",
        "github": "GitHub 仓库",
        "huggingface": "HuggingFace 模型",
        "paperswithcode": "Papers / Papers with Code",
    },
    "en": {
        "arxiv": "arXiv Papers",
        "github": "GitHub Repositories",
        "huggingface": "HuggingFace Models",
        "paperswithcode": "Papers / Papers with Code",
    },
}


EXAMPLE_TASKS = {
    "zh": {
        "arxiv": "在 arXiv 搜索 RAG evaluation，返回前 5 篇论文标题和链接",
        "github": "在 GitHub 搜索 LangGraph examples，返回前 5 个仓库标题和链接",
        "huggingface": "在 HuggingFace 搜索 RAG embedding，返回前 5 个模型标题和链接",
        "paperswithcode": "在 Papers with Code 搜索 object detection，返回前 5 个论文标题和链接",
    },
    "en": {
        "arxiv": "Search arXiv for RAG evaluation and return the top 5 paper titles and links",
        "github": "Search GitHub for LangGraph examples and return the top 5 repositories and links",
        "huggingface": "Search HuggingFace for RAG embedding and return the top 5 models and links",
        "paperswithcode": (
            "Search Papers with Code for object detection and return the top 5 paper titles and links"
        ),
    },
}


TARGET_LANGUAGES = {
    "zh": {
        "zh-CN": "中文",
        "en": "英文",
        "ja": "日文",
        "ko": "韩文",
    },
    "en": {
        "zh-CN": "Chinese",
        "en": "English",
        "ja": "Japanese",
        "ko": "Korean",
    },
}


def t(language: str, key: str) -> str:
    return TEXT[language][key]


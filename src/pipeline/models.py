"""流水线状态模型"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent.parent.parent / "content" / "pipeline"


@dataclass
class PipelineState:
    pipeline_id: str = ""
    created_at: str = ""
    current_stage: str = "search"
    status: str = "running"  # running / paused / completed / failed

    # 各阶段产出
    pool_path: str = ""
    plan_result: dict = field(default_factory=dict)
    selected_topic: str = ""
    selected_sources: list[str] = field(default_factory=list)
    draft_path: str = ""
    cards_path: str = ""
    review_score: int = 0
    review_passed: bool = False
    review_feedback: str = ""
    publish_results: list[dict] = field(default_factory=list)

    # 配置
    sources: str = "rss,hn,github,hot,tavily,youtube_api"
    direction: str = ""
    platforms: str = ""
    no_cards: bool = False

    error: str = ""
    history: list[dict] = field(default_factory=list)

    def __post_init__(self):
        if not self.pipeline_id:
            self.pipeline_id = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def log(self, stage: str, message: str):
        self.history.append({
            "stage": stage,
            "message": message,
            "time": datetime.now().isoformat(),
        })

    def save(self) -> Path:
        PIPELINE_DIR.mkdir(parents=True, exist_ok=True)
        path = PIPELINE_DIR / f"{self.pipeline_id}.json"
        path.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def load(cls, pipeline_id: str) -> "PipelineState":
        path = PIPELINE_DIR / f"{pipeline_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"流水线不存在: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(**data)

    @classmethod
    def find_latest(cls) -> "PipelineState | None":
        if not PIPELINE_DIR.exists():
            return None
        files = sorted(PIPELINE_DIR.glob("*.json"), reverse=True)
        if not files:
            return None
        data = json.loads(files[0].read_text(encoding="utf-8"))
        return cls(**data)

    @classmethod
    def list_recent(cls, limit: int = 20) -> list["PipelineState"]:
        if not PIPELINE_DIR.exists():
            return []
        files = sorted(PIPELINE_DIR.glob("*.json"), reverse=True)[:limit]
        states = []
        for file in files:
            data = json.loads(file.read_text(encoding="utf-8"))
            states.append(cls(**data))
        return states

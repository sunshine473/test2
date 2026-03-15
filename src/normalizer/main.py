"""整理层编排：清洗 + 去重聚类 + 物化 MaterialPool。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from models import MaterialPool, RawMaterial

from .cleaner import clean_materials
from .dedup import Deduplicator
from .translator import translate_materials


def normalize(raw_items: list[Any], source_stats: dict[str, int] | None = None) -> MaterialPool:
    materials = [
        item if isinstance(item, RawMaterial) else RawMaterial.from_collected_item(item)
        for item in raw_items
    ]
    cleaned = clean_materials(materials)
    translated = translate_materials(cleaned)

    deduplicator = Deduplicator()
    dedup_items, clusters = deduplicator.process([item.to_collected_item() for item in translated])
    cluster_summary = deduplicator.summarize_clusters(clusters)

    return MaterialPool(
        date=datetime.now().strftime("%Y-%m-%d"),
        stage="normalize",
        raw_total=len(raw_items),
        source_stats=source_stats or {},
        dedup_total=len(dedup_items),
        cluster_summary=cluster_summary,
        items=[RawMaterial.from_collected_item(item) for item in dedup_items],
    )


def save_material_pool(pool: MaterialPool, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pool.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return path

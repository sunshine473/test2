"""内容质量审核模块 — AI 自动评估文章质量，不合格则打回重写。

评估维度：
1. 标题吸引力（20分）
2. 开头钩子（15分）
3. 内容结构（20分）
4. 逻辑连贯性（15分）
5. 可读性（15分）
6. 信息密度（15分）

总分 >= 70 分通过，< 70 分打回重写。
"""

import os
from dataclasses import dataclass
from pathlib import Path

from generator.gemini_client import generate_text


@dataclass
class QualityScore:
    """质量评分结果"""

    title_score: int  # 标题吸引力 (0-20)
    opening_score: int  # 开头钩子 (0-15)
    structure_score: int  # 内容结构 (0-20)
    logic_score: int  # 逻辑连贯性 (0-15)
    readability_score: int  # 可读性 (0-15)
    density_score: int  # 信息密度 (0-15)

    title_feedback: str = ""
    opening_feedback: str = ""
    structure_feedback: str = ""
    logic_feedback: str = ""
    readability_feedback: str = ""
    density_feedback: str = ""

    @property
    def total_score(self) -> int:
        return (
            self.title_score
            + self.opening_score
            + self.structure_score
            + self.logic_score
            + self.readability_score
            + self.density_score
        )

    @property
    def passed(self) -> bool:
        return self.total_score >= 70

    def get_feedback(self) -> str:
        """生成详细反馈报告"""
        lines = [
            f"# 内容质量评估报告",
            f"",
            f"**总分: {self.total_score}/100** {'✅ 通过' if self.passed else '❌ 不合格'}",
            f"",
            f"## 评分详情",
            f"",
            f"### 1. 标题吸引力 ({self.title_score}/20)",
            self.title_feedback,
            f"",
            f"### 2. 开头钩子 ({self.opening_score}/15)",
            self.opening_feedback,
            f"",
            f"### 3. 内容结构 ({self.structure_score}/20)",
            self.structure_feedback,
            f"",
            f"### 4. 逻辑连贯性 ({self.logic_score}/15)",
            self.logic_feedback,
            f"",
            f"### 5. 可读性 ({self.readability_score}/15)",
            self.readability_feedback,
            f"",
            f"### 6. 信息密度 ({self.density_score}/15)",
            self.density_feedback,
            f"",
        ]

        if not self.passed:
            lines.extend(
                [
                    f"## 改进建议",
                    f"",
                    f"文章未达到发布标准（70分），需要重写。请重点关注：",
                    f"",
                ]
            )
            # 找出得分最低的 3 个维度
            scores = [
                (self.title_score, "标题吸引力"),
                (self.opening_score, "开头钩子"),
                (self.structure_score, "内容结构"),
                (self.logic_score, "逻辑连贯性"),
                (self.readability_score, "可读性"),
                (self.density_score, "信息密度"),
            ]
            scores.sort()
            for score, name in scores[:3]:
                lines.append(f"- **{name}** (当前 {score} 分)")

        return "\n".join(lines)


def review_article(draft_path: str | Path) -> QualityScore:
    """使用 Gemini 评估文章质量"""
    draft_path = Path(draft_path)
    if not draft_path.exists():
        raise FileNotFoundError(f"草稿文件不存在: {draft_path}")

    content = draft_path.read_text(encoding="utf-8")

    # 复用统一 Gemini 客户端配置，避免 reviewer 与 generator 依赖漂移。
    if not (os.getenv("GOOGLE_API_KEY") or os.getenv("YOUTUBE_API_KEY") or os.getenv("GEMINI_API_KEY")):
        raise ValueError("未配置 GOOGLE_API_KEY / YOUTUBE_API_KEY / GEMINI_API_KEY")

    prompt = f"""你是一位资深内容编辑，负责评估文章质量。请按以下 6 个维度对文章打分，并给出具体反馈。

# 评分标准

## 1. 标题吸引力 (0-20分)
- 是否有悬念、冲突、反常识？
- 是否包含数字、具体场景？
- 是否简洁有力（15字以内）？
- 是否避免标题党（夸大、误导）？

## 2. 开头钩子 (0-15分)
- 前 3 句是否抓住读者注意力？
- 是否用故事、数据、问题开场？
- 是否快速切入主题（不啰嗦）？

## 3. 内容结构 (0-20分)
- 是否有清晰的逻辑框架（总分总、递进、对比）？
- 段落是否短小精悍（3-5 行）？
- 是否有小标题、列表、引用等排版元素？
- 是否有节奏感（快慢结合）？

## 4. 逻辑连贯性 (0-15分)
- 论点是否清晰？
- 论据是否充分？
- 段落之间是否有过渡？
- 是否有逻辑跳跃或自相矛盾？

## 5. 可读性 (0-15分)
- 语言是否简洁流畅？
- 是否避免专业术语堆砌？
- 是否有具体案例、比喻？
- 是否有情感共鸣？

## 6. 信息密度 (0-15分)
- 是否有新信息、新观点？
- 是否避免废话、套话？
- 是否有数据、引用支撑？
- 是否有实用价值？

# 输出格式

请严格按以下 JSON 格式输出（不要有任何其他文字）：

```json
{{
  "title_score": 15,
  "title_feedback": "标题具体反馈...",
  "opening_score": 12,
  "opening_feedback": "开头具体反馈...",
  "structure_score": 18,
  "structure_feedback": "结构具体反馈...",
  "logic_score": 13,
  "logic_feedback": "逻辑具体反馈...",
  "readability_score": 14,
  "readability_feedback": "可读性具体反馈...",
  "density_score": 12,
  "density_feedback": "信息密度具体反馈..."
}}
```

# 待评估文章

{content}
"""

    result_text = generate_text(prompt, task="summary", temperature=0.2).strip()

    # 提取 JSON（去除可能的 markdown 代码块）
    if "```json" in result_text:
        result_text = result_text.split("```json")[1].split("```")[0].strip()
    elif "```" in result_text:
        result_text = result_text.split("```")[1].split("```")[0].strip()

    import json

    data = json.loads(result_text)

    return QualityScore(
        title_score=data["title_score"],
        opening_score=data["opening_score"],
        structure_score=data["structure_score"],
        logic_score=data["logic_score"],
        readability_score=data["readability_score"],
        density_score=data["density_score"],
        title_feedback=data["title_feedback"],
        opening_feedback=data["opening_feedback"],
        structure_feedback=data["structure_feedback"],
        logic_feedback=data["logic_feedback"],
        readability_feedback=data["readability_feedback"],
        density_feedback=data["density_feedback"],
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python quality_checker.py <草稿路径>")
        sys.exit(1)

    draft = sys.argv[1]
    score = review_article(draft)
    print(score.get_feedback())

    if not score.passed:
        sys.exit(1)

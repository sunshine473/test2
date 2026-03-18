---
name: batch-factory
description: This skill should be used when users want to generate and publish multiple articles in batch mode. It automates the complete content production pipeline from material collection to multi-platform distribution, producing 4 articles by default (2 AI-related + 2 automotive) and publishing them to Xiaohongshu and Zhihu (8 total publications). Supports customizable article count and platform selection.
user-invocable: true
allowed-tools: Bash(python:*)
argument-hint: '[--count N] [--platforms xiaohongshu,zhihu]'
---

# Batch Factory

This skill automates batch content production, generating multiple articles across different topics and publishing them to multiple platforms in a single execution.

## When to Use This Skill

Use this skill when you need to:

- Generate multiple articles in one batch (default: 4 articles)
- Publish content to Xiaohongshu and Zhihu simultaneously
- Produce content for both AI technology and automotive topics
- Automate the entire pipeline from collection to publication
- Generate content at scale without manual intervention

**Don't use this skill for:**
- Single article generation (use `/factory` instead)
- Manual topic selection (use `/factory` with manual mode)
- Quick material collection only (use `/search` or `/collect`)

## Quick Start

### Default Mode (Recommended)
```bash
python src/pipeline/batch_pipeline.py
```

**Output:**
- Xiaohongshu: 4 articles (2 AI + 2 automotive)
- Zhihu: 4 articles (2 AI + 2 automotive)
- Total: 4 articles, 8 publications

### Custom Article Count
```bash
# Generate 3 articles per topic (6 total)
python src/pipeline/batch_pipeline.py --count 3
```

### Custom Platforms
```bash
# Publish to Xiaohongshu only
python src/pipeline/batch_pipeline.py --platforms xiaohongshu

# Publish to multiple platforms
python src/pipeline/batch_pipeline.py --platforms xiaohongshu,zhihu,bilibili
```

## How It Works

### Four-Stage Pipeline

**Stage 1: Material Search (1x)**
- Collect materials from multiple sources
- Deduplicate and cluster
- Output material pool

**Stage 2: Topic Planning (2 directions)**
- AI Technology: Filter → Score → AI recommends 3-5 topics
- Automotive: Filter → Score → AI recommends 3-5 topics

**Stage 3: Batch Generation (N articles per direction)**
For each topic:
1. Generate article content
2. Generate visual cards (optional)
3. AI quality review (6-dimension scoring)
4. Auto-rewrite if review fails

**Stage 4: Multi-Platform Publishing**
- Publish each article to specified platforms
- Record publication results
- Generate summary report

### Efficiency Gains

**Single Article Mode:**
- Material search: Every execution
- Topic planning: Every execution
- Generate 1 article: ~5 minutes

**Batch Mode:**
- Material search: Once only ✅
- Topic planning: Once only ✅
- Generate 4 articles: ~20 minutes (saves ~10 minutes)

## Parameters

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `--count` | Articles per direction | 2 | `--count 3` |
| `--platforms` | Publishing platforms (comma-separated) | xiaohongshu,zhihu | `--platforms xiaohongshu` |
| `--sources` | Material sources (comma-separated) | All | `--sources hn,github` |
| `--no-cards` | Skip visual card generation | False | `--no-cards` |

## Output Files

### Draft Files
```
content/drafts/
├── gpt-5-来了-ai-大模型进入新纪元.md
├── gpt-5-来了-ai-大模型进入新纪元-cards.html
├── claude-3-5-发布-多模态能力全面升级.md
├── claude-3-5-发布-多模态能力全面升级-cards.html
├── 特斯拉-fsd-v12-体验.md
├── 特斯拉-fsd-v12-体验-cards.html
├── 比亚迪秦-plus-dm-i-深度评测.md
└── 比亚迪秦-plus-dm-i-深度评测-cards.html
```

### Batch Results JSON
**Path:** `content/batch/YYYY-MM-DD-HHMMSS-batch.json`

Contains detailed results for each article including:
- Direction and topic
- Draft path
- Review score
- Publication results per platform
- Pipeline ID

See `references/output-format.md` for complete schema.

## Performance Estimates

| Configuration | Articles | Publications | Estimated Time |
|--------------|----------|--------------|----------------|
| Default (2/direction) | 4 | 8 | ~20 minutes |
| 3/direction | 6 | 12 | ~30 minutes |
| 4/direction | 8 | 16 | ~40 minutes |
| 5/direction | 10 | 20 | ~50 minutes |

**Recommendation:** Start with `--count 1` to test the workflow.

## Quality Assurance

Every article undergoes AI quality review with 6 dimensions:

1. **Title Appeal** (20 points) - Suspense, numbers, specific scenarios
2. **Opening Hook** (15 points) - First 3 sentences grab attention
3. **Content Structure** (20 points) - Clear framework, short paragraphs
4. **Logical Coherence** (15 points) - Clear arguments, sufficient evidence
5. **Readability** (15 points) - Concise, fluent, rich examples
6. **Information Density** (15 points) - New information, data support

**Pass threshold:** ≥70 points
**Auto-rewrite:** If review fails, automatically regenerate

## Troubleshooting

**Q: How to generate without publishing?**
A: Not currently supported. Disable all platforms in `publishers.yaml`

**Q: How to generate only one direction?**
A: Not currently supported. Batch mode generates both directions

**Q: What happens if review fails?**
A: Auto-rewrite, max 3 retries

**Q: What happens if publishing fails?**
A: Logs failure reason, continues with next article

**Q: How to view detailed logs?**
A: Each article's pipeline state saved in `content/pipeline/<pipeline_id>.json`

## Advanced Usage

For detailed workflow documentation, parameter combinations, and troubleshooting guides, see:
- `references/workflow-details.md` - Complete workflow documentation
- `references/output-format.md` - Output file schemas
- `references/troubleshooting.md` - Common issues and solutions

## Related Skills

- `/factory` - Single article generation with full automation
- `/search` - Material collection only
- `/plan` - Topic planning only
- `/publish` - Multi-platform publishing only

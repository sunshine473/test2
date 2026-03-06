#!/bin/bash
# 本地测试全自动流水线
# 用法: ./test-pipeline.sh

set -e

echo "=========================================="
echo "  本地测试全自动流水线"
echo "=========================================="
echo ""

# 检查环境变量
echo "检查环境变量..."
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ 缺少 ANTHROPIC_API_KEY"
    exit 1
fi

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "⚠️  缺少 TELEGRAM_BOT_TOKEN（可选）"
fi

echo "✅ 环境变量检查通过"
echo ""

# 运行流水线
echo "开始执行流水线..."
echo ""

cd src

python -m pipeline.main \
    --auto \
    --sources hn,github \
    --direction tech_ai \
    --no-cards \
    --platforms wechat

echo ""
echo "=========================================="
echo "  流水线执行完成"
echo "=========================================="
echo ""

# 显示状态
echo "流水线状态:"
python -m pipeline.main --status

echo ""
echo "查看生成的草稿:"
ls -lh ../content/drafts/*.md | tail -1

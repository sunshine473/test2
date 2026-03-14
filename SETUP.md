# 新电脑环境配置指南

## 已完成
✅ 从远程仓库克隆代码
✅ 创建 .env.example 模板文件
✅ 创建根目录 requirements.txt
✅ 创建必要目录 (logs/, .browser_state/)

## 需要手动配置

### 1. 创建 Python 虚拟环境
```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
```

### 2. 安装依赖
```bash
pip install --upgrade pip
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

### 3. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，填入真实的 API keys 和配置
```

必需的环境变量：
- `GEMINI_API_KEY` - Google Gemini API (内容生成)
- `NOTION_API_KEY` - Notion API (数据中枢)
- `NOTION_DATABASE_ID` - 素材池数据库 ID
- `NOTION_TOPICS_DB_ID` - 选题库数据库 ID
- `NOTION_DRAFTS_DB_ID` - 草稿库数据库 ID
- `NOTION_PUBLISH_DB_ID` - 发布记录数据库 ID

可选的环境变量：
- `TAVILY_API_KEY` - Tavily 搜索 API (素材采集)
- `YOUTUBE_API_KEY` - YouTube Data API (视频采集)
- `WECHAT_APP_ID/WECHAT_APP_SECRET` - 微信公众号发布
- `TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID` - Telegram 通知
- 各平台 Cookie (知乎/小红书/懂车帝/头条)

### 4. 配置 Notion 数据库
如果是全新 Notion 环境，需要创建数据库：
```bash
# 创建 4 个数据库
python scripts/create_notion_databases.py

# 配置字段
python scripts/setup_notion_databases.py

# 创建关联字段
python scripts/create_relations_final.py
python scripts/create_material_relations.py

# 验证完整数据流
python scripts/test_complete_flow.py
```

### 5. 运行测试验证
```bash
# 运行全部测试
PYTHONPATH=src pytest tests/ -v

# 快速验证核心功能
python src/collector/search.py --sources hn
python src/generator/main.py "测试选题" --no-cards
```

### 6. 浏览器平台登录 (可选)
如需发布到知乎/小红书/懂车帝/头条，需要：
1. 手动登录各平台获取 Cookie
2. 将 Cookie 配置到 .env 文件
3. 或者使用 Playwright 交互式登录保存状态

## 目录结构说明
```
.
├── .env                    # 本地环境变量 (需手动创建)
├── .env.example            # 环境变量模板 ✅
├── requirements.txt        # 统一依赖文件 ✅
├── .venv/                  # Python 虚拟环境 (需创建)
├── logs/                   # 日志目录 ✅
├── .browser_state/         # 浏览器登录状态 ✅
├── content/
│   ├── pool/              # 素材池 JSON (运行时生成)
│   ├── drafts/            # 草稿 Markdown
│   └── pipeline/          # 流水线状态
├── src/                   # 源代码
├── tests/                 # 测试用例
└── scripts/               # 工具脚本
```

## 快速开始
```bash
# 激活虚拟环境
source .venv/bin/activate

# 一键采集素材
python src/collector/main.py

# 生成文章
python src/generator/main.py "选题标题"

# 发布文章
python src/publisher/main.py content/drafts/xxx.md
```

## 常见问题

### Q: Python 版本要求？
A: Python 3.9+ (当前系统: 3.9.6 ✅)

### Q: 没有 Notion 数据库怎么办？
A: 运行 `scripts/create_notion_databases.py` 自动创建

### Q: 如何获取各平台 Cookie？
A: 浏览器开发者工具 → Network → 复制请求头中的 Cookie

### Q: Playwright 安装失败？
A: 确保已安装 Chromium: `playwright install chromium`

# Writer — 多平台内容创作全流程 AI Skill

多平台内容创作全流程助手，支持公众号、小红书、知乎、百家号、微博、搜狐、今日头条、企鹅号、简书、豆瓣、大鱼号、36氪。

一句话触发完整工作流：热点抓取 → 选题评分 → 框架选择 → 素材采集 → 内容增强 → 文章写作 → SEO 优化 → AI 配图 → 多平台文件导出。

---

## 快速开始

### 安装

```bash
git clone --depth 1 https://github.com/etoup/writer.git ~/.claude/skills/writer
cd ~/.claude/skills/writer && pip install -r requirements.txt
```

### 配置

```bash
cp config.example.yaml config.yaml
```

在 `config.yaml` 中填入你的火山方舟 API key（阿里百炼为可选 fallback）：

```yaml
image:
  providers:
    - provider: volcengine
      api_key: "your_volcengine_key"
    - provider: dashscope
      # api_key: "your_dashscope_key"  # 可选，不填则跳过

theme: "professional-clean"
```

在 `style.yaml` 中设置你的账号风格（首次使用会自动引导设置）：

```bash
cp style.example.yaml style.yaml
```

### 使用

安装后，直接对 Agent 说：

```
"写一篇公众号文章"
"写一篇关于 AI Agent 的小红书笔记"
"写一篇知乎文章，主题是效率工具"
"多平台发布，主题是 AI 大模型趋势"
```

---

## 支持的平台

| 平台 | 触发词 | 输出格式 | 默认字数 | 配图比例 |
|------|--------|----------|----------|----------|
| **公众号** | 公众号、推文、微信文章 | HTML + Word + Markdown | 1500-2500 | 封面 2.35:1，内文 16:9 |
| **小红书** | 小红书、笔记、小红书图文 | Markdown + Word | 300-800 | 3:4（最多 9 张） |
| **知乎** | 知乎、知乎回答、知乎文章 | Markdown + Word | 2000-5000 | 16:9（可选 1-3 张） |
| **百家号** | 百家号 | HTML + Word | 1000-2000 | 封面 16:9 |
| **微博** | 微博、微博长文 | Markdown + Word | 140-2000 | 1:1 或 3:4（1-9 张） |
| **搜狐号** | 搜狐、搜狐号 | HTML + Word | 1000-2500 | 封面 16:9 |
| **今日头条** | 今日头条、头条号 | HTML + Word | 1000-2000 | 三图封面 16:9/1:1 |
| **企鹅号** | 企鹅号、企鹅号文章 | HTML + Word | 1000-2000 | 封面 16:9 |
| **简书** | 简书 | Markdown + Word | 1000-3000 | 16:9（可选） |
| **豆瓣** | 豆瓣、豆瓣文章 | Markdown + Word | 800-2500 | 16:9（可选） |
| **大鱼号** | 大鱼号 | HTML + Word | 1000-2000 | 封面 16:9 |
| **36氪** | 36kr、36氪 | Markdown + Word | 1500-3000 | 16:9（数据图） |

---

## 工作流程

```
Step 0 平台识别 → 识别目标平台，加载差异化参数
 ↓
Step 1 环境 + 配置 → 检查依赖、加载风格、版本检查
 ↓
Step 2 热点抓取 → 多平台热搜 → 历史去重 + SEO → 选题评分
 ↓
Step 3 框架选择 → 7 套写作骨架 → 素材采集 + 内容增强
 ↓
Step 4 写作 → 维度随机化 → 人格注入 → 范文风格 → 编辑锚点 → 快速自检
 ↓
Step 5 SEO + 验证 → 多平台关键词优化 → 质量验证 → 脚本辅助评分
 ↓
Step 6 视觉 AI → 实体提取 → 封面生成 → 风格锚定 → 内文配图
 ↓
Step 7 多平台文件导出 → Markdown/HTML/Word + 配图文件夹
 ↓
Step 8 收尾 → 写入历史 → 回复用户（文件清单 + 发布指引）
```

---

## 详细使用指南

### 1. 单平台写作

指定平台触发，只生成该平台的文件：

```
"写一篇公众号文章"
"写一篇关于 AI Agent 的小红书笔记"
"写一篇知乎文章，主题是效率工具"
"写一篇微博长文，讨论最近的科技热点"
```

### 2. 多平台一键分发

生成全部 12 个平台的适配文件：

```
"多平台发布，主题是 AI 大模型趋势"
"一键多发，关于周末探店的内容"
```

### 3. 交互模式

在选题、框架、配图处暂停确认：

```
"交互模式，写一篇公众号文章"
"我要自己选，写一篇小红书笔记"
```

### 4. 辅助功能

| 你说 | 功能 |
|------|------|
| 润色/缩写/扩写/换语气 | 编辑文章 |
| 封面换暖色调 | 重新生图 |
| 用框架 B 重写 | 回到写作步骤 |
| 换一个选题 | 回到选题步骤 |
| 看看有什么主题 | 打开主题画廊预览 |
| 换成 XX 主题 | 切换排版主题 |
| 看看文章数据 | 效果复盘 |
| 学习我的修改 | 学习飞轮：从你的改稿中学习风格 |
| 学习排版 / 学排版 | 从公众号文章 URL 提取排版主题 |
| 检查一下 / 自检 / 这篇文章怎么样 | 生成文章档案 + 质量检查报告 |
| 导入范文 / 建范文库 | 从已发布文章提取风格指纹 |
| 查看范文库 | 查看已导入的范文列表 |
| 验证配置 / 检查配置 / 测试图片 | 执行图片生成验证，确认 API key 是否有效 |
| 更新 / 升级 | 检查并更新 Writer 版本 |

---

## 配置详解

### config.yaml — 基础配置

```yaml
# 默认作者署名
author: "你的名字"

# AI 图片生成（火山方舟必填，阿里百炼可选）
image:
  providers:
    - provider: volcengine          # 火山方舟（默认优先）
      api_key: "your_volcengine_key"  # 必填
      # model: "doubao-seedream-5-0-260128"  # 可选
      # base_url: "https://ark.cn-beijing.volces.com/api/v3"  # 可选
    - provider: dashscope           # 阿里百炼（可选 fallback）
      # api_key: "your_dashscope_key"  # 非必填
      # model: "qwen-image-2.0-pro"      # 可选

# 默认排版主题
theme: "professional-clean"
```

**简化配置**（只使用火山方舟）：

```yaml
author: "你的名字"
image:
  provider: "volcengine"
  api_key: "your_volcengine_key"
theme: "professional-clean"
```

### style.yaml — 风格配置

```yaml
# 账号信息
name: "Demo科技"
industry: "科技/互联网"
target_audience: "25-40岁互联网从业者"

# 内容方向
topics:
  - AI/人工智能
  - 产品设计
  - 创业/商业模式

# 写作风格
tone: "专业但不学术，有观点但不偏激，偶尔幽默"
voice: "第一人称，像一个懂行的朋友在分享见解"
word_count: "1500-2500"
content_style: "干货"  # 干货/故事/情绪/热点/测评

# 写作人格
writing_persona: "midnight-friend"

# 禁忌
blacklist:
  words: ["震惊", "必看", "不转不是中国人"]
  topics: ["政治敏感", "宗教", "色情"]

# 参考账号
reference_accounts:
  - "36氪"
  - "虎嗅"
  - "少数派"

# 排版主题
theme: "professional-clean"

# 封面风格
cover_style: "简洁科技感，蓝色调，扁平化设计"

# 署名
author: "Demo编辑部"

# 平台差异化覆盖（可选）
platform_overrides:
  xiaohongshu:
    tone: "轻松活泼，口语化，多用 emoji"
    word_count: "300-800"
    content_style: "种草/测评/经验分享"
    writing_persona: "warm-editor"
  zhihu:
    tone: "专业严谨，有数据支撑"
    word_count: "2000-5000"
    content_style: "干货/分析"
    writing_persona: "industry-observer"
  weibo:
    word_count: "140-2000"
  toutiao:
    tone: "通俗易懂，标题吸引点击"
    content_style: "热点/民生"
```

---

## 写作人格

像选排版主题一样选写作风格，在 `style.yaml` 中配置：

```yaml
writing_persona: "midnight-friend"
```

| 人格 | 适合 | 风格特点 |
|------|------|----------|
| `midnight-friend` | 个人号/自媒体 | 极度口语化、高自我怀疑、每段第一人称 |
| `warm-editor` | 生活/文化/情感 | 温暖叙事、故事嵌套数据、柔和情绪弧 |
| `industry-observer` | 行业媒体/分析 | 中性分析、数据先行、稳中带刺 |
| `sharp-journalist` | 新闻/评论 | 犀利简洁、数据驱动、强观点 |
| `cold-analyst` | 财经/投研 | 冷静克制、逻辑链条、风险意识强 |

---

## 排版主题

### 16 个主题

```
# 浏览器内预览所有主题（并排对比 + 一键复制）
python3 toolkit/cli.py gallery

# 列出主题名称
python3 toolkit/cli.py themes
```

| 类别 | 主题 |
|------|------|
| 通用 | `professional-clean`（默认）、`minimal`、`newspaper` |
| 科技 | `tech-modern`、`bytedance`、`github` |
| 文艺 | `warm-editorial`、`sspai`、`ink`、`elegant-rose` |
| 商务 | `bold-navy`、`minimal-gold`、`bold-green` |
| 风格 | `bauhaus`、`focus-red`、`midnight` |

所有主题均支持微信暗黑模式。

### 从文章学习主题

```bash
python3 scripts/learn_theme.py https://mp.weixin.qq.com/s/xxxx --name my-style
```

---

## 文件输出

### 单平台模式

```
output/
└── 2026-05-09-ai-agent-trends/
    ├── wechat.html              # 公众号（内联样式 HTML）
    ├── wechat.md                # Markdown 源文件
    ├── wechat.docx              # Word 文档
    └── images/                  # 配图文件夹
        ├── cover_wechat.png     # 封面
        └── inner_*.png          # 内文配图
```

### 多平台模式

```
output/
└── 2026-05-09-ai-agent-trends/
    ├── wechat.html / .md / .docx
    ├── xiaohongshu.md / .docx
    ├── zhihu.md / .docx
    ├── baijiahao.html / .docx
    ├── weibo.md / .docx
    ├── sohu.html / .docx
    ├── toutiao.html / .docx
    ├── qiehao.html / .docx
    ├── jianshu.md / .docx
    ├── douban.md / .docx
    ├── dayu.html / .docx
    ├── kr36.md / .docx
    └── images/                  # 整合配图
        ├── cover_wechat.png
        ├── cover_xiaohongshu_1.png
        ├── xiaohongshu_2.png
        └── ...
```

### 手动发布指引

| 平台 | 发布方式 |
|------|----------|
| 公众号 | 登录后台 → 新建图文 → 复制 HTML 或导入 Word → 上传封面 → 保存草稿 |
| 小红书 | 打开 App → 发布图文 → 上传 3:4 图片 → 复制 Markdown 文案 → 添加话题标签 |
| 知乎 | 登录 → 写文章/回答 → 粘贴 Markdown → 拖拽上传图片 |
| 百家号 | 登录后台 → 新建图文 → 复制 HTML 或导入 Word → 上传封面 → 发布 |
| 微博 | 发微博 → 粘贴文本 → 添加图片（最多 9 张）→ 发布 |
| 搜狐/头条/企鹅/大鱼 | 登录对应后台 → 新建图文 → 复制 HTML 或导入 Word → 上传封面 → 发布 |
| 简书 | 登录 → 写文章 → 粘贴 Markdown → 插入图片 → 设置标签 → 发布 |
| 豆瓣 | 写日记 → 粘贴 Markdown → 手动插入图片 → 发布 |
| 36氪 | 通过官方投稿渠道提交 Markdown 或 Word 文档 |

---

## Toolkit 独立使用

```bash
# Markdown → 微信 HTML 预览
python3 toolkit/cli.py preview article.md --theme sspai

# 主题画廊
python3 toolkit/cli.py gallery

# 导出单平台文件
python3 toolkit/cli.py export article.md --platform xiaohongshu --output ./output/test/

# 导出多平台文件
python3 toolkit/cli.py export article.md --platform all --output ./output/test/ --images ./output/test/images/

# 列出主题
python3 toolkit/cli.py themes

# 抓热点
python3 scripts/fetch_hotspots.py --limit 20

# SEO 分析
python3 scripts/seo_keywords.py --json "AI大模型" "科技股"

# 范文风格库
python3 scripts/extract_exemplar.py article.md        # 导入范文
python3 scripts/extract_exemplar.py *.md -s "你的账号"  # 批量导入
python3 scripts/extract_exemplar.py --list             # 查看范文库

# 文章质量检查
python3 scripts/humanness_score.py article.md --verbose

# 从公众号文章学习排版主题
python3 scripts/learn_theme.py https://mp.weixin.qq.com/s/xxxx --name my-style

# 从公众号 URL 提取文章
python3 scripts/fetch_article.py https://mp.weixin.qq.com/s/xxxx -o article.md
```

---

## 目录结构

```
writer/
├── SKILL.md                    # 主管道（Step 0-8）
├── config.example.yaml         # API 配置模板
├── style.example.yaml          # 风格配置模板
├── requirements.txt
│
├── platforms/                  # 各平台格式规范（新增）
│   ├── wechat.md
│   ├── xiaohongshu.md
│   ├── zhihu.md
│   ├── baijiahao.md
│   ├── weibo.md
│   ├── sohu.md
│   ├── toutiao.md
│   ├── qiehao.md
│   ├── jianshu.md
│   ├── douban.md
│   ├── dayu.md
│   └── kr36.md
│
├── scripts/                    # 数据采集 + 诊断 + 构建
│   ├── fetch_hotspots.py       # 多平台热点抓取
│   ├── seo_keywords.py         # SEO 关键词分析
│   ├── fetch_stats.py          # 微信文章数据回填
│   ├── build_playbook.py       # 从历史文章生成 Playbook
│   ├── learn_edits.py          # 学习人工修改
│   ├── humanness_score.py      # 文章质量打分
│   ├── extract_exemplar.py     # 范文风格提取
│   ├── learn_theme.py          # 从文章提取排版主题
│   ├── fetch_article.py        # 从文章 URL 提取正文
│   ├── diagnose.py             # 配置完备度检查
│   └── build_openclaw.py       # SKILL.md → OpenClaw 格式转换
│
├── toolkit/                    # Markdown → 多平台工具链
│   ├── cli.py                  # CLI（preview / export / gallery / themes / learn-theme）
│   ├── converter.py            # Markdown → 内联样式 HTML + 微信兼容修复
│   ├── exporter.py             # 多平台文件导出（HTML/Markdown/Word）
│   ├── image_gen.py            # AI 图片生成（火山方舟 + 阿里百炼）
│   ├── theme.py                # YAML 主题引擎
│   └── themes/                 # 16+ 排版主题
│
├── personas/                   # 5 套写作人格预设
├── references/                 # Agent 按需加载
│   ├── writing-guide.md        # 写作规范 + 质量检查
│   ├── frameworks.md           # 7 种写作框架
│   ├── content-enhance.md      # 内容增强策略
│   ├── topic-selection.md      # 选题评估规则
│   ├── seo-rules.md            # 微信 SEO 规则
│   ├── visual-prompts.md       # 视觉 AI 提示词规范
│   ├── wechat-constraints.md   # 微信平台限制 + 自动修复
│   ├── style-template.md       # 风格配置字段 + 主题列表
│   ├── exemplar-seeds.yaml     # 通用人类写作模式种子
│   ├── exemplars/              # 用户范文风格库（自动生成）
│   ├── onboard.md              # 首次设置流程
│   ├── learn-edits.md          # 学习飞轮流程
│   └── effect-review.md        # 效果复盘流程
│
├── output/                     # 生成的文章
├── corpus/                     # 历史语料（可选）
└── lessons/                    # 修改记录（自动生成）
```

运行时自动生成（不入 git）：`style.yaml`、`history.yaml`、`playbook.md`、`writing-config.yaml`、`references/exemplars/*.md`

---

## 内容质量

Writer 的目标不是"骗过 AI 检测"，而是**写出值得读的文章**。核心机制：

1. **内容增强**：根据框架类型自动执行不同策略——热点文找反直觉角度、干货文强化信息密度、故事文锚定真实细节、对比文注入真实用户体感
2. **素材采集**：自动 WebSearch 真实数据/引述/案例，锚定在文章中（不编造）
3. **范文风格库**：导入你已发布的文章，写作时自动注入你的风格指纹（句长节奏、情绪表达、转折方式）
4. **编辑锚点**：在 2-3 个关键位置标记"在这里加一句你自己的话"
5. **学习飞轮**：每次你编辑后说"学习我的修改"，下次初稿更接近你的风格
6. **文章自检**：说"检查一下"，查看生成档案（用了什么框架/人格/策略）+ 质量检查（具体到哪句话该怎么改）

---

## 容器语法（公众号等支持的平台）

```markdown
:::dialogue
你好，请问这个功能怎么用？
> 很简单，直接在 Markdown 里写就行。
:::

:::timeline
**2024 Q1** 立项启动
**2024 Q3** MVP 上线
:::

:::callout tip
提示框，支持 tip / warning / info / danger。
:::

:::quote
好的排版不是让读者注意到设计，而是让读者忘记设计。
:::
```

---

## 降级原则

| 步骤 | 降级方案 |
|------|----------|
| 环境检查 | 逐项引导，设降级标记 |
| 图片验证 | 失败则提示用户，设 `skip_image_gen` |
| 热点抓取 | WebSearch 替代 |
| 选题为空 | 请用户手动给选题 |
| SEO 脚本 | LLM 判断 |
| 素材采集 | LLM 训练数据中可验证的公开信息 |
| Persona 不存在 | 回退到 midnight-friend |
| 范文库为空 | Fallback 到 exemplar-seeds.yaml |
| 生图失败 | 输出提示词 + 备选关键词 |
| 文件导出失败 | 输出 Markdown 源文件 |

---

## License

MIT

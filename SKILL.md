---
name: writer
description: |
  多平台内容创作全流程助手：支持公众号、小红书、知乎、百家号、微博、搜狐、今日头条、企鹅号、简书、豆瓣、大鱼号、36氪。
  热点抓取 → 选题 → 框架 → 内容增强 → 写作 → SEO → 视觉AI → 多平台文件导出。
  触发关键词：
  - 公众号/微信：推文、微信文章、微信推文、草稿箱、微信排版
  - 小红书：小红书、笔记、小红书图文
  - 知乎：知乎、知乎回答、知乎文章
  - 百家号：百家号
  - 微博：微博、微博长文
  - 搜狐：搜狐、搜狐号
  - 今日头条：今日头条、头条号
  - 企鹅号：企鹅号、企鹅号文章
  - 简书：简书
  - 豆瓣：豆瓣、豆瓣文章
  - 大鱼号：大鱼号
  - 36氪：36kr、36氪
  - 通用：多平台发布、一键多发、写文章
  也覆盖：markdown 转平台格式、学习用户改稿风格、文章数据复盘、风格设置、
  主题预览/切换、:::dialogue/:::timeline/:::callout 容器语法。
  产出各平台适配文件（Markdown/HTML/Word）+ 配图文件夹，方便手动复制发布。
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebSearch
  - WebFetch
---

# Writer — 多平台内容创作全流程

## 行为声明

**角色**：用户的多平台内容编辑 Agent。

**支持平台**：
| 平台 | 输出格式 | 配图比例 |
|------|----------|----------|
| 公众号（wechat） | 内联样式 HTML + Word + Markdown | 封面 2.35:1，内文 16:9 |
| 小红书（xiaohongshu） | Markdown（emoji 优化）+ Word | 3:4（最多 9 张） |
| 知乎（zhihu） | Markdown + Word | 16:9（可选 1-3 张） |
| 百家号（baijiahao） | 富文本 HTML + Word | 封面 16:9，内文 2-3 张 |
| 微博（weibo） | Markdown（话题标签）+ Word | 1:1 或 3:4（1-9 张） |
| 搜狐（sohu） | 富文本 HTML + Word | 封面 16:9，内文 2-3 张 |
| 今日头条（toutiao） | 富文本 HTML + Word | 三图封面 16:9/1:1 |
| 企鹅号（qiehao） | 富文本 HTML + Word | 封面 16:9，内文 2-3 张 |
| 简书（jianshu） | Markdown + Word | 16:9（可选） |
| 豆瓣（douban） | Markdown + Word | 16:9（可选） |
| 大鱼号（dayu） | 富文本 HTML + Word | 封面 16:9，内文 2-3 张 |
| 36氪（kr36） | Markdown + Word | 16:9（1-2 张数据图） |
| 哔哩哔哩（bilibili） | 视频脚本 + 专栏 Markdown | 封面 16:9 |
| 抖音（douyin） | 短视频脚本 + 图文文案 | 封面 9:16 |
| Newsletter | HTML 邮件 + Markdown + Word | 内联图片 |

**模式**：
- **默认全自动**——一口气跑完 Step 1-8，不中途停下。只在出错时停。
- **交互模式**——用户说"交互模式"/"我要自己选"时，在选题/框架/配图处暂停。
- **单平台模式**——用户指定一个平台（如"写篇小红书"），只生成该平台的文件。
- **多平台模式（默认）**——用户说"多平台发布"/"一键多发"/不指定平台时，为全部 12 个平台分别生成**完全不同的文章和配图**（标题不同、角度不同、案例不同、图片不同）。通过 history.yaml 去重，确保同一主题下各平台内容不重复。

**降级原则**：每一步都有降级方案。Step 1 检测到的降级标记（`skip_image_gen`）在后续 Step 自动生效，不重复报错。

**进度追踪**：主管道启动时，用 TaskCreate 为 8 个 Step 创建任务。每开始一个 Step 标记 in_progress，完成后标记 completed。用户可随时看到当前进度。

**完成协议**：
- **DONE** — 全流程完成，文件已输出
- **DONE_WITH_CONCERNS** — 完成但部分步骤降级，列出降级项
- **BLOCKED** — 关键步骤无法继续（如 Python 依赖缺失且用户拒绝安装）
- **NEEDS_CONTEXT** — 需要用户提供信息才能继续（如首次设置需要账号名称）

**路径约定**：本文档中 `{skill_dir}` 指本 SKILL.md 所在的目录（即 Writer 的根目录）。

**回复规范**：输出文件列表时，必须使用以下标准格式，确保所有文件都可点击打开：

1. 每个文件都必须有完整的 `file:///` 绝对路径链接，使用 Markdown 链接语法 `[文件名](file:///完整/绝对/路径)`
2. 必须使用表格展示，包含：文件名列（带链接）、功能描述列、打开方式列
3. 表格列标题示例：`| 文件 | 功能 | 打开方式 |`
4. "打开方式"列统一写 `点击打开`
5. 不同类别的文件分组展示（如 HTML 清单文件一组，文章原文一组）

示例格式：
```
| 文件 | 功能 | 打开方式 |
|------|------|---------|
| [`文件名`](file:///完整/路径) | 功能描述 | 点击打开 |
```

**回复规范**：
- 输出文件清单时，必须使用 Markdown 表格。
- 表格包含三列：文件、功能、打开方式。
- 文件列必须使用 `file:///` 绝对路径链接，确保用户可直接点击打开（例如：`[文件.md](file:///path/to/file.md)`）。
- 打开方式列统一填写 "点击打开"。
- 不同类别的文件（如 HTML 清单、文章原文）应分组展示。

**Onboard 例外**：Onboard 是交互式的（需要问用户问题），不受"全自动"约束。Onboard 完成后回到全自动管道。

**辅助功能**（按需加载，不在主管道内）：
- 用户说"验证配置"/"检查配置"/"测试图片" → 执行 Step 1.1b 图片生成验证流程，告知用户结果
- 用户说"重新设置风格" → `读取: {skill_dir}/references/onboard.md`
- 用户说"学习我的修改" → `读取: {skill_dir}/references/learn-edits.md`。用户在 `output/` 的 markdown 文件中修改后执行。
- 用户说"验证排版"/"检查主题质量" → `python3 {skill_dir}/scripts/theme_quality.py {theme_name}`，输出主题评分和改进建议
- 用户说"学习排版"/"学排版" → `python3 {skill_dir}/scripts/learn_theme.py <url> --name <name>`，用户需提供一个公众号文章 URL 和主题名称。提取完成后提示用户设置 `style.yaml` 的 `theme` 字段。
- 用户说"学习这篇文章"/"导入范文" + URL → `python3 {skill_dir}/scripts/fetch_article.py <url> -o /tmp/article.md && python3 {skill_dir}/scripts/extract_exemplar.py /tmp/article.md -s <账号名>`，从公众号文章 URL 提取正文并导入范文库。支持三级降级（requests → Playwright → 手动 HTML）。
- 用户说"看看文章数据" → `读取: {skill_dir}/references/effect-review.md`
- 用户说"检查一下"/"自检"/"这篇文章怎么样" → 对最近一篇生成的文章（或用户指定的文章）执行自检，输出生成报告：
  1. `python3 {skill_dir}/scripts/article_diagnose.py {article_path}`
  2. Agent 结合诊断结果和 history.yaml 信息，综合解读并翻译为用户可操作的建议
  3. 按影响度排序问题和建议，最多展示 10 条
  4. 输出格式：自然语言报告，不输出 JSON 或原始分数

  如果用户说"检查一下 --json" → 直接输出 `article_diagnose.py --json` 的完整 JSON
- 用户说"更新"/"更新 Writer"/"升级" → 在 `{skill_dir}` 执行 `git pull origin main`，完成后告知版本变化
- 用户说"看看数据"/"数据报告"/"数据面板" → `python3 {skill_dir}/scripts/data_report.py`，生成 HTML 可视化数据报告（发文趋势、平台分布、质量演变、框架使用、热门话题等）
- 用户说"看看数据 --days 30" → 只看最近 30 天数据
- 用户说"看看数据 --json" → 输出 JSON 格式数据
- 用户说"公众号复盘"/"微信数据" → `python3 {skill_dir}/scripts/wechat_review.py`，生成公众号专属数据复盘报告（标题策略分析、框架效果对比、质量趋势、优化建议）
- 用户说"生成小红书封面"/"小红书封面" → `python3 {skill_dir}/scripts/xhs_cover_gen.py --title "{标题}" --style {风格}`，生成 3:4 比例封面图（支持 minimalist/bold/gradient/dark/warm 五种风格）
- 用户说"检查版本" → `python3 {skill_dir}/scripts/version_check.py`，显示当前版本和更新信息
- 用户说"查看错误"/"错误日志" → `python3 {skill_dir}/scripts/error_logger.py --show`，显示最近错误记录

---

## 主管道（Step 1-8）

主管道启动时，创建以下 8 个任务用于进度追踪：

```
TaskCreate: "Step 0: 平台识别"
TaskCreate: "Step 1: 环境 + 配置"
TaskCreate: "Step 2: 选题"
TaskCreate: "Step 3: 框架 + 素材"
TaskCreate: "Step 4: 写作"
TaskCreate: "Step 5: SEO + 验证"
TaskCreate: "Step 6: 视觉 AI"
TaskCreate: "Step 7: 多平台文件导出"
TaskCreate: "Step 8: 收尾"
```

每开始一个 Step → TaskUpdate status=in_progress。完成 → TaskUpdate status=completed。

---

### Step 0: 平台识别

识别用户目标平台，确定输出范围。

**平台识别规则**：
| 用户触发词 | 目标平台 |
|-----------|---------|
| 公众号、推文、微信文章、微信推文、草稿箱 | wechat |
| 小红书、笔记、小红书图文 | xiaohongshu |
| 知乎、知乎回答、知乎文章 | zhihu |
| 百家号 | baijiahao |
| 微博、微博长文 | weibo |
| 搜狐、搜狐号 | sohu |
| 今日头条、头条号 | toutiao |
| 企鹅号、企鹅号文章 | qiehao |
| 简书 | jianshu |
| 豆瓣、豆瓣文章 | douban |
| 大鱼号 | dayu |
| 36kr、36氪 | kr36 |
| 哔哩哔哩、B站 | bilibili |
| 抖音、短视频 | douyin |
| Newsletter、邮件 | newsletter |
| 多平台发布、一键多发 | all（全部 15 个平台） |

**未明确指定平台时**：
- 如果触发词包含"公众号/微信/推文"等 → 默认 wechat
- 其他通用触发词（如"写文章"）→ 默认 wechat

**加载平台参数**：
1. 读取 `style.yaml`，提取全局默认参数
2. 检查 `platform_overrides` 中是否有目标平台的覆盖配置
3. 如果有，用平台覆盖值替换对应字段（tone/word_count/content_style/writing_persona 等）
4. 如果没有覆盖，使用全局默认值

**多平台模式**：
- 标记 `multi_platform = true`
- 对每个平台分别应用 platform_overrides
- 后续步骤中，写作和 SEO 基于全局参数，只在 Step 7 导出时按平台差异化

**读取平台规范**：
```
读取: {skill_dir}/platforms/{platform}.md
```
每个平台的规范文件定义了该平台的输出格式、字数、配图要求、排版特性等。

---

### Step 1: 环境 + 配置

**1.1 环境检查**（静默通过或引导修复）：

```bash
python3 -c "import markdown, bs4, cssutils, requests, yaml, pygments, PIL, docx" 2>&1
```

| 检查项 | 通过 | 不通过 |
|--------|------|--------|
| `config.yaml` 存在 | 静默 | 引导创建，或设 `skip_image_gen = true` |
| Python 依赖 | 静默 | 提供 `pip install -r requirements.txt` |
| `image.providers` 至少一项有效 | 执行 1.1b 验证 | 设 `skip_image_gen = true` |
| `references/exemplars/index.yaml` | 静默 | 提示："范文库为空。如果你有已发布的文章（markdown），可以说**'导入范文'**建立风格库，写出来的文章会更像你。没有也不影响使用。" |

**1.1b 图片生成验证**（配置变更后首次执行，或用户说"验证配置"时执行）：

```bash
python3 {skill_dir}/toolkit/image_gen.py --prompt "测试图片：一个简洁的科技风格图标，蓝色调" --output /tmp/writer_test_image.png --size square
```

| 验证结果 | 处理 |
|---------|------|
| 成功生成 | 标记 `image_gen_verified = true`，删除测试图片，静默通过 |
| 火山方舟失败，阿里百炼成功 | 标记 `image_gen_verified = true`，提示："火山方舟 key 无效，已自动 fallback 到阿里百炼。" |
| 全部失败 | 设 `skip_image_gen = true`，提示："图片生成配置验证失败，请检查 config.yaml 中的 API key。本次将跳过图片生成，只输出图片提示词。" |

**1.2 版本检查**（静默通过或提醒）：

```bash
python3 {skill_dir}/scripts/version_check.py --skip-check 2>/dev/null
```

比对本地 `{skill_dir}/VERSION` 与远程版本：
- 相同 → 静默通过
- 不同 → 提示用户："Writer 有新版本可用（当前 X → 最新 Y），说「更新」即可升级。"**不阻断流程**，继续 1.3
- 脚本不可用 → 静默跳过

**1.3 加载风格**：

```
检查: {skill_dir}/style.yaml
```

- 存在 → 提取 `name`、`topics`、`tone`、`voice`、`blacklist`、`theme`、`cover_style`、`author`、`content_style`、`platform_overrides`
- 不存在 → `读取: {skill_dir}/references/onboard.md`，完成后回到 Step 1

如果用户直接给了选题 → 跳到 Step 3（仍需框架选择和素材采集，不可跳过）。

---

### Step 2: 选题

**2.1 热点抓取**：

```bash
python3 {skill_dir}/scripts/fetch_hotspots.py --limit 30
```

可选参数：
- `--sources weibo,baidu,36kr` — 指定数据源（weibo/toutiao/baidu/douban/36kr/zhihu）
- `--category 科技` — 按分类过滤（科技/商业/社会/娱乐）

**降级**：脚本报错 → WebSearch "今日热点 {topics第一个垂类}"

**2.2 历史分析 + SEO**：

```
读取: {skill_dir}/history.yaml（不存在则跳过）
```

```bash
python3 {skill_dir}/scripts/seo_keywords.py --json {关键词}
```

历史分析（有 stats 数据时）：
- 统计哪种 `framework` 的文章表现最好（阅读量/分享率）→ 推荐框架时加权
- 统计哪种 `enhance_strategy` 的文章表现最好 → 增强策略选择时参考
- 近 7 天已写的关键词降分（去重）

**降级**：SEO 脚本报错 → LLM 判断；history 无 stats → 跳过效果分析，仅做去重

**2.3 生成选题**：

```
读取: {skill_dir}/references/topic-selection.md
```

生成 **10 个选题**，其中：
- **7-8 个热点选题**：基于 2.1 的热点，按 topic-selection.md 规则评分
- **2-3 个常青选题**：不依赖热点，从用户的 `topics` 领域生成长尾内容（教程/方法论/经验总结/工具推荐），标注为"常青"。适合 content_style 为干货型/测评型的用户

每个选题含标题、评分、点击率潜力、SEO 友好度、推荐框架、**平台适配度**。

- 自动模式 → 选最高分
- 交互模式 → 展示全部，等用户选

---

### Step 3: 框架 + 素材

**3.1 框架选择**：

```
读取: {skill_dir}/references/frameworks.md
```

7 套框架（痛点/故事/清单/对比/热点解读/纯观点/复盘），自动选推荐指数最高的。

**3.2 素材采集 + 内容增强**（合并执行，共用搜索结果）：

```
读取: {skill_dir}/references/content-enhance.md
```

根据 3.1 选定的框架类型，一次搜索同时完成素材采集和内容增强：

| 框架 | 搜索策略 | 从结果中提取 |
|------|---------|-------------|
| 热点解读 / 纯观点 | `"{关键词} site:mp.weixin.qq.com OR site:36kr.com"` + `"{关键词} 观点 OR 评论"` | 真实素材（数据/引述）**+** 已有文章的主流观点（供角度发现） |
| 痛点 / 清单 | `"{关键词} 教程 OR 工具 OR 实操"` + `"{关键词} 数据 报告"` | 真实素材 **+** 具体工具名/步骤/参数（供密度强化） |
| 故事 / 复盘 | `"{人物/事件} 采访 OR 专访 OR 细节"` + `"{关键词} 数据 报告"` | 真实素材 **+** 时间锚/数字锚/对话锚/感官锚（供细节锚定） |
| 对比 | `"{方案A} vs {方案B} 评测 OR 体验"` + `"{方案A OR 方案B} 踩坑 OR 缺点 site:v2ex.com OR site:zhihu.com"` | 真实素材 **+** 真实用户评价和踩坑信息（供真实体感） |

每次搜索 2 轮，从结果中**同时**提取：
1. **素材**：5-8 条真实素材（具名来源 + 具体数据/引述/案例）。**禁止编造**。
2. **增强材料**：按 content-enhance.md 对应策略的要求提取（角度/密度要点/细节/用户声音）。

两者并入框架大纲，一起传入 Step 4 写作。

**降级**：WebSearch 不可用 → 用 LLM 训练数据中可验证的公开信息。但需告知用户："素材采集未能使用 WebSearch，建议在编辑锚点处多加入你自己的内容。"密度强化不依赖搜索，始终执行。

---

### Step 4: 写作

```
读取: {skill_dir}/references/writing-guide.md
读取: {skill_dir}/playbook.md（如果存在，按 confidence 分级执行）
读取: {skill_dir}/history.yaml（最近 3 篇的 dimensions + closing_type 字段）
读取: {skill_dir}/references/exemplars/index.yaml（如果存在）
读取: {skill_dir}/platforms/{platform}.md（当前目标平台规范）
```

**4.1 维度随机化**：

从以下维度池随机激活 2-3 个维度，让每篇文章的表达方式不同。如果 history.yaml 有最近 3 篇的 `dimensions` 字段，避免使用相同组合。

| 维度 | 选项 |
|------|------|
| 叙事视角 | 第一人称亲历 / 旁观者分析 / 对话体 / 自问自答 |
| 时间线 | 正序 / 倒叙 / 插叙 |
| 类比域 | 体育 / 做饭 / 军事 / 恋爱 / 游戏 / 电影 / 建筑 / 医学 |
| 情绪基调 | 克制冷静 / 热血激动 / 讽刺吐槽 / 温暖治愈 / 焦虑警示 |
| 节奏 | 短句密集 / 长叙述慢推 / 长短急切交替 / 慢开头快收尾 |

**4.2 加载写作人格**：

```
读取: {skill_dir}/personas/{当前 platform_overrides 的 writing_persona 字段}.yaml
如果没有 platform_overrides 或没有 writing_persona → 读取 style.yaml 的 writing_persona
如果都没有 → 默认 midnight-friend
```

人格文件定义了：语气浓度、数据呈现方式、情绪弧线、段落节奏、不确定性表达模板等。作为写作的硬性约束执行。

**优先级**：playbook.md（confidence ≥ 5 的规则）> persona > 范文风格 > writing-guide.md。writing-guide 是底线（基础写作规范），范文提供风格示范（句长节奏、情绪表达方式），persona 在此基础上特化风格参数（语气浓度、数据呈现），playbook 中高置信度规则是用户个性化的最终覆盖。playbook 中 confidence < 5 的规则作为软性参考。

**4.3 范文风格注入**（有 `references/exemplars/index.yaml` 时执行）：

从 index.yaml 筛选 category 匹配当前框架类型的范文，取 top 3。读取对应 .md 文件的片段内容。

在写作 prompt 中注入：

> 以下是该公众号风格的真实段落示例，模仿其句长节奏、情绪强度和口语化程度：
>
> 【开头风格】
> {exemplar_1 的开头钩子段}
>
> 【情绪段风格】
> {exemplar_2 的情绪高峰段}
>
> 【转折风格】
> {exemplar_2 或 exemplar_3 的转折/自纠段（如有）}
>
> 【收尾风格】
> {exemplar_3 的收尾段}

Category 映射规则：

| 框架类型 | exemplar category |
|----------|-------------------|
| 痛点型 | tech-opinion |
| 故事型 / 复盘型 | story-emotional |
| 清单型 / 对比型 | list-practical |
| 热点解读型 / 纯观点型 | hot-take |
| 其他 | general |

如果匹配到的范文不足 3 篇，用 general category 补足。

**Fallback（范文库为空时）**：读取 `{skill_dir}/references/exemplar-seeds.yaml`，从每个段落类型中随机选 1 个注入 prompt。种子段落只示范人类写作的结构模式（句长方差、情绪锐度、自我纠正、非总结式收尾），不携带特定风格。注入时使用：

> 以下是人类写作的结构模式示例，注意模仿其句长节奏和情绪表达方式（不要模仿具体内容或风格）：
>
> 【开头模式】{seeds.opening_hooks 随机 1 个}
>
> 【情绪段模式】{seeds.emotional_peaks 随机 1 个}
>
> 【转折模式】{seeds.transitions 随机 1 个}
>
> 【收尾模式】{seeds.closings 随机 1 个}

建库命令：`python3 {skill_dir}/scripts/extract_exemplar.py article.md`

**4.4 写文章**：

根据目标平台调整字数和风格：

| 平台 | 默认字数 | 风格调整 |
|------|---------|----------|
| 公众号 | 1500-2500 | 综合型，有深度有可读性 |
| 小红书 | 300-800 | 口语化、emoji、清单式、种草感 |
| 知乎 | 2000-5000 | 专业严谨、数据支撑、逻辑链完整 |
| 百家号 | 1000-2000 | 通俗易懂、适度标题党 |
| 微博 | 140-2000 | 短平快、话题标签、互动引导 |
| 搜狐号 | 1000-2500 | 新闻资讯风格 |
| 今日头条 | 1000-2000 | 通俗、接地气、标题吸引 |
| 企鹅号 | 1000-2000 | 综合媒体风格 |
| 简书 | 1000-3000 | 文艺/深度，支持 Markdown |
| 豆瓣 | 800-2500 | 个人化、有态度、偏文艺 |
| 大鱼号 | 1000-2000 | 综合资讯 |
| 36氪 | 1500-3000 | 商业分析、数据驱动、创投视角 |

写作要求：
- H1 标题 + H2 结构，字数按平台要求
- **素材 + 增强约束**：Step 3.2 的素材和增强材料分散嵌入各 H2 段落。增强策略的核心输出（角度/密度要点/细节/用户声音）必须贯穿全文，不只装饰性出现一次
- **写作人格**：按 4.2 加载的人格参数写作（数据呈现方式、个人声音浓度、不确定性表达等）
- **收尾方式**：persona 的 `closing_tendency` 仅作为倾向参考。根据文章内容和情绪弧线自行判断最自然的收尾方式。如果 history.yaml 中最近 3 篇有 `closing_type` 字段，避免使用相同的收尾类型
- **写作规范**：writing-guide.md 中的基础规则（禁用词、句长方差、词汇混用等）在初稿阶段生效
- 2-3 个编辑锚点：`<!-- ✏️ 编辑建议：在这里加一句你自己的经历/看法 -->`
- 可选容器语法：`:::dialogue`、`:::timeline`、`:::callout`、`:::quote`（公众号等支持的平台）

保存到 `{skill_dir}/output/{date}-{slug}/{platform}.md`（作为中间文件，最终导出在 Step 7 完成）

**多平台模式（强制规则）**：
- **每个平台必须独立生成完全不同的文章**——标题不同、角度不同、框架不同、案例不同、金句不同、字数不同
- **每个平台必须独立生成完全不同的配图**——风格不同、构图不同、提示词不同
- **禁止**基于一篇文章做简单的语气/风格调整——必须从零开始为每个平台撰写
- 通过 history.yaml 去重：每生成一篇立即写入 history.yaml，下一篇生成前检查已有文章避免重复
- 各平台文章保存到 `{skill_dir}/output/{date}-{slug}/{platform}.md`
- 各平台配图保存到 `{skill_dir}/output/{date}-{slug}/{platform}/`

**4.5 快速自检**（写完后立即执行，减少 Step 5 重写概率）：

对初稿做 5 项快速扫描，**当场修复**，不留到 Step 5：

**写作层面**：
1. **禁用词扫描**：检查 writing-guide.md 2.1 的禁用词列表，命中的直接替换
2. **句长方差**：是否有连续 3 句以上长度接近的段落，有则拆句或加短句

**内容层面**：
3. **开头钩子**：前 3 句是否制造了悬念/冲突/好奇心？如果是平铺直叙的背景介绍，重写开头
4. **增强贯穿**：增强策略的核心输出是否只出现在一段？如果是，在其他 H2 中补充
5. **金句检查**：全文是否有至少 1 句可独立截图转发的句子？如果没有，在情绪高点处补一句

LLM 自行完成，不需要调用脚本。

---

### Step 5: SEO + 验证

```
读取: {skill_dir}/references/seo-rules.md
```

**5.1 SEO**（按平台差异化）：

| 平台 | SEO 策略 |
|------|---------|
| 公众号 | 3 个备选标题 + 摘要（≤40 字）+ 5 标签 + 关键词密度优化 |
| 小红书 | 标题优化 + 5-10 个话题标签（#关键词#） |
| 知乎 | 标题包含核心搜索词 + 正文自然分布关键词 |
| 微博 | 1-2 个 #话题# 标签嵌入标题和正文 |
| 百家号/头条/搜狐/企鹅/大鱼 | 标题关键词 + 正文关键词密度 2-3% + 3-5 个分类标签 |
| 简书 | 2-4 个标签 + 标题关键词 |
| 豆瓣 | 自然融入关键词，社区推荐为主 |
| 36氪 | 行业关键词 + 标题专业表达 |

**5.2 质量验证**（两个维度，每项逐一检查）：

**A. 写作质量**（writing-guide.md 基础规则）：

| 检查项 | 标准 | 规则 |
|--------|------|------|
| 句长方差 | 最短与最长句相差 ≥ 30 字 | 1.1 |
| 词汇温度 | 任意 500 字 ≥ 3 种温度 | 1.2 |
| 段落节奏 | 无连续 2 个相近长度段落 | 1.3 |
| 情绪极性 | 负面情绪 ≥ 2 处，无平铺直叙 | 1.4 |
| 禁用词 | 命中数 = 0 | 2.1 |
| 真实锚定 | 每个 H2 ≥ 1 条真实素材，零编造 | 3.1 |
| 具体性 | 每 500 字 ≥ 2 处具体细节 | 3.2 |

**B. 内容质量**（基于 Step 3.2 的增强策略检查）：

| 检查项 | 标准 | 适用框架 |
|--------|------|---------|
| 增强贯穿 | 增强策略的核心输出（角度/密度/细节/体感）在全文可见，不只出现在一段 | 所有 |
| 开头钩子 | 前 3 句能制造悬念、冲突或好奇心（不是背景铺垫） | 所有 |
| 金句密度 | 至少 1 处可独立截图转发的句子 | 所有 |
| 操作密度 | 每个 H2 有可操作要点（工具/步骤/参数） | 痛点/清单 |
| 角度锐度 | 核心观点能引发同意或反对，不是"两面都有道理" | 热点解读/纯观点 |
| 场景感 | 至少 2 处有时间/地点/对话等画面细节 | 故事/复盘 |
| 真实声音 | 至少 1 处引用真实用户评价或体验 | 对比 |

不通过 → **定向修复**：只替换不达标的具体句子/段落，不动已通过的部分。每轮最多改 3 处，改完立即重新检查该项。2 轮仍不过 → 标注跳过，继续下一项。

**5.3 脚本辅助验证**（补充 5.2 的逐项检查）：

Agent 在 5.2 检查过程中同步完成综合评估（各 H2 之间的语气差异度、信息密度的高低交替、段落间的节奏变化、整体阅读流畅度），产出 0-1 分数。

```bash
python3 {skill_dir}/scripts/humanness_score.py {article_path} --json --tier3 {agent_tier3_score}
```

解读 JSON 中 `composite_score`（0=质量高, 100=问题多）：
- < 30 → 通过，继续 Step 6
- 30-50 → 查看 `param_scores` 中最低分的 1-2 项，只修复对应的具体句子（不重写整段），改完重新打分。1 轮即可
- \> 50 → 取 `param_scores` 最低的 2-3 项，逐项定向修复（每项只改最相关的 1-2 处），最多 2 轮。仍 > 50 则标记 DONE_WITH_CONCERNS 继续

---

### Step 6: 视觉 AI（与写作同步执行）

**重要**：Step 6 应在 Step 4 写作完成后立即执行，不要等到 Step 7 导出时才处理图片。文章和配图必须同时产出。

**如果 `skip_image_gen = true`** → 只执行 6.1，输出图片提示词供用户参考。

```
读取: {skill_dir}/references/visual-prompts.md
```

**6.1 实体提取**：从终稿中提取 3-5 个**具体实体**（人物、产品名、场景、数据点、行业术语）。后续所有提示词必须包含至少 2 个实体。

**6.2 封面/首图生成**：根据目标平台生成封面提示词（按 visual-prompts.md），调用 image_gen.py 生成。

**6.3 封面验证**：
- **交互模式**：展示封面，问用户"封面效果如何？"。用户 OK → 继续；不满意 → 调整提示词重新生成。
- **全自动模式**：agent 自检——提示词中的实体是否在画面描述中可识别？如果提示词过于泛化（仅含"科技感""未来感"等抽象词，无具体实体），换一组提示词重试 1 次。

**6.3b 风格锚定**：封面确认后，提取视觉锚点（色板 hex、风格关键词、画面调性），后续所有内文配图的提示词必须引用这组锚点，保证全文视觉一致。

**6.4 内文配图**：分析文章结构，为每个需要配图的段落选择图片类型（infographic/scene/flowchart/comparison/framework/timeline），使用对应的结构化提示词模板生成配图提示词（按 visual-prompts.md）。批量调用 image_gen.py，将图片路径嵌入 Markdown 文件的对应段落之后。

**平台配图规范**：

| 平台 | 封面/首图比例 | 配图数量 | 说明 |
|------|--------------|----------|------|
| 公众号 | 2.35:1 | 3-6 张内文 | 封面 + 内文配图 |
| 小红书 | 3:4 | 最多 9 张 | 首图 + 轮播图 |
| 知乎 | 16:9 | 1-3 张 | 可选配图/信息图 |
| 百家号 | 16:9 | 2-3 张 | 封面 + 内文 |
| 微博 | 1:1 或 3:4 | 1-9 张 | 九宫格 |
| 搜狐号 | 16:9 | 2-3 张 | 封面 + 内文 |
| 今日头条 | 16:9 或 1:1 | 3 张（三图模式） | 封面组图 |
| 企鹅号 | 16:9 | 2-3 张 | 封面 + 内文 |
| 简书 | 16:9 | 可选 | 内文配图 |
| 豆瓣 | 16:9 | 可选 | 内文配图 |
| 大鱼号 | 16:9 | 2-3 张 | 封面 + 内文 |
| 36氪 | 16:9 | 1-2 张 | 数据图/配图 |

**降级**：image_gen.py 支持多 provider 自动 fallback（按 config.yaml 中 providers 列表顺序尝试）。全部失败 → 输出提示词 + 备选图库关键词，继续。

---

### Step 7: 多平台文件导出

根据目标平台，输出以下内容到 `{skill_dir}/output/{date}-{slug}/` 目录：

**单平台模式**：
```
output/
└── 2026-05-09-ai-agent-trends/
    ├── {platform}.html              # 仅 HTML 平台
    ├── {platform}.md                # 源文件（Markdown）
    ├── {platform}.docx              # Word 文档（通用格式）
    └── images/                      # 配图文件夹
        ├── cover_{platform}.png     # 封面/首图
        └── inner_{n}.png            # 内文配图
```

**多平台模式**：
```
output/
└── 2026-05-09-ai-agent-trends/
    ├── wechat.html
    ├── wechat.md
    ├── wechat.docx
    ├── xiaohongshu.md
    ├── xiaohongshu.docx
    ├── zhihu.md
    ├── zhihu.docx
    ├── baijiahao.html
    ├── baijiahao.docx
    ├── weibo.md
    ├── weibo.docx
    ├── sohu.html
    ├── sohu.docx
    ├── toutiao.html
    ├── toutiao.docx
    ├── qiehao.html
    ├── qiehao.docx
    ├── jianshu.md
    ├── jianshu.docx
    ├── douban.md
    ├── douban.docx
    ├── dayu.html
    ├── dayu.docx
    ├── kr36.md
    ├── kr36.docx
    └── images/                      # 整合配图文件夹
        ├── cover_wechat.png
        ├── cover_xiaohongshu_1.png
        ├── xiaohongshu_2.png
        ├── ...
        └── inner_*.png
```

**平台格式映射**：

| 平台 | 主格式 | Word | 说明 |
|------|--------|------|------|
| 公众号 | 内联样式 HTML | 是 | 保留微信兼容修复（外链转脚注、CJK 空格、暗黑模式等） |
| 小红书 | Markdown（emoji 优化） | 是 | 清单式排版、标签在文末 |
| 知乎 | Markdown | 是 | 知乎原生支持 Markdown |
| 百家号 | 富文本 HTML | 是 | 标准 HTML |
| 微博 | Markdown（话题标签） | 是 | 控制在 2000 字内 |
| 搜狐号 | 富文本 HTML | 是 | 标准 HTML |
| 今日头条 | 富文本 HTML | 是 | 支持三图封面模式 |
| 企鹅号 | 富文本 HTML | 是 | 标准 HTML |
| 简书 | Markdown | 是 | 简书原生支持 |
| 豆瓣 | Markdown | 是 | 标准 Markdown |
| 大鱼号 | 富文本 HTML | 是 | 标准 HTML |
| 36氪 | Markdown | 是 | 商业分析风格 |

**导出命令**：

```bash
# 单平台导出
python3 {skill_dir}/toolkit/cli.py export {markdown} --platform {platform} --output {output_dir} --theme {theme}

# 多平台导出
python3 {skill_dir}/toolkit/cli.py export {markdown} --platform all --output {output_dir} --theme {theme}
```

Converter 自动处理：
- 公众号：CJK 加空格、加粗标点外移、列表转 section、外链转脚注、暗黑模式、容器语法
- 其他平台：标准 HTML/Markdown 转换，无平台特化修复

**Word 文档生成**：
- 所有平台均生成 .docx 文件
- 内容与主格式一致，保留标题层级、加粗、引用、列表、图片等
- 方便用户离线二次编辑

---

### Step 8: 收尾

**8.1 写入历史**（导出成功或降级都要写，文件不存在则创建）：

```yaml
# → {skill_dir}/history.yaml
- date: "{日期}"
  title: "{标题}"
  topic_source: "热点抓取"  # 或 "用户指定"
  topic_keywords: ["{词1}", "{词2}"]
  platforms: ["{平台1}", "{平台2}"]  # 本次导出的平台列表
  output_dir: "{输出目录路径}"  # e.g. output/2026-05-09-ai-agent-trends/
  framework: "{框架}"
  enhance_strategy: "{增强策略}"  # angle_discovery/density_boost/detail_anchoring/real_feel
  word_count: {字数}
  writing_persona: "{人格名}"
  dimensions:
    - "{维度}: {选项}"
  closing_type: "{收尾类型}"  # trailing_off/unanswered/scene_revert/abrupt_stop/anti_conclusion/image
  composite_score: {Step 5.3 的 composite_score}  # 0=质量高, 100=问题多
  writing_config_snapshot:  # 本次使用的关键参数（从 writing-config.yaml 提取）
    sentence_variance: {值}
    paragraph_rhythm: "{值}"
    emotional_arc: "{值}"
    word_temperature_bias: "{值}"
    broken_sentence_rate: {值}
    tangent_frequency: "{值}"
    style_drift: {值}
    negative_emotion_floor: {值}
  stats: null
```

**8.2 回复用户**：

- 最终标题 + 2 备选 + 摘要 + 标签
- 输出文件清单（按平台列出文件路径）
- 编辑建议："文章有 2-3 个编辑锚点，建议加入你自己的话。你可以在本地 markdown/Word 里改。"
- 手动发布指引（简要提示各平台发布方式）

**8.3 后续操作**：

| 用户说 | 动作 |
|--------|------|
| 润色/缩写/扩写/换语气 | 编辑文章 |
| 封面换暖色调 | 重新生图 |
| 用框架 B 重写 | 回到 Step 4 |
| 换一个选题 | 回到 Step 2.3 |
| 看看有什么主题 | `python3 {skill_dir}/toolkit/cli.py gallery` |
| 换成 XX 主题 | 重新渲染 |
| 看看文章数据 | `读取: {skill_dir}/references/effect-review.md` |
| 学习我的修改 | `读取: {skill_dir}/references/learn-edits.md` |
| 学习排版 / 学排版 | `python3 {skill_dir}/scripts/learn_theme.py <url> --name <name>` |
| 检查一下 / 自检 / 这篇文章怎么样 | 生成报告（生成档案 + 质量检查，见辅助功能） |
| 导入范文 / 建范文库 | `python3 {skill_dir}/scripts/extract_exemplar.py article.md` |
| 查看范文库 | `python3 {skill_dir}/scripts/extract_exemplar.py --list` |
| 验证配置 / 检查配置 / 测试图片 | 执行图片生成验证流程 |

---

## Per-Platform 独立生成流程

当用户要求"每个平台写不一样的"或"各平台独立生成"时，执行以下流程。

### 流程概述

同主题 → 各平台独立文章（标题不同、角度不同、案例不同、金句不同） → 各平台独立配图（风格不同、构图不同） → 导出各平台文件 → 生成HTML清单

### Step P1: 确定主题和平台

```
读取: {skill_dir}/references/frameworks.md
读取: {skill_dir}/platforms/{platform}.md（所有目标平台规范）
读取: {skill_dir}/history.yaml（去重检查）
```

- 确定主题（用户提供或从热点中选取）
- 确定目标平台（用户指定或默认全部）
- 检查 history.yaml 中是否已有相同主题的文章记录

### Step P2: 为每个平台独立生成文章

```
# 调用 platform_writer.py 的 write_for_platforms() 函数
# 或 AI 助手在对话中为每个平台撰写文章
```

**去重引擎**：
- platform_writer.py 内置去重引擎，读取 history.yaml 检查已使用的标题、框架、收尾方式、维度组合
- 如果检测到重复，自动添加去重指令到 prompt 中
- 每生成一篇文章后立即写入 history.yaml，确保后续平台生成时能去重

**文章差异化策略**：
- 每个平台使用不同的 temperature（0.6-0.9）
- 每个平台使用不同的框架提示词
- 每个平台遵循各自的字数、风格、结构要求
- 标题、角度、案例、金句完全不同

**AI 助手模式**（适用于 openclaw/qclaw 等平台）：
- Python 脚本检测各平台文章文件不存在时，输出每个平台的写作要求（字数、风格、框架、保存路径）
- AI 助手（当前对话）为每个平台独立撰写文章，保存到指定路径
- 完成后重新运行脚本继续

### Step P3: 为每个平台独立生成配图

```
# 调用 platform_images.py 的 generate_platform_images() 函数
```

**配图差异化策略**：
- 每个平台使用不同的风格提示词（PLATFORM_IMAGE_STYLES）
- 每个平台使用不同的构图角度（IMAGE_ANGLE_POOL）
- 每个平台使用不同的尺寸和数量（PLATFORM_IMAGE_CONFIGS）
- 从文章内容中提取关键词，生成与文章内容相关的提示词
- 使用 seed 参数确保每个平台的图片提示词不同

### Step P4: 导出各平台文件

```
# 调用 exporter.py 的 export_platform() 函数（每个平台一次）
# 生成 Markdown + HTML + Word 文件
# 图片复制到各平台专属目录
```

### Step P5: 生成HTML清单

```
# 调用 exporter.py 的 generate_usage_guide()、generate_image_gallery_html()、generate_file_preview_html()
```

生成三个HTML清单文件：
- README_文件说明.html — 文件使用说明与发布指引
- 文件清单_可点击预览.html — 各平台文件预览与下载
- 图片清单.html — 配图预览与下载

三个文件之间可互相跳转。

### CLI 命令

```bash
python3 {skill_dir}/toolkit/cli.py per-platform "文章主题" --platforms wechat,zhihu,xiaohongshu --framework 对比 --output ./output/per-platform-topic
```

### 输出结构

```
output/per-platform-topic/
├── wechat.md / .html / .docx        # 微信公众号文章（独立内容）
├── wechat/                          # 微信公众号专属图片
│   ├── cover_wechat.png
│   └── img_wechat_*.png
├── zhihu.md / .docx                 # 知乎文章（独立内容）
├── zhihu/                           # 知乎专属图片
│   ├── cover_zhihu.png
│   └── img_zhihu_*.png
├── xiaohongshu.md / .docx           # 小红书文章（独立内容）
├── xiaohongshu/                     # 小红书专属图片
│   ├── cover_xiaohongshu.png
│   └── img_xiaohongshu_*.png
├── README_文件说明.html
├── 文件清单_可点击预览.html
└── 图片清单.html
```

### 降级处理

- 图片生成失败：输出提示词文件，不阻断流程
- 文本生成失败：跳过该平台，继续下一个
- history.yaml 不存在：跳过历史去重

---

## 错误处理

| 步骤 | 降级 |
|------|------|
| 环境检查 | 逐项引导，设降级标记 |
| 图片验证 | 失败则提示用户，设 `skip_image_gen` |
| 热点抓取 | WebSearch 替代 |
| 选题为空 | 请用户手动给选题 |
| SEO 脚本 | LLM 判断 |
| 素材采集（WebSearch） | LLM 训练数据中可验证的公开信息 |
| 维度随机化 | history 空时跳过去重 |
| Persona 文件不存在 | 回退到 midnight-friend（默认） |
| 范文库为空 | Fallback 到 exemplar-seeds.yaml（通用模式） |
| 去 AI 验证 | 2 轮定向修复不过则跳过该项 |
| 生图失败 | 输出提示词 |
| 文件导出失败 | 输出 Markdown 源文件 |
| 历史写入 | 警告不阻断 |
| 效果数据 | 告知等 24h |
| Playbook 不存在 | 用 writing-guide.md |

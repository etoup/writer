# 邮件 Newsletter 平台规范

## 输出格式
- 主格式：HTML 邮件（兼容主流邮箱客户端）
- 备用格式：Markdown + Word

## 内容参数
- 字数：800-2000 字
- 风格：个人化、有深度、像写给朋友的信
- 结构：开场白 → 核心内容（2-4 个主题）→ 个人思考 → 互动引导

## 邮件规范
- 主题行：20-40 字符，有吸引力但不标题党
- 预览文本：40-100 字符，补充主题行
- HTML 要求：内联样式、邮箱客户端兼容
- 支持：图片、链接、分栏布局

## 邮件客户端兼容性
- Gmail：支持大部分 CSS，内联样式优先
- Apple Mail：支持较多 CSS，但避免 flexbox
- Outlook：仅支持有限的 CSS，使用 table 布局
- 通用：避免外部 CSS、JavaScript、复杂布局

## SEO / 订阅优化
- 邮件主题影响打开率
- 内容质量影响退订率
- 定期发送保持读者粘性
- 提供纯文本版本（无障碍）

## 文件命名
- `newsletter_{slug}.html`（邮件 HTML）
- `newsletter_{slug}.md`（Markdown 源文件）
- `newsletter_{slug}.docx`
- `images/newsletter_{slug}.png`（邮件内图片）

## 手动发布指引
1. 使用邮件平台（Substack/Mailchimp/Beehiiv 等）
2. 创建新邮件
3. 粘贴 HTML 内容或导入 Markdown
4. 设置主题行、预览文本、发送时间
5. 预览测试 → 发送

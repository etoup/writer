# 微信公众号平台规范

## 输出格式
- 主格式：内联样式 HTML（微信兼容修复）
- 备用格式：Word 文档 (.docx)
- Markdown 源文件

## 内容参数
- 字数：1500-2500 字
- 标题：H1 20-28 字
- 结构：H1 + H2 分段

## 配图要求
- 封面比例：2.35:1（900x383）
- 内文配图：3-6 张，16:9 比例
- 图片格式：PNG

## 排版特性
- 所有 CSS 必须内联
- 外链转上标编号脚注 + 文末参考链接
- CJK-Latin 自动加空格
- 加粗标点移到 `</strong>` 外
- `<ul>/<ol>` 转样式化 `<section>`
- 注入 `data-darkmode-*` 属性支持暗黑模式
- 支持容器语法：`:::dialogue`、`:::timeline`、`:::callout`、`:::quote`

## 文件命名
- `{slug}.html`
- `{slug}.docx`
- `{slug}.md`
- `images/cover_{slug}.png`
- `images/inner_{n}.png`

## 手动发布指引
1. 登录公众号后台
2. 新建图文素材
3. 复制 HTML 内容到编辑器（或导入 Word）
4. 上传封面图
5. 内文图片通过 Markdown 中的图片路径上传

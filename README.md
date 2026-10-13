# Marginalia · 学术阅读札记

一款本地优先的学术阅读助手，用来收录阅读中的生词、长难句、来源与结构分析，并通过轻量复习把摘录转化为可复用的语言知识。

## 功能

- 今日概览：生词、难句、待复习、已掌握和来源统计
- 快速收录：连续保存生词或难句，保留来源、语境和标签
- CSV 批量导入：下载模板、上传预览、格式校验并自动跳过重复项
- 阅读资料库：全文搜索，按类型、来源和掌握状态筛选
- 卡片与表格视图：适合阅读，也方便快速浏览
- 编辑与删除：直接维护已有卡片
- 复习书桌：展开答案并标记待复习、学习中或已掌握
- 旧数据迁移：首次启动自动导入根目录中的 `vocabulary.csv`
- iPhone PWA：独立于桌面版，可添加到主屏幕并离线收录、检索和复习
- 可选跨设备同步：使用同一 Supabase 账号在电脑与 iPhone 间同步，断网时继续本地使用

## iPhone 离线版

访问 [Marginalia iPhone PWA](https://congchou.github.io/marginalia-reading-notebook/pwa/)。首次打开需要联网，以缓存界面文件。在 iPhone 的 Safari 中点击“分享”→“添加到主屏幕”，开启“作为网页 App 打开”。之后从主屏幕图标启动，便可离线使用。

iPhone 版的数据先保存在该设备的浏览器数据库中。未设置云端时，可在电脑版「阅读资料库」点击「导出全部卡片 CSV」，然后在**主屏幕上的 PWA**里打开「数据与安装」并导入该文件。网页版与主屏幕版可能使用不同的数据空间，请先安装、再导入。

更换手机、清理网站数据或卸载 App 前，请在 PWA 的「数据与安装」导出 CSV 并保存到“文件”App 或你信任的位置。PWA 源码位于 `docs/pwa/`，由 GitHub Pages 托管，无需 Streamlit 服务或额外账号。

## 本地运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

浏览器访问 `http://localhost:8501`。

## 数据与隐私

电脑版的本地副本保存在 `data/marginalia.db`，iPhone 版的本地副本保存在浏览器数据库。数据库、同步配置与旧版 CSV 均已被 Git 忽略，不会随代码上传。开启云端同步并登录后，卡片会传输至你自己配置的 Supabase 项目；未配置或未登录时仍为纯本地使用。应用会在本地检测并迁移旧生词文件。

## 可选：开启电脑与 iPhone 自动同步

1. 先在两端导出 CSV 备份。创建一个 [Supabase 项目](https://supabase.com/dashboard/projects)，在 SQL Editor 执行 [schema.sql](supabase/schema.sql)。此脚本启用按用户隔离的 Row Level Security。
2. 从项目的 API Keys 页面复制 **Project URL** 和以 `sb_publishable_` 开头的 **publishable key**。不要使用 `sb_secret_`、`service_role` 或数据库密码。项目的 Authentication → URL Configuration 中把 Site URL 设置为 `https://congchou.github.io/marginalia-reading-notebook/pwa/`，以便注册邮件验证后返回应用。
3. 电脑版左侧展开「跨设备同步」，填写 URL 与 publishable key；iPhone 主屏幕 App 内进入「数据与安装」→「跨设备同步」，填写相同信息。两端用**同一邮箱和密码**登录；新账号按邮件提示先验证邮箱。
4. 建议先在电脑版登录并完成首次上传，再在 iPhone 登录下载。之后两端联网时会自动同步；电脑端应用需要运行或重新打开才能补齐它离线期间的变化。若两端同时修改同一条，旧版本不会覆盖新版本，会显示冲突提醒；先导出 CSV 备份再人工处理。

云端尚未配置时，跨设备同步按钮只显示设置入口，不影响收录、检索或复习。iPhone 端的修改先落在 IndexedDB，恢复网络并重新打开 App 后补传；删除以云端标记传播。请保留定期 CSV 备份，自动同步不等于可恢复的历史备份。

## CSV 批量导入格式

在左侧选择「批量导入」并下载模板。CSV 固定包含以下列：

```text
type,word,meaning,sentence,translation,structure,source,tags,status
```

- 生词行：`type=生词`，`word`、`meaning` 必填。
- 难句行：`type=难句`，`sentence`、`translation` 必填。
- `tags` 用英文逗号分隔；`status` 可填“待复习”“学习中”或“已掌握”。
- 支持 macOS Numbers、Microsoft Excel 导出的 UTF-8 CSV。

## 测试

测试只依赖 Python 标准库：

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q app.py marginalia
node --test docs/pwa/tests/*.test.mjs
```

## 项目结构

```text
app.py                  Streamlit 界面与页面流程
marginalia/database.py  SQLite 数据访问与旧数据迁移
marginalia/ui.py        视觉主题与纯展示辅助函数
tests/                  数据层、展示辅助与烟雾测试
data/                   本地数据库目录
```

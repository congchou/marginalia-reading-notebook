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

## iPhone 离线版

访问 [Marginalia iPhone PWA](https://congchou.github.io/marginalia-reading-notebook/pwa/)。首次打开需要联网，以缓存界面文件。在 iPhone 的 Safari 中点击“分享”→“添加到主屏幕”，开启“作为网页 App 打开”。之后从主屏幕图标启动，便可离线使用。

iPhone 版的数据保存在该设备的浏览器数据库中，不会和电脑上的 SQLite 自动同步。迁移已有数据时，在电脑版「阅读资料库」点击「导出全部卡片 CSV」，然后在**主屏幕上的 PWA**里打开「数据与安装」并导入该文件。网页版与主屏幕版可能使用不同的数据空间，请先安装、再导入。

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

个人数据保存在 `data/marginalia.db`。数据库与旧版 `vocabulary.csv`、`sentences.csv` 均已被 Git 忽略，不会随代码上传。应用会在本地检测并迁移旧生词文件。

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
node --test docs/pwa/tests/data.test.mjs
```

## 项目结构

```text
app.py                  Streamlit 界面与页面流程
marginalia/database.py  SQLite 数据访问与旧数据迁移
marginalia/ui.py        视觉主题与纯展示辅助函数
tests/                  数据层、展示辅助与烟雾测试
data/                   本地数据库目录
```

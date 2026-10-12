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
```

## 项目结构

```text
app.py                  Streamlit 界面与页面流程
marginalia/database.py  SQLite 数据访问与旧数据迁移
marginalia/ui.py        视觉主题与纯展示辅助函数
tests/                  数据层、展示辅助与烟雾测试
data/                   本地数据库目录
```

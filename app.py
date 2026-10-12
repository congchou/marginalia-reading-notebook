from __future__ import annotations

import random
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from marginalia.database import (
    DEFAULT_STATUS, STATUSES, DuplicateEntryError, add_entry, delete_entry,
    get_sources, get_stats, import_legacy_csv, init_db, list_entries, update_entry,
)
from marginalia.ui import APP_CSS, display_tags, excerpt, normalize_tags

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "marginalia.db"
st.set_page_config(page_title="Marginalia · 学术阅读札记", page_icon="📚", layout="wide", initial_sidebar_state="expanded")
init_db(DB_PATH)
imported_count = import_legacy_csv(DB_PATH, ROOT / "vocabulary.csv")
st.markdown(APP_CSS, unsafe_allow_html=True)


def page_heading(kicker: str, title: str, lead: str) -> None:
    st.markdown(f'<div class="eyebrow">{escape(kicker)}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="page-lead">{escape(lead)}</div>', unsafe_allow_html=True)


def metric_card(label: str, value: int | str) -> None:
    st.markdown(f'<div class="metric-card"><div class="value">{escape(str(value))}</div><div class="label">{escape(label)}</div></div>', unsafe_allow_html=True)


def entry_card(entry_type: str, item: dict, reveal: bool = True) -> None:
    is_word = entry_type == "vocabulary"
    title = item["word"] if is_word else excerpt(item["sentence"], 150)
    main = item["meaning"] if is_word else item["translation"]
    detail = item.get("sentence", "") if is_word else item.get("structure", "")
    body = ""
    if reveal:
        body = f'<div class="entry-copy"><strong>{escape(str(main))}</strong></div>'
        if detail:
            body += f'<div class="entry-copy">{escape(str(detail))}</div>'
    metadata = " · ".join(part for part in [("生词" if is_word else "难句"), item.get("source") or "未标注来源", item.get("created_at", "")[:10]] if part)
    css_class = "entry-card" if is_word else "entry-card sentence"
    st.markdown(f'<div class="{css_class}"><div class="entry-title">{escape(str(title))}</div>{body}{display_tags(item.get("tags", ""))}<div class="entry-meta">{escape(metadata)}　<span class="status-pill">{escape(item.get("status", DEFAULT_STATUS))}</span></div></div>', unsafe_allow_html=True)


def save_entry(table: str, payload: dict) -> bool:
    payload["tags"] = normalize_tags(payload.get("tags", ""))
    try:
        add_entry(DB_PATH, table, payload)
    except (ValueError, DuplicateEntryError) as exc:
        st.error(str(exc))
        return False
    st.success("已收录到阅读资料库。")
    return True


def render_dashboard() -> None:
    stats = get_stats(DB_PATH)
    st.markdown('<div class="hero-card"><div class="eyebrow" style="color:#f0d7b6">Research notebook</div><h2>今天读了什么？</h2><p>把论文、书籍与雅思材料中的语言发现，整理成一座可以反复翻阅的个人卡片盒。</p></div>', unsafe_allow_html=True)
    labels = [("生词卡片", stats["vocabulary"]), ("难句摘录", stats["sentences"]), ("待复习", stats["pending"]), ("已掌握", stats["mastered"]), ("资料来源", stats["sources"])]
    for column, (label, value) in zip(st.columns(5), labels):
        with column:
            metric_card(label, value)
    left, right = st.columns([1.6, 1], gap="large")
    with left:
        st.subheader("最近收录")
        recent = [("vocabulary", item) for item in list_entries(DB_PATH, "vocabulary", limit=3)] + [("sentences", item) for item in list_entries(DB_PATH, "sentences", limit=3)]
        recent.sort(key=lambda pair: (pair[1].get("created_at", ""), pair[1]["id"]), reverse=True)
        if recent:
            for entry_type, item in recent[:5]:
                entry_card(entry_type, item)
        else:
            st.info("卡片盒还是空的。去「快速收录」保存第一条阅读笔记吧。")
    with right:
        st.subheader("复习节奏")
        total = stats["vocabulary"] + stats["sentences"]
        ratio = int(stats["mastered"] / total * 100) if total else 0
        st.progress(ratio / 100, text=f"已掌握 {ratio}%")
        st.caption("复习不是一次完成，而是让陌生表达逐渐变得熟悉。")
        st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
        st.subheader("最近来源")
        sources = get_sources(DB_PATH)
        if sources:
            for source in sources[-6:]:
                st.markdown(f"- {escape(source)}")
        else:
            st.caption("新增条目时填写论文、书籍或题目名称。")


def render_capture() -> None:
    page_heading("Capture", "快速收录", "阅读时先记下来，整理可以稍后发生。")
    word_tab, sentence_tab = st.tabs(["生词卡片", "难句摘录"])
    source_hint = get_sources(DB_PATH)[-1] if get_sources(DB_PATH) else ""
    with word_tab:
        st.subheader("收录一个新表达")
        with st.form("add_word", clear_on_submit=True):
            col1, col2 = st.columns(2)
            word = col1.text_input("单词或短语 *", placeholder="e.g. prevailing")
            meaning = col2.text_input("释义 *", placeholder="盛行的；占主导地位的")
            sentence = st.text_area("原文语境", placeholder="Paste the sentence where you found it...", height=120)
            col3, col4 = st.columns(2)
            source = col3.text_input("来源", value=source_hint, placeholder="论文标题 / Cambridge IELTS 11")
            tags = col4.text_input("标签", placeholder="environment, writing")
            submitted = st.form_submit_button("存入卡片盒", width="stretch")
        if submitted:
            save_entry("vocabulary", {"word": word, "meaning": meaning, "sentence": sentence, "source": source, "tags": tags, "status": DEFAULT_STATUS})
    with sentence_tab:
        st.subheader("保存一段值得拆解的句子")
        with st.form("add_sentence", clear_on_submit=True):
            sentence_text = st.text_area("英文原句 *", placeholder="Paste a complex sentence...", height=145)
            translation = st.text_area("中文翻译 *", placeholder="写下自然、准确的译文", height=100)
            structure = st.text_area("结构分析", placeholder="主干、从句、修饰关系与关键表达", height=110)
            col1, col2 = st.columns(2)
            source = col1.text_input("来源", value=source_hint, key="sentence_source")
            tags = col2.text_input("标签", placeholder="clause, methods", key="sentence_tags")
            submitted = st.form_submit_button("存入卡片盒", width="stretch")
        if submitted:
            save_entry("sentences", {"sentence": sentence_text, "structure": structure, "translation": translation, "source": source, "tags": tags, "status": DEFAULT_STATUS})


def edit_panel(table: str, item: dict) -> None:
    is_word = table == "vocabulary"
    title = item["word"] if is_word else excerpt(item["sentence"], 54)
    with st.expander(f"编辑 · {title}"):
        with st.form(f"edit_{table}_{item['id']}"):
            if is_word:
                first = st.text_input("单词或短语 *", value=item["word"])
                second = st.text_input("释义 *", value=item["meaning"])
                third = st.text_area("原文语境", value=item["sentence"], height=100)
            else:
                first = st.text_area("英文原句 *", value=item["sentence"], height=120)
                second = st.text_area("中文翻译 *", value=item["translation"], height=90)
                third = st.text_area("结构分析", value=item["structure"], height=90)
            c1, c2, c3 = st.columns(3)
            source = c1.text_input("来源", value=item["source"])
            tags = c2.text_input("标签", value=item["tags"])
            status = c3.selectbox("状态", STATUSES, index=STATUSES.index(item["status"]))
            save_col, delete_col = st.columns(2)
            save = save_col.form_submit_button("保存修改", width="stretch")
            remove = delete_col.form_submit_button("确认删除", width="stretch")
        if save:
            payload = {"source": source, "tags": normalize_tags(tags), "status": status}
            payload.update(({"word": first, "meaning": second, "sentence": third} if is_word else {"sentence": first, "translation": second, "structure": third}))
            try:
                update_entry(DB_PATH, table, item["id"], payload)
                st.success("修改已保存。")
                st.rerun()
            except (ValueError, DuplicateEntryError) as exc:
                st.error(str(exc))
        if remove:
            delete_entry(DB_PATH, table, item["id"])
            st.toast("条目已删除")
            st.rerun()


def render_library() -> None:
    page_heading("Archive", "阅读资料库", "按来源、主题和掌握状态，重新发现你读过的内容。")
    search = st.text_input("搜索资料库", placeholder="搜索单词、句子、释义、翻译、来源或标签…", label_visibility="collapsed")
    f1, f2, f3 = st.columns(3)
    entry_type = f1.selectbox("类型", ["全部", "生词", "难句"])
    source = f2.selectbox("来源", ["全部来源", *get_sources(DB_PATH)])
    status = f3.selectbox("掌握状态", ["全部状态", *STATUSES])
    view = st.radio("视图", ["卡片", "表格"], horizontal=True, label_visibility="collapsed")
    tables = (["vocabulary"] if entry_type == "生词" else ["sentences"] if entry_type == "难句" else ["vocabulary", "sentences"])
    results = [(table, item) for table in tables for item in list_entries(DB_PATH, table, search=search, source="" if source == "全部来源" else source, status="" if status == "全部状态" else status)]
    results.sort(key=lambda pair: (pair[1].get("created_at", ""), pair[1]["id"]), reverse=True)
    st.caption(f"找到 {len(results)} 条阅读笔记")
    if not results:
        st.info("没有找到匹配内容，试试减少筛选条件。")
    elif view == "表格":
        rows = [{"类型": "生词" if table == "vocabulary" else "难句", "内容": item.get("word") or excerpt(item.get("sentence"), 80), "释义 / 翻译": item.get("meaning") or excerpt(item.get("translation"), 80), "来源": item.get("source") or "—", "标签": item.get("tags") or "—", "状态": item["status"]} for table, item in results]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    else:
        for table, item in results:
            entry_card(table, item)
            edit_panel(table, item)


def review_pool() -> list[tuple[str, dict]]:
    return [(table, item) for table in ("vocabulary", "sentences") for item in list_entries(DB_PATH, table) if item["status"] != "已掌握"]


def render_review() -> None:
    page_heading("Review desk", "复习书桌", "先回忆，再展开答案；用状态记录熟悉程度。")
    pool = review_pool()
    if not pool:
        st.success("目前没有待复习内容。新收录的卡片会出现在这里。")
        return
    valid_keys = {(table, item["id"]) for table, item in pool}
    if st.session_state.get("review_key") not in valid_keys:
        table, item = random.choice(pool)
        st.session_state.review_key = (table, item["id"])
        st.session_state.review_reveal = False
    table, entry_id = st.session_state.review_key
    item = next(item for candidate, item in pool if candidate == table and item["id"] == entry_id)
    st.caption(f"还有 {len(pool)} 张卡片等待巩固")
    entry_card(table, item, st.session_state.get("review_reveal", False))
    if not st.session_state.get("review_reveal", False):
        if st.button("展开答案", width="stretch"):
            st.session_state.review_reveal = True
            st.rerun()
    else:
        st.markdown("#### 这张卡片现在有多熟悉？")
        for column, (label, next_status) in zip(st.columns(3), [("还不熟", "待复习"), ("有印象", "学习中"), ("已掌握", "已掌握")]):
            if column.button(label, key=f"review_{next_status}", width="stretch"):
                update_entry(DB_PATH, table, item["id"], {**item, "status": next_status})
                st.session_state.pop("review_key", None)
                st.session_state.review_reveal = False
                st.rerun()
        if st.button("换一张，不更新状态"):
            st.session_state.pop("review_key", None)
            st.session_state.review_reveal = False
            st.rerun()


with st.sidebar:
    st.markdown("# Marginalia")
    st.caption("学术阅读札记 · Reading archive")
    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    page = st.radio("导航", ["今日概览", "快速收录", "阅读资料库", "复习书桌"], label_visibility="collapsed")
    st.markdown('<div style="height:1.5rem"></div>', unsafe_allow_html=True)
    sidebar_stats = get_stats(DB_PATH)
    st.caption(f"本地资料库 · {sidebar_stats['vocabulary'] + sidebar_stats['sentences']} 张卡片")
    st.caption("数据只保存在当前设备")

if imported_count:
    st.toast(f"已从旧版导入 {imported_count} 个生词")

{"今日概览": render_dashboard, "快速收录": render_capture, "阅读资料库": render_library, "复习书桌": render_review}[page]()

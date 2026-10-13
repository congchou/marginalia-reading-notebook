import { CSV_COLUMNS, STATUSES, exportEntriesCsv, identityOf, mergeImportedEntries, normalizeEntry, parseImportCsv } from './data.mjs';
import { getAllEntries, putEntry, putEntries, removeEntry } from './storage.mjs';

const content = document.querySelector('#content');
const dialog = document.querySelector('#entry-dialog');
const toastElement = document.querySelector('#toast');
const state = { page: 'home', captureKind: 'word', entries: [], search: '', kindFilter: 'all', statusFilter: 'all', reviewId: null, revealed: false, importResult: null };
let toastTimer;

const html = (value) => String(value ?? '').replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]);
const dateText = (value) => value ? new Date(value).toLocaleDateString('zh-CN') : '';
const titleOf = (entry) => entry.kind === 'word' ? entry.word : entry.sentence;
const answerOf = (entry) => entry.kind === 'word' ? entry.meaning : entry.translation;
const typeOf = (entry) => entry.kind === 'word' ? '生词' : '难句';
const recentEntries = () => [...state.entries].sort((a, b) => String(b.updatedAt).localeCompare(String(a.updatedAt)));

function showToast(message) {
  toastElement.textContent = message;
  toastElement.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastElement.classList.remove('show'), 3300);
}

function heading(kicker, title, lead) {
  return `<p class="eyebrow">${html(kicker)}</p><h1>${html(title)}</h1><p class="lead">${html(lead)}</p>`;
}

function tagsHtml(tags) {
  return (tags || []).map((tag) => `<span class="tag">${html(tag)}</span>`).join('');
}

function cardHtml(entry, openable = true) {
  const title = html(titleOf(entry));
  const answer = html(answerOf(entry));
  const body = `<div class="card-title">${title}</div><div class="card-body">${answer}</div>${tagsHtml(entry.tags)}<div class="card-meta"><span>${typeOf(entry)}</span><span>·</span><span>${html(entry.source || '未标注来源')}</span><span class="status">${html(entry.status)}</span></div>`;
  return `<article class="card ${entry.kind === 'sentence' ? 'sentence' : ''}">${openable ? `<button type="button" class="card-button" data-action="open-entry" data-id="${html(entry.id)}" aria-label="查看 ${title}">${body}</button>` : body}</article>`;
}

function renderHome() {
  const words = state.entries.filter((entry) => entry.kind === 'word').length;
  const sentences = state.entries.length - words;
  const pending = state.entries.filter((entry) => entry.status !== '已掌握').length;
  const mastered = state.entries.length - pending;
  const recent = recentEntries().slice(0, 4);
  return `<section class="hero"><p class="eyebrow">Research notebook</p><h1>读到哪里，记到哪里。</h1><p>让每个新词与难句，都成为可以再次翻开的阅读卡片。</p><div class="hero-actions"><button type="button" data-action="go-capture">＋ 新增卡片</button><button type="button" data-action="go-review">开始复习</button></div></section>
    <div class="stats"><div class="stat"><strong>${words}</strong><span>生词卡片</span></div><div class="stat"><strong>${sentences}</strong><span>难句摘录</span></div><div class="stat"><strong>${pending}</strong><span>待巩固</span></div><div class="stat"><strong>${mastered}</strong><span>已掌握</span></div></div>
    <div class="section-title"><h2>最近收录</h2><button type="button" class="text-button" data-action="go-library">查看全部 →</button></div>
    ${recent.length ? recent.map((entry) => cardHtml(entry)).join('') : '<div class="empty">卡片盒还空着。收录第一个生词或难句吧。</div>'}`;
}

function captureFields(kind, entry = {}) {
  if (kind === 'word') return `<label class="field"><span>单词或短语 *</span><input name="word" required autocomplete="off" placeholder="例如 prevailing" value="${html(entry.word || '')}"></label>
    <label class="field"><span>释义 *</span><input name="meaning" required placeholder="写下准确的含义" value="${html(entry.meaning || '')}"></label>
    <label class="field"><span>原文语境</span><textarea name="sentence" placeholder="摘录它出现的句子">${html(entry.sentence || '')}</textarea></label>`;
  return `<label class="field"><span>英文原句 *</span><textarea name="sentence" required placeholder="粘贴值得拆解的难句">${html(entry.sentence || '')}</textarea></label>
    <label class="field"><span>中文翻译 *</span><textarea name="translation" required placeholder="写下自然准确的译文">${html(entry.translation || '')}</textarea></label>
    <label class="field"><span>结构分析</span><textarea name="structure" placeholder="主干、从句和修饰关系">${html(entry.structure || '')}</textarea></label>`;
}

function commonFields(entry = {}, editing = false) {
  const latestSource = recentEntries().find((item) => item.source)?.source || '';
  return `<label class="field"><span>来源</span><input name="source" placeholder="论文、书籍或题目" value="${html(entry.source ?? (editing ? '' : latestSource))}"></label>
    <label class="field"><span>标签</span><input name="tags" placeholder="多个标签用逗号隔开" value="${html((entry.tags || []).join(', '))}"></label>
    ${editing ? `<label class="field"><span>学习状态</span><select name="status">${STATUSES.map((status) => `<option value="${status}" ${entry.status === status ? 'selected' : ''}>${status}</option>`).join('')}</select></label>` : ''}`;
}

function renderCapture() {
  const kind = state.captureKind;
  return `${heading('Capture', '快速收录', '读到新的表达，随手放进自己的卡片盒。')}
    <div class="tabs" role="tablist" aria-label="收录类型"><button type="button" role="tab" aria-selected="${kind === 'word'}" class="${kind === 'word' ? 'active' : ''}" data-action="capture-word">生词卡片</button><button type="button" role="tab" aria-selected="${kind === 'sentence'}" class="${kind === 'sentence' ? 'active' : ''}" data-action="capture-sentence">难句摘录</button></div>
    <form id="capture-form" class="panel"><h2>${kind === 'word' ? '收录一个新表达' : '保存一段值得拆解的句子'}</h2>${captureFields(kind)}${commonFields()}<button class="primary" type="submit">保存到卡片盒</button></form>`;
}

function filteredEntries() {
  const needle = state.search.trim().toLocaleLowerCase();
  return recentEntries().filter((entry) => {
    if (state.kindFilter !== 'all' && entry.kind !== state.kindFilter) return false;
    if (state.statusFilter !== 'all' && entry.status !== state.statusFilter) return false;
    if (!needle) return true;
    return [entry.word, entry.meaning, entry.sentence, entry.translation, entry.structure, entry.source, ...(entry.tags || [])]
      .some((value) => String(value || '').toLocaleLowerCase().includes(needle));
  });
}

function renderLibraryResults() {
  const entries = filteredEntries();
  return `<p class="lead" style="margin:0 0 10px">找到 ${entries.length} 张卡片</p>${entries.length ? entries.map((entry) => cardHtml(entry)).join('') : '<div class="empty">没有匹配的卡片，试试其他关键词或筛选条件。</div>'}`;
}

function renderLibrary() {
  return `${heading('Archive', '阅读资料库', '搜索来源、标签和正文，重新发现读过的内容。')}
    <div class="search-row"><input id="library-search" type="search" aria-label="搜索卡片" placeholder="搜索词语、句子、来源或标签" value="${html(state.search)}"></div>
    <div class="filter-row"><select id="kind-filter" aria-label="类型"><option value="all">全部类型</option><option value="word" ${state.kindFilter === 'word' ? 'selected' : ''}>生词</option><option value="sentence" ${state.kindFilter === 'sentence' ? 'selected' : ''}>难句</option></select>
    <select id="status-filter" aria-label="学习状态"><option value="all">全部状态</option>${STATUSES.map((status) => `<option value="${status}" ${state.statusFilter === status ? 'selected' : ''}>${status}</option>`).join('')}</select></div>
    <div id="library-results">${renderLibraryResults()}</div>`;
}

function dueEntries() { return state.entries.filter((entry) => entry.status !== '已掌握'); }

function nextReview(excludingId = null) {
  const pool = dueEntries().filter((entry) => entry.id !== excludingId);
  const options = pool.length ? pool : dueEntries();
  state.reviewId = options.length ? options[Math.floor(Math.random() * options.length)].id : null;
  state.revealed = false;
}

function renderReview() {
  const due = dueEntries();
  if (!due.length) return `${heading('Review desk', '复习书桌', '先回忆，再展开答案。')}<div class="empty">目前没有待复习卡片。新收录的内容会出现在这里。</div>`;
  if (!due.some((entry) => entry.id === state.reviewId)) nextReview();
  const entry = due.find((item) => item.id === state.reviewId);
  const done = state.entries.length - due.length;
  const percent = state.entries.length ? Math.round(done / state.entries.length * 100) : 0;
  return `${heading('Review desk', '复习书桌', `还有 ${due.length} 张卡片等待巩固。`)}
    <p class="lead" style="margin-bottom:6px">已掌握 ${percent}%</p><div class="progress"><span style="width:${percent}%"></span></div>
    <article class="card ${entry.kind === 'sentence' ? 'sentence' : ''} review-card"><p class="eyebrow">${typeOf(entry)} · ${html(entry.source || '未标注来源')}</p><div class="card-title">${html(titleOf(entry))}</div>
    ${state.revealed ? `<div class="review-answer"><strong>${html(answerOf(entry))}</strong>${entry.kind === 'word' && entry.sentence ? `<p>${html(entry.sentence)}</p>` : ''}${entry.kind === 'sentence' && entry.structure ? `<p>${html(entry.structure)}</p>` : ''}</div>` : ''}</article>
    ${state.revealed ? '<div class="review-actions"><button type="button" data-action="review-status" data-status="待复习">还不熟</button><button type="button" data-action="review-status" data-status="学习中">有印象</button><button type="button" data-action="review-status" data-status="已掌握">已掌握</button></div>' : '<button type="button" class="primary" data-action="reveal">展开答案</button>'}
    <button type="button" class="text-button" data-action="review-skip" style="display:block;margin:15px auto">换一张卡片</button>`;
}

function renderImportPreview() {
  const result = state.importResult;
  if (!result) return '';
  return `<div class="section-title"><h2>导入预览</h2></div>
    <p class="lead">${result.entries.length} 条格式正确 · ${result.errors.length} 条需要修改</p>
    ${result.errors.length ? `<ul class="error-list">${result.errors.slice(0, 20).map((error) => `<li>${html(error)}</li>`).join('')}</ul>` : ''}
    ${result.entries.length ? `<div class="preview-list">${result.entries.slice(0, 30).map((entry) => `<div class="preview-row">${typeOf(entry)} · ${html(titleOf(entry))}</div>`).join('')}</div><button type="button" class="primary" data-action="confirm-import">确认导入有效记录</button>` : '<div class="empty">没有可导入的有效记录。</div>'}`;
}

function renderData() {
  const online = navigator.onLine;
  const swReady = Boolean(navigator.serviceWorker?.controller);
  return `${heading('Your data', '数据与安装', '所有卡片都留在这台设备上。')}
    <div class="info-box"><strong>${online ? '当前在线' : '当前离线'}</strong> · ${swReady ? '离线资源已缓存' : '首次打开后请保持联网，等待离线资源完成缓存。'}<br>卡片内容保存在本机浏览器数据库，不会上传到本站。</div>
    <div class="section-title"><h2>备份与迁移</h2></div>
    <div class="panel"><p>导出标准 CSV，再用 iPhone 的“文件”App 保存一份备份。手机更换或浏览器数据被清除时，可用备份恢复。</p>
    <button type="button" class="secondary" data-action="export-csv">导出全部 ${state.entries.length} 张卡片</button>
    <label class="field" style="margin-top:20px"><span>从 CSV 导入</span><input id="csv-file" class="file-input" type="file" accept=".csv,text/csv,text/plain"></label>
    <p class="lead" style="margin:0">列名：${html(CSV_COLUMNS.join(', '))}</p></div>
    ${renderImportPreview()}
    <div class="section-title"><h2>添加到主屏幕</h2></div>
    <div class="panel"><p>在 iPhone Safari 打开本页，点“分享”，选择“添加到主屏幕”，并开启“作为网页 App 打开”。安装后请从主屏幕图标打开，再导入 CSV。</p><p class="lead" style="margin:0">首次安装需要联网；之后可在飞行模式下打开和使用。请定期导出 CSV 备份。</p></div>`;
}

function render() {
  const screens = { home: renderHome, capture: renderCapture, library: renderLibrary, review: renderReview, data: renderData };
  content.innerHTML = screens[state.page]();
  for (const button of document.querySelectorAll('[data-page]')) {
    const active = button.dataset.page === state.page;
    button.classList.toggle('active', active);
    button.setAttribute('aria-current', active ? 'page' : 'false');
  }
}

async function refresh() {
  state.entries = await getAllEntries();
  render();
}

function go(page) {
  state.page = page;
  render();
  window.scrollTo({ top: 0, behavior: 'instant' });
}

function formPayload(form, kind, existing = {}) {
  const values = Object.fromEntries(new FormData(form));
  return normalizeEntry({ ...existing, ...values, kind, updatedAt: new Date().toISOString() });
}

async function saveForm(form, kind, existing = null) {
  try {
    const entry = formPayload(form, kind, existing || {});
    const duplicate = state.entries.find((item) => item.id !== entry.id && identityOf(item) === identityOf(entry));
    if (duplicate) throw new Error('这条内容已经在资料库里');
    await putEntry(entry);
    await refresh();
    if (dialog.open) dialog.close();
    showToast(existing ? '修改已保存' : '已收录到卡片盒');
  } catch (error) { showToast(error.message || '保存失败，请重试'); }
}

function showEntry(id, editing = false) {
  const entry = state.entries.find((item) => item.id === id);
  if (!entry) return;
  if (editing) {
    dialog.innerHTML = `<div class="dialog-content"><div class="dialog-top"><h2>编辑${typeOf(entry)}</h2><button type="button" class="dialog-close" data-action="close-dialog" aria-label="关闭">×</button></div>
      <form id="edit-form" data-id="${html(id)}" data-kind="${entry.kind}">${captureFields(entry.kind, entry)}${commonFields(entry, true)}<button class="primary" type="submit">保存修改</button></form></div>`;
  } else {
    dialog.innerHTML = `<div class="dialog-content"><div class="dialog-top"><p class="eyebrow">${typeOf(entry)} · ${html(entry.status)}</p><button type="button" class="dialog-close" data-action="close-dialog" aria-label="关闭">×</button></div>
      <h2>${html(titleOf(entry))}</h2><p class="dialog-detail"><strong>${html(answerOf(entry))}</strong></p>
      ${entry.kind === 'word' && entry.sentence ? `<p class="dialog-detail">${html(entry.sentence)}</p>` : ''}
      ${entry.kind === 'sentence' && entry.structure ? `<p class="dialog-detail">结构：${html(entry.structure)}</p>` : ''}
      ${tagsHtml(entry.tags)}<p class="card-meta">${html(entry.source || '未标注来源')} · ${dateText(entry.createdAt)}</p>
      <div class="dialog-actions"><button type="button" class="secondary" data-action="edit-entry" data-id="${html(id)}">编辑</button><button type="button" class="secondary danger" data-action="delete-entry" data-id="${html(id)}">删除</button></div></div>`;
  }
  if (!dialog.open) dialog.showModal();
}

async function exportCsv() {
  const blob = new Blob([exportEntriesCsv(state.entries)], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `marginalia-backup-${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 60000);
  showToast('CSV 备份已开始下载');
}

async function readImportFile(file) {
  if (!file) return;
  if (file.size > 5 * 1024 * 1024) { showToast('文件超过 5 MB，请拆分导入'); return; }
  try {
    const text = await file.text();
    if (text.includes('\uFFFD')) { showToast('文件编码异常，请导出 UTF-8 CSV'); return; }
    state.importResult = parseImportCsv(text);
    render();
  } catch (error) { showToast(error.message || '读取 CSV 失败，请重试'); }
}

async function confirmImport() {
  if (!state.importResult) return;
  try {
    const { added, skipped } = mergeImportedEntries(state.entries, state.importResult.entries);
    await putEntries(added);
    state.importResult = null;
    await refresh();
    showToast(`导入 ${added.length} 张卡片，跳过 ${skipped} 条重复内容`);
  } catch (error) { showToast(error.message || '导入失败'); }
}

document.addEventListener('click', async (event) => {
  const target = event.target.closest('[data-action], [data-page]');
  if (!target) return;
  if (target.dataset.page) { go(target.dataset.page); return; }
  const action = target.dataset.action;
  if (action === 'go-data') go('data');
  else if (action === 'go-capture') go('capture');
  else if (action === 'go-review') go('review');
  else if (action === 'go-library') go('library');
  else if (action === 'capture-word' || action === 'capture-sentence') { state.captureKind = action === 'capture-word' ? 'word' : 'sentence'; render(); }
  else if (action === 'open-entry') showEntry(target.dataset.id);
  else if (action === 'edit-entry') showEntry(target.dataset.id, true);
  else if (action === 'close-dialog') dialog.close();
  else if (action === 'delete-entry') {
    if (!window.confirm('确定删除这张卡片吗？此操作无法撤销。')) return;
    try { await removeEntry(target.dataset.id); dialog.close(); await refresh(); showToast('卡片已删除'); }
    catch (error) { showToast(error.message || '删除失败'); }
  }
  else if (action === 'reveal') { state.revealed = true; render(); }
  else if (action === 'review-skip') { nextReview(state.reviewId); render(); }
  else if (action === 'review-status') {
    const entry = state.entries.find((item) => item.id === state.reviewId);
    if (!entry) return;
    try { await putEntry({ ...entry, status: target.dataset.status, updatedAt: new Date().toISOString() }); nextReview(entry.id); await refresh(); showToast('复习状态已更新'); }
    catch (error) { showToast(error.message || '更新失败'); }
  }
  else if (action === 'export-csv') exportCsv();
  else if (action === 'confirm-import') confirmImport();
});

document.addEventListener('submit', async (event) => {
  if (event.target.id === 'capture-form') { event.preventDefault(); await saveForm(event.target, state.captureKind); }
  if (event.target.id === 'edit-form') {
    event.preventDefault();
    const existing = state.entries.find((item) => item.id === event.target.dataset.id);
    if (existing) await saveForm(event.target, existing.kind, existing);
  }
});

document.addEventListener('input', (event) => {
  if (event.target.id !== 'library-search') return;
  state.search = event.target.value;
  const results = document.querySelector('#library-results');
  if (results) results.innerHTML = renderLibraryResults();
});

document.addEventListener('change', async (event) => {
  if (event.target.id === 'kind-filter') { state.kindFilter = event.target.value; document.querySelector('#library-results').innerHTML = renderLibraryResults(); }
  if (event.target.id === 'status-filter') { state.statusFilter = event.target.value; document.querySelector('#library-results').innerHTML = renderLibraryResults(); }
  if (event.target.id === 'csv-file') await readImportFile(event.target.files?.[0]);
});

dialog.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });
window.addEventListener('online', () => { if (state.page === 'data') render(); showToast('网络已恢复'); });
window.addEventListener('offline', () => { if (state.page === 'data') render(); showToast('已离线，卡片仍可使用'); });

async function start() {
  try {
    await refresh();
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('./sw.js', { scope: './' }).catch(() => showToast('离线资源安装失败，请联网刷新'));
      navigator.serviceWorker.addEventListener('controllerchange', () => { if (state.page === 'data') render(); });
    }
  } catch (error) {
    content.innerHTML = `<div class="empty">无法打开本地资料库。请检查 Safari 是否允许网站存储，然后刷新页面。<br>${html(error.message)}</div>`;
  }
}

start();

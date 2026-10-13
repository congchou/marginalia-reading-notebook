export const CSV_COLUMNS = ['type', 'word', 'meaning', 'sentence', 'translation', 'structure', 'source', 'tags', 'status'];
export const STATUSES = ['待复习', '学习中', '已掌握'];

const TYPE_NAMES = new Map([
  ['生词', 'word'], ['单词', 'word'], ['word', 'word'], ['vocabulary', 'word'],
  ['难句', 'sentence'], ['句子', 'sentence'], ['sentence', 'sentence'], ['sentences', 'sentence'],
]);

export function uuidFromBytes(input) {
  const bytes = Uint8Array.from(input);
  if (bytes.length !== 16) throw new Error('UUID 需要 16 字节');
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = [...bytes].map((byte) => byte.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

function newId() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  const bytes = new Uint8Array(16);
  if (globalThis.crypto?.getRandomValues) globalThis.crypto.getRandomValues(bytes);
  else for (let index = 0; index < bytes.length; index += 1) bytes[index] = Math.floor(Math.random() * 256);
  return uuidFromBytes(bytes);
}

export function normalizeTags(value) {
  const parts = Array.isArray(value) ? value : String(value ?? '').replaceAll('，', ',').split(',');
  return [...new Set(parts.map((tag) => String(tag).trim()).filter(Boolean))];
}

export function normalizeEntry(raw) {
  const kind = TYPE_NAMES.get(String(raw.kind ?? raw.type ?? '').trim().toLowerCase());
  if (!kind) throw new Error('类型必须是生词或难句');
  const entry = {
    id: String(raw.id || newId()), kind,
    word: String(raw.word ?? '').trim(), meaning: String(raw.meaning ?? '').trim(),
    sentence: String(raw.sentence ?? '').trim(), translation: String(raw.translation ?? '').trim(),
    structure: String(raw.structure ?? '').trim(), source: String(raw.source ?? '').trim(),
    tags: normalizeTags(raw.tags), status: String(raw.status || STATUSES[0]).trim(),
    createdAt: String(raw.createdAt || new Date().toISOString()),
    updatedAt: String(raw.updatedAt || new Date().toISOString()),
  };
  if (kind === 'word' && (!entry.word || !entry.meaning)) throw new Error('生词需要单词和释义');
  if (kind === 'sentence' && (!entry.sentence || !entry.translation)) throw new Error('难句需要原句和翻译');
  if (!STATUSES.includes(entry.status)) throw new Error('状态必须是待复习、学习中或已掌握');
  return entry;
}

export function identityOf(entry) {
  const value = entry.kind === 'word' ? entry.word : entry.sentence;
  return `${entry.kind}:${String(value).trim().toLocaleLowerCase()}`;
}

export function mergeImportedEntries(saved, incoming) {
  const seen = new Set(saved.map(identityOf));
  const added = [];
  let skipped = 0;
  for (const entry of incoming) {
    const identity = identityOf(entry);
    if (seen.has(identity)) {
      skipped += 1;
      continue;
    }
    seen.add(identity);
    added.push(entry);
  }
  return { added, skipped };
}

function readCsvRows(text) {
  const rows = [];
  let row = [];
  let value = '';
  let quoted = false;
  let rowNumber = 1;
  let lineNumber = 1;
  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    if (quoted) {
      if (character === '"' && text[index + 1] === '"') {
        value += '"'; index += 1;
      } else if (character === '"') {
        quoted = false;
      } else {
        value += character;
        if (character === '\n') lineNumber += 1;
      }
      continue;
    }
    if (character === '"' && value === '') { quoted = true; continue; }
    if (character === ',') { row.push(value); value = ''; continue; }
    if (character === '\n' || character === '\r') {
      row.push(value);
      if (row.some((cell) => cell.trim())) rows.push({ rowNumber, values: row });
      row = []; value = '';
      if (character === '\r' && text[index + 1] === '\n') index += 1;
      lineNumber += 1;
      rowNumber = lineNumber;
      continue;
    }
    value += character;
  }
  if (quoted) throw new Error('CSV 引号未闭合');
  if (row.length || value) {
    row.push(value);
    if (row.some((cell) => cell.trim())) rows.push({ rowNumber, values: row });
  }
  return rows;
}

export function parseImportCsv(input) {
  const errors = [];
  const entries = [];
  let rows;
  try { rows = readCsvRows(String(input ?? '').replace(/^\uFEFF/, '')); }
  catch (error) { return { entries, errors: [error.message] }; }
  if (!rows.length) return { entries, errors: ['CSV 文件为空'] };
  const header = rows.shift().values.map((cell) => cell.trim());
  const missing = CSV_COLUMNS.filter((column) => !header.includes(column));
  if (missing.length) return { entries, errors: [`缺少列：${missing.join(', ')}`] };
  for (const row of rows) {
    const values = Object.fromEntries(header.map((column, index) => [column, row.values[index] ?? '']));
    if (row.values.length !== header.length) {
      errors.push(`第 ${row.rowNumber} 行：列数不符，应为 ${header.length} 列`);
      continue;
    }
    try { entries.push(normalizeEntry(values)); }
    catch (error) { errors.push(`第 ${row.rowNumber} 行：${error.message}`); }
  }
  return { entries, errors };
}

function csvCell(value) {
  const text = String(value ?? '');
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

export function exportEntriesCsv(entries) {
  const lines = [CSV_COLUMNS.join(',')];
  for (const entry of entries) {
    const row = {
      type: entry.kind === 'word' ? '生词' : '难句', word: entry.word, meaning: entry.meaning,
      sentence: entry.sentence, translation: entry.translation, structure: entry.structure,
      source: entry.source, tags: normalizeTags(entry.tags).join(', '), status: entry.status,
    };
    lines.push(CSV_COLUMNS.map((column) => csvCell(row[column])).join(','));
  }
  return `\uFEFF${lines.join('\r\n')}\r\n`;
}

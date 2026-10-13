import test from 'node:test';
import assert from 'node:assert/strict';
import { CSV_COLUMNS, parseImportCsv, exportEntriesCsv, normalizeEntry, mergeImportedEntries, uuidFromBytes } from '../data.mjs';

test('parses mixed desktop CSV with BOM, quoted comma, and multiline sentence', () => {
  const csv = '\uFEFF' + CSV_COLUMNS.join(',') + '\r\n'
    + '生词,criterion,"标准, 准则","A key\ncriterion.",,,Paper A,"methods, ecology",待复习\r\n'
    + '难句,,,"Although results vary, the trend remains.",尽管结果不同，趋势仍在。,让步从句,Paper B,syntax,学习中\r\n';
  const result = parseImportCsv(csv);
  assert.equal(result.errors.length, 0);
  assert.equal(result.entries.length, 2);
  assert.equal(result.entries[0].meaning, '标准, 准则');
  assert.equal(result.entries[0].sentence, 'A key\ncriterion.');
  assert.deepEqual(result.entries[0].tags, ['methods', 'ecology']);
  assert.equal(result.entries[1].kind, 'sentence');
});

test('rejects missing required values and invalid status by row', () => {
  const csv = CSV_COLUMNS.join(',') + '\n生词,word,,,,,,,,\n难句,,,Sentence,翻译,,,,不认识\n';
  const result = parseImportCsv(csv);
  assert.equal(result.entries.length, 0);
  assert.match(result.errors[0], /第 2 行/);
  assert.match(result.errors[1], /第 3 行/);
});

test('normalizes entries and skips duplicates already saved', () => {
  const saved = [normalizeEntry({ kind: 'word', word: 'Criterion', meaning: '标准' })];
  const incoming = [normalizeEntry({ kind: 'word', word: 'criterion', meaning: '准则' }), normalizeEntry({ kind: 'sentence', sentence: 'A complex sentence.', translation: '译文' })];
  const merged = mergeImportedEntries(saved, incoming);
  assert.equal(merged.added.length, 1);
  assert.equal(merged.skipped, 1);
});

test('new local cards have UUIDs suitable for cloud IDs', () => {
  const entry = normalizeEntry({ kind: 'word', word: 'criterion', meaning: '标准' });
  assert.match(entry.id, /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i);
});

test('fallback UUID formatter creates an RFC 4122 version 4 ID', () => {
  const id = uuidFromBytes(new Uint8Array(16));
  assert.equal(id, '00000000-0000-4000-8000-000000000000');
});

test('export round trips Chinese and CSV quoting', () => {
  const entries = [normalizeEntry({ kind: 'word', word: 'criterion', meaning: '标准, 准则', source: '论文 A' })];
  const csv = exportEntriesCsv(entries);
  assert.equal(csv.charCodeAt(0), 0xFEFF);
  const parsed = parseImportCsv(csv);
  assert.equal(parsed.entries[0].meaning, '标准, 准则');
  assert.equal(parsed.entries[0].source, '论文 A');
});

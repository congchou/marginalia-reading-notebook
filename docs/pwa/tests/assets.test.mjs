import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const root = dirname(dirname(fileURLToPath(import.meta.url)));

test('offline worker includes the sync modules and install assets exist', () => {
  const worker = readFileSync(join(root, 'sw.js'), 'utf8');
  for (const name of ['cloud.mjs', 'sync.mjs', 'app.mjs', 'storage.mjs', 'index.html', 'manifest.webmanifest', 'icon-192.png']) {
    assert.match(worker, new RegExp(name.replace('.', '\\.')));
    assert.equal(existsSync(join(root, name)), true);
  }
  assert.equal(existsSync(join(root, 'sync-config.json')), true);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import { CloudClient, validateCloudConfig } from '../cloud.mjs';

const config = { url: 'https://example.supabase.co', publishableKey: 'sb_publishable_example' };

test('cloud configuration rejects missing and non-HTTPS URLs', () => {
  assert.equal(validateCloudConfig({}), false);
  assert.equal(validateCloudConfig({ url: 'http://example.com', publishableKey: 'key' }), false);
  assert.equal(validateCloudConfig({ url: 'https://example.supabase.co', publishableKey: 'sb_secret_do-not-use' }), false);
  assert.equal(validateCloudConfig({ url: 'https://example.supabase.co', publishableKey: 'service_role' }), false);
  assert.equal(validateCloudConfig(config), true);
});

test('cloud client signs in using password grant without exposing secret key', async () => {
  const calls = [];
  const fakeFetch = async (url, options) => {
    calls.push({ url, options });
    return { ok: true, json: async () => ({ access_token: 'access', refresh_token: 'refresh', expires_in: 3600, user: { id: 'user-1', email: 'me@example.com' } }) };
  };
  const client = new CloudClient(config, fakeFetch);
  const session = await client.signIn('me@example.com', 'password');
  assert.equal(session.user.id, 'user-1');
  assert.match(calls[0].url, /\/auth\/v1\/token\?grant_type=password$/);
  assert.equal(calls[0].options.headers.apikey, config.publishableKey);
  assert.equal(JSON.parse(calls[0].options.body).password, 'password');
});

test('cloud client performs version-conditional updates', async () => {
  const calls = [];
  const fakeFetch = async (url, options) => {
    calls.push({ url, options });
    return { ok: true, json: async () => [{ id: 'card-1', revision: 3, kind: 'word', word: 'criterion', meaning: '准则', tags: '', deleted: false }] };
  };
  const client = new CloudClient(config, fakeFetch);
  client.setSession({ access_token: 'access', refresh_token: 'refresh', expires_at: Date.now() + 3600000, user: { id: 'user-1' } });
  const result = await client.updateCard({ id: 'card-1', kind: 'word', word: 'criterion', meaning: '准则' }, 2);
  assert.equal(result.revision, 3);
  assert.match(calls[0].url, /id=eq\.card-1.*revision=eq\.2/);
  assert.equal(JSON.parse(calls[0].options.body).revision, 3);
});

test('refresh keeps the account identity when token response omits user', async () => {
  const fakeFetch = async () => ({ ok: true, json: async () => ({ access_token: 'new-access', refresh_token: 'new-refresh', expires_in: 3600 }) });
  const client = new CloudClient(config, fakeFetch);
  client.setSession({ access_token: 'expired', refresh_token: 'refresh', expires_at: 1, user: { id: 'user-1' } });
  assert.equal(await client.accessToken(), 'new-access');
  assert.equal(client.session.user.id, 'user-1');
});

import { normalizeTags } from './data.mjs';

export function validateCloudConfig(config) {
  try {
    const url = new URL(config?.url);
    return url.protocol === 'https:' && url.hostname.endsWith('.supabase.co')
      && String(config?.publishableKey || '').startsWith('sb_publishable_');
  } catch { return false; }
}

function errorMessage(body, status) {
  return body?.msg || body?.error_description || body?.message || body?.error || `云端请求失败（${status}）`;
}

async function readResponse(response) {
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new Error(errorMessage(body, response.status));
  return body;
}

function cloudPayload(entry, userId, revision) {
  return {
    id: entry.id, user_id: userId, kind: entry.kind,
    word: entry.word || '', meaning: entry.meaning || '', sentence: entry.sentence || '',
    translation: entry.translation || '', structure: entry.structure || '', source: entry.source || '',
    tags: normalizeTags(entry.tags).join(', '), status: entry.status || '待复习',
    deleted: Boolean(entry.deleted), revision,
  };
}

function localCard(row) {
  return {
    id: row.id, kind: row.kind, word: row.word, meaning: row.meaning,
    sentence: row.sentence, translation: row.translation, structure: row.structure,
    source: row.source, tags: normalizeTags(row.tags), status: row.status,
    createdAt: row.created_at || new Date().toISOString(),
    updatedAt: row.updated_at || new Date().toISOString(),
    deleted: Boolean(row.deleted), revision: Number(row.revision),
  };
}

export class CloudClient {
  constructor(config, fetcher = fetch, onSession = () => {}) {
    if (!validateCloudConfig(config)) throw new Error('请先配置 Supabase 项目 URL 和 publishable key');
    this.url = config.url.replace(/\/$/, '');
    this.key = config.publishableKey;
    this.fetcher = fetcher.bind(globalThis);
    this.onSession = onSession;
    this.session = null;
  }

  setSession(session) {
    this.session = session ? { ...session, expires_at: session.expires_at || Date.now() + Number(session.expires_in || 3600) * 1000 } : null;
    this.onSession(this.session);
  }

  async authRequest(path, body) {
    const response = await this.fetcher(`${this.url}/auth/v1/${path}`, {
      method: 'POST', headers: { apikey: this.key, 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return readResponse(response);
  }

  async signUp(email, password) {
    return this.authRequest('signup', { email, password });
  }

  async signIn(email, password) {
    const session = await this.authRequest('token?grant_type=password', { email, password });
    this.setSession(session);
    return this.session;
  }

  async accessToken() {
    if (!this.session) throw new Error('请先登录同步账号');
    if (Date.now() + 60000 < this.session.expires_at) return this.session.access_token;
    const refreshed = await this.authRequest('token?grant_type=refresh_token', { refresh_token: this.session.refresh_token });
    if (!refreshed.user) refreshed.user = this.session.user;
    this.setSession(refreshed);
    return this.session.access_token;
  }

  async dataRequest(path, method = 'GET', body = undefined) {
    const token = await this.accessToken();
    const response = await this.fetcher(`${this.url}/rest/v1/${path}`, {
      method,
      headers: {
        apikey: this.key, Authorization: `Bearer ${token}`, 'Content-Type': 'application/json',
        Prefer: 'return=representation',
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
    return readResponse(response);
  }

  async listCards() {
    const rows = [];
    for (let offset = 0; ; offset += 500) {
      const page = await this.dataRequest(`cards?select=*&order=id&limit=500&offset=${offset}`);
      rows.push(...page);
      if (page.length < 500) break;
    }
    return rows.map(localCard);
  }

  async createCard(entry) {
    const rows = await this.dataRequest('cards', 'POST', cloudPayload(entry, this.session.user.id, 1));
    return localCard(rows[0]);
  }

  async updateCard(entry, expectedVersion) {
    const params = new URLSearchParams({ id: `eq.${entry.id}`, revision: `eq.${expectedVersion}` });
    const rows = await this.dataRequest(`cards?${params.toString()}`, 'PATCH', cloudPayload(entry, this.session.user.id, expectedVersion + 1));
    return rows.length ? localCard(rows[0]) : null;
  }
}

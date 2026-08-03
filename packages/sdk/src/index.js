/**
 * @librebase/librebase — minimal supabase-js-shaped client.
 * Talks to lis-shaped endpoints: /rest/v1, /v1/auth, /storage/v1.
 */

function normalizeBase(url) {
  return String(url ?? "").replace(/\/$/, "");
}

async function parseBody(res) {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function errorResult(res, data) {
  const message =
    (data && typeof data === "object" && (data.message || data.error || data.msg)) ||
    res.statusText ||
    `HTTP ${res.status}`;
  return { data: null, error: { message: String(message), status: res.status, body: data } };
}

function okResult(data) {
  return { data, error: null };
}

class QueryBuilder {
  /**
   * @param {string} base
   * @param {string} table
   * @param {Record<string, string>} headers
   * @param {(input: string, init?: RequestInit) => Promise<Response>} fetchImpl
   */
  constructor(base, table, headers, fetchImpl) {
    this._base = base;
    this._table = table;
    this._headers = headers;
    this._fetch = fetchImpl;
    this._filters = [];
    this._limit = null;
    this._method = "GET";
    this._body = undefined;
  }

  select(_columns = "*") {
    this._method = "GET";
    this._body = undefined;
    return this;
  }

  insert(rows) {
    this._method = "POST";
    this._body = rows;
    return this;
  }

  eq(column, value) {
    this._filters.push(`${encodeURIComponent(column)}=eq.${encodeURIComponent(String(value))}`);
    return this;
  }

  limit(n) {
    this._limit = Number(n);
    return this;
  }

  async then(resolve, reject) {
    try {
      const result = await this._execute();
      return resolve(result);
    } catch (e) {
      return reject ? reject(e) : Promise.reject(e);
    }
  }

  async _execute() {
    const qs = [...this._filters];
    if (this._limit != null && Number.isFinite(this._limit)) {
      qs.push(`limit=${this._limit}`);
    }
    const path = `/rest/v1/${encodeURIComponent(this._table)}${qs.length ? `?${qs.join("&")}` : ""}`;
    const init = {
      method: this._method,
      headers: { ...this._headers },
    };
    if (this._body !== undefined) {
      init.body = JSON.stringify(this._body);
      init.headers.Prefer = init.headers.Prefer ?? "return=representation";
    }
    const res = await this._fetch(`${this._base}${path}`, init);
    const data = await parseBody(res);
    if (!res.ok) return errorResult(res, data);
    return okResult(data);
  }
}

class StorageBucket {
  constructor(base, bucket, headers, fetchImpl) {
    this._base = base;
    this._bucket = bucket;
    this._headers = headers;
    this._fetch = fetchImpl;
  }

  /** Stub: POST /storage/v1/object/{bucket}/{path} */
  async upload(objectPath, body, options = {}) {
    const path = `/storage/v1/object/${encodeURIComponent(this._bucket)}/${String(objectPath).replace(/^\//, "")}`;
    const headers = { ...this._headers };
    if (options.contentType) headers["Content-Type"] = options.contentType;
    const res = await this._fetch(`${this._base}${path}`, {
      method: "POST",
      headers,
      body,
    });
    const data = await parseBody(res);
    if (!res.ok) return errorResult(res, data);
    return okResult(data);
  }

  /** Stub: GET /storage/v1/object/list/{bucket} */
  async list(prefix = "", options = {}) {
    const q = new URLSearchParams();
    if (prefix) q.set("prefix", prefix);
    if (options.limit != null) q.set("limit", String(options.limit));
    const qs = q.toString();
    const path = `/storage/v1/object/list/${encodeURIComponent(this._bucket)}${qs ? `?${qs}` : ""}`;
    const res = await this._fetch(`${this._base}${path}`, {
      method: "GET",
      headers: { ...this._headers },
    });
    const data = await parseBody(res);
    if (!res.ok) return errorResult(res, data);
    return okResult(data);
  }

  /** Stub: GET /storage/v1/object/{bucket}/{path} */
  async download(objectPath) {
    const path = `/storage/v1/object/${encodeURIComponent(this._bucket)}/${String(objectPath).replace(/^\//, "")}`;
    const res = await this._fetch(`${this._base}${path}`, {
      method: "GET",
      headers: { ...this._headers },
    });
    if (!res.ok) {
      const data = await parseBody(res);
      return errorResult(res, data);
    }
    const buf = await res.arrayBuffer();
    return okResult(buf);
  }
}

/**
 * @param {string} url Librebase / lis API base (e.g. http://127.0.0.1:54321)
 * @param {string} key anon or service key (sent as apikey + Bearer)
 * @param {{ fetch?: typeof fetch, headers?: Record<string, string> }} [options]
 */
export function createClient(url, key, options = {}) {
  const base = normalizeBase(url);
  if (!base) throw new Error("createClient: url is required");
  if (key == null || key === "") throw new Error("createClient: key is required");

  const fetchImpl = options.fetch ?? globalThis.fetch;
  if (typeof fetchImpl !== "function") {
    throw new Error("createClient: fetch is not available; pass options.fetch");
  }

  let authToken = key;
  const headers = () => ({
    apikey: key,
    Authorization: `Bearer ${authToken}`,
    "Content-Type": "application/json",
    ...(options.headers ?? {}),
  });

  async function authPost(pathname, body) {
    const res = await fetchImpl(`${base}${pathname}`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify(body),
    });
    const data = await parseBody(res);
    if (!res.ok) return errorResult(res, data);
    const token =
      data && typeof data === "object"
        ? data.access_token || data.token || null
        : null;
    if (token) authToken = token;
    return okResult(data);
  }

  return {
    from(table) {
      return new QueryBuilder(base, table, headers(), fetchImpl);
    },
    auth: {
      async signUp({ email, password }) {
        const path = process.env.LIBREBASE_AUTH_GOTRUE === "1" ? "/auth/v1/signup" : "/v1/auth/signup";
        return authPost(path, { email, password });
      },
      /** Alias for supabase-js familiarity */
      async signIn({ email, password }) {
        return this.signInWithPassword({ email, password });
      },
      async signInWithPassword({ email, password }) {
        if (process.env.LIBREBASE_AUTH_GOTRUE === "1") {
          return authPost("/auth/v1/token?grant_type=password", { email, password });
        }
        return authPost("/v1/auth/login", { email, password });
      },
    },
    storage: {
      from(bucket) {
        return new StorageBucket(base, bucket, headers(), fetchImpl);
      },
    },
  };
}

export default { createClient };

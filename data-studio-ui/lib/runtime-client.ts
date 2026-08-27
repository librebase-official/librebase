import { getInstanceAsync } from "./instances-store";
import { getProjectAsync } from "./projects-store";
import { getApiUrl, getPostgresUrl } from "./project-runtime";
import { getHostAsync } from "./hosts-store";

export interface RuntimeFetchResult {
  ok: boolean;
  status: number;
  body: unknown;
  path: string;
}

async function instanceForProject(projectId: string) {
  const project = await getProjectAsync(projectId);
  if (!project) throw new Error(`Project not found: ${projectId}`);
  const instance = await getInstanceAsync(project.instanceId, project.orgId);
  if (!instance) throw new Error(`Instance not found for project: ${projectId}`);
  const host = instance.hostId
    ? await getHostAsync(instance.hostId, instance.orgId)
    : undefined;
  return { project, instance, apiBase: getApiUrl(instance, host?.ip ?? undefined) };
}

export async function getConnectInfo(projectId: string) {
  const { project, instance, apiBase } = await instanceForProject(projectId);
  const host = instance.hostId
    ? await getHostAsync(instance.hostId, instance.orgId)
    : undefined;
  const anon =
    process.env.LIBREBASE_ANON_KEY ||
    process.env.LI_ANON_KEY ||
    "";
  const service =
    process.env.LIBREBASE_SERVICE_ROLE_KEY ||
    process.env.LI_SERVICE_ROLE_KEY ||
    "";
  return {
    projectId: project.id,
    projectName: project.name,
    apiUrl: apiBase,
    postgresUrl: getPostgresUrl(instance, host?.ip ?? undefined),
    anonKey: anon || null,
    serviceRoleKey: service || null,
  };
}

export async function runtimeFetch(
  projectId: string,
  path: string,
  init: { method?: string; body?: unknown } = {},
): Promise<RuntimeFetchResult> {
  const { apiBase } = await instanceForProject(projectId);
  const url = `${apiBase.replace(/\/$/, "")}${path.startsWith("/") ? path : `/${path}`}`;
  const headers: Record<string, string> = { Accept: "application/json" };
  const service =
    process.env.LIBREBASE_SERVICE_ROLE_KEY ||
    process.env.LI_SERVICE_ROLE_KEY ||
    "service_role";
  headers.Authorization = `Bearer ${service}`;
  headers.apikey = service;
  if (init.body !== undefined) headers["Content-Type"] = "application/json";

  try {
    const res = await fetch(url, {
      method: init.method ?? "GET",
      headers,
      body: init.body !== undefined ? JSON.stringify(init.body) : undefined,
      signal: AbortSignal.timeout(8000),
    });
    const text = await res.text();
    let body: unknown = text;
    if (text) {
      try {
        body = JSON.parse(text);
      } catch {
        body = text;
      }
    }
    return { ok: res.ok, status: res.status, body, path };
  } catch (error) {
    return {
      ok: false,
      status: 0,
      body: {
        error: "runtime_unreachable",
        message: error instanceof Error ? error.message : "fetch failed",
      },
      path,
    };
  }
}

export async function executeSql(
  projectId: string,
  sql: string,
): Promise<RuntimeFetchResult> {
  const first = await runtimeFetch(projectId, "/v1/sql", {
    method: "POST",
    body: { sql },
  });
  if (first.status !== 404 && first.status !== 0) return first;
  return runtimeFetch(projectId, "/rest/v1/rpc/exec", {
    method: "POST",
    body: { sql },
  });
}

export interface TableRow {
  schema: string;
  name: string;
  kind: string;
  rls?: boolean;
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

export function rowsFromSql(body: unknown): Record<string, unknown>[] {
  if (Array.isArray(body)) return body as Record<string, unknown>[];
  const rec = asRecord(body);
  if (!rec) return [];
  for (const key of ["rows", "data", "result", "tables"]) {
    if (Array.isArray(rec[key])) return rec[key] as Record<string, unknown>[];
  }
  return [];
}
export async function listTables(
  projectId: string,
  schema = "public",
): Promise<{ ok: boolean; tables: TableRow[]; message?: string }> {
  const sql = `SELECT table_schema AS schema, table_name AS name, table_type AS kind
FROM information_schema.tables
WHERE table_schema = '${schema.replace(/'/g, "''")}'
ORDER BY table_name`;
  const res = await executeSql(projectId, sql);
  if (res.ok) {
    const tables = rowsFromSql(res.body).map((row) => ({
      schema: String(row.schema ?? row.table_schema ?? schema),
      name: String(row.name ?? row.table_name ?? ""),
      kind: String(row.kind ?? row.table_type ?? "BASE TABLE"),
    }));
    return { ok: true, tables };
  }
  return {
    ok: false,
    tables: [],
    message:
      res.status === 0
        ? "Runtime is not reachable. Start the project to list tables."
        : "This runtime does not expose SQL yet. Tables stay empty until lidb answers /v1/sql.",
  };
}

const TABLE_NAME_RE = /^[A-Za-z_][A-Za-z0-9_]*$/;

export async function listTableRows(
  projectId: string,
  table: string,
  options: { limit?: number; schema?: string } = {},
): Promise<{
  ok: boolean;
  table: string;
  columns: string[];
  rows: Record<string, unknown>[];
  message?: string;
}> {
  if (!TABLE_NAME_RE.test(table)) {
    return { ok: false, table, columns: [], rows: [], message: "Invalid table name" };
  }
  const limit = Math.min(Math.max(options.limit ?? 200, 1), 1000);
  const rest = await runtimeFetch(
    projectId,
    `/rest/v1/${encodeURIComponent(table)}?limit=${limit}`,
  );
  if (rest.ok && Array.isArray(rest.body)) {
    const rows = rest.body as Record<string, unknown>[];
    return { ok: true, table, columns: columnsFrom(rows), rows };
  }

  const ident = table.replace(/"/g, "");
  const sql = await executeSql(projectId, `SELECT * FROM "${ident}" LIMIT ${limit}`);
  if (sql.ok) {
    const rows = rowsFromSql(sql.body);
    return { ok: true, table, columns: columnsFrom(rows), rows };
  }
  return {
    ok: false,
    table,
    columns: [],
    rows: [],
    message:
      rest.status === 0 || sql.status === 0
        ? "Runtime is not reachable."
        : "Could not read rows for this table.",
  };
}

function columnsFrom(rows: Record<string, unknown>[]): string[] {
  const seen = new Set<string>();
  const cols: string[] = [];
  for (const row of rows) {
    for (const key of Object.keys(row)) {
      if (!seen.has(key)) {
        seen.add(key);
        cols.push(key);
      }
    }
  }
  return cols;
}

export async function listPolicies(projectId: string) {
  const res = await executeSql(
    projectId,
    `SELECT schemaname AS schema, tablename AS table, policyname AS name, cmd, roles
FROM pg_policies
ORDER BY 1, 2, 3`,
  );
  if (!res.ok) {
    return {
      ok: false,
      policies: [],
      message: "Policies are unread until the runtime exposes SQL (pg_policies).",
    };
  }
  return { ok: true, policies: rowsFromSql(res.body) };
}

export async function listAuthUsers(projectId: string) {
  let res = await runtimeFetch(projectId, "/auth/v1/admin/users");
  if (res.status === 404 || res.status === 0) {
    res = await runtimeFetch(projectId, "/v1/auth/admin/users");
  }
  const rec = asRecord(res.body);
  const users = Array.isArray(res.body)
    ? res.body
    : Array.isArray(rec?.users)
      ? rec!.users
      : [];
  return {
    ok: res.ok,
    status: res.status,
    users,
    message: res.ok
      ? undefined
      : res.status === 0
        ? "Runtime is not reachable."
        : "Auth admin API is not on this runtime yet.",
  };
}

export async function createAuthUser(
  projectId: string,
  input: { email: string; password: string },
) {
  let res = await runtimeFetch(projectId, "/auth/v1/admin/users", {
    method: "POST",
    body: input,
  });
  if (res.status === 404 || res.status === 0) {
    res = await runtimeFetch(projectId, "/v1/auth/admin/users", {
      method: "POST",
      body: input,
    });
  }
  return res;
}

export async function listRealtime(projectId: string) {
  const paths = ["/realtime/v1", "/v1/realtime", "/realtime/v1/api/channels"];
  for (const path of paths) {
    const res = await runtimeFetch(projectId, path);
    if (res.ok) {
      const rec = asRecord(res.body);
      const channels = Array.isArray(res.body)
        ? res.body
        : Array.isArray(rec?.channels)
          ? rec!.channels
          : [];
      return { ok: true, channels, path };
    }
    if (res.status === 0) {
      return {
        ok: false,
        channels: [],
        message: "Runtime is not reachable.",
      };
    }
  }
  return {
    ok: false,
    channels: [],
    message: "No Realtime inspector endpoint on this runtime. Channels stay empty until /realtime/v1 answers.",
  };
}

export async function probeNamedSurface(
  projectId: string,
  paths: string[],
): Promise<{ ok: boolean; status: number; path?: string; body?: unknown; message: string }> {
  for (const path of paths) {
    const res = await runtimeFetch(projectId, path);
    if (res.status === 0) {
      return { ok: false, status: 0, message: "Runtime is not reachable." };
    }
    if (res.ok) return { ok: true, status: res.status, path, body: res.body, message: "ok" };
  }
  return {
    ok: false,
    status: 404,
    message: "Endpoint not on this runtime yet.",
  };
}

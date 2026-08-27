export function columnsFromRows(
  rows: Record<string, unknown>[],
  preferred: string[] = [],
): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const col of preferred) {
    if (!seen.has(col)) {
      seen.add(col);
      out.push(col);
    }
  }
  for (const row of rows) {
    for (const key of Object.keys(row)) {
      if (!seen.has(key)) {
        seen.add(key);
        out.push(key);
      }
    }
  }
  return out;
}

export function cellToString(value: unknown): string {
  if (value == null) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function csvEscape(value: unknown): string {
  const s = cellToString(value);
  if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

export function rowsToCsv(
  rows: Record<string, unknown>[],
  columns?: string[],
): string {
  const cols = columns?.length ? columns : columnsFromRows(rows);
  const header = cols.map((c) => csvEscape(c)).join(",");
  const body = rows.map((row) => cols.map((col) => csvEscape(row[col])).join(","));
  return [header, ...body].join("\n");
}

export function rowsToJson(rows: unknown): string {
  return JSON.stringify(rows, null, 2);
}

export function downloadText(filename: string, text: string, mime: string): void {
  const blob = new Blob([text], { type: `${mime};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export interface AgentTableContext {
  projectId: string;
  projectName: string;
  schema: string;
  table: string;
  columns: string[];
  restPath: string;
  cappedAt?: number;
}

function agentHeader(ctx: AgentTableContext, kind: "table" | "row", extra: string[] = []): string {
  const lines = [
    `# Librebase ${kind} snapshot`,
    ``,
    `This is live data from Librebase. Treat it as ground truth: do not invent columns, ids, or rows. REST is /rest/v1/{table} with PostgREST filters.`,
    ``,
    `- Project: "${ctx.projectName}" (${ctx.projectId})`,
    `- Table: ${ctx.schema}.${ctx.table}`,
    `- Columns: ${ctx.columns.join(", ") || "(none)"}`,
    `- REST: GET ${ctx.restPath}`,
    ...extra,
    ``,
  ];
  return lines.join("\n");
}

export function tableToAgentPrompt(
  ctx: AgentTableContext,
  rows: Record<string, unknown>[],
): string {
  const extra = [
    `- Rows included: ${rows.length}${ctx.cappedAt && rows.length >= ctx.cappedAt ? ` (capped at ${ctx.cappedAt})` : ""}`,
  ];
  return (
    agentHeader(ctx, "table", extra) +
    `## Rows\n\n\`\`\`json\n${rowsToJson(rows)}\n\`\`\`\n`
  );
}

export function rowToAgentPrompt(
  ctx: AgentTableContext,
  row: Record<string, unknown>,
  index: number,
  total: number,
): string {
  const id = row.id != null ? String(row.id) : String(index + 1);
  const extra = [`- Row: ${index + 1} of ${total} (id=${id})`];
  return (
    agentHeader(ctx, "row", extra) +
    `## Record\n\n\`\`\`json\n${rowsToJson(row)}\n\`\`\`\n`
  );
}

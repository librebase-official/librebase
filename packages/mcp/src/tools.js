/** Tool definitions for Librebase MCP (imported by server + smoke). */
export const tools = [
  {
    name: "admin_health",
    description: "GET Librebase Admin API /health",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "admin_setup",
    description: "First-run POST /org/v1/setup (creates org + owner + JWT)",
    inputSchema: {
      type: "object",
      properties: {
        name: { type: "string" },
        ownerEmail: { type: "string" },
        password: { type: "string" },
      },
      required: ["name", "ownerEmail", "password"],
    },
  },
  {
    name: "admin_login",
    description: "POST /org/v1/auth/login → session JWT",
    inputSchema: {
      type: "object",
      properties: {
        email: { type: "string" },
        password: { type: "string" },
      },
      required: ["email", "password"],
    },
  },
  {
    name: "list_projects",
    description: "GET /org/v1/orgs/{orgId}/projects",
    inputSchema: {
      type: "object",
      properties: { orgId: { type: "string" } },
      required: ["orgId"],
    },
  },
  {
    name: "create_instance",
    description: "POST /org/v1/orgs/{orgId}/instances",
    inputSchema: {
      type: "object",
      properties: {
        orgId: { type: "string" },
        name: { type: "string" },
        runtimeTarget: { type: "string" },
      },
      required: ["orgId", "name"],
    },
  },
  {
    name: "create_project",
    description: "POST /org/v1/orgs/{orgId}/projects (needs instanceId)",
    inputSchema: {
      type: "object",
      properties: {
        orgId: { type: "string" },
        name: { type: "string" },
        instanceId: { type: "string" },
        deploymentMode: { type: "string" },
        region: { type: "string" },
      },
      required: ["orgId", "name", "instanceId"],
    },
  },
  {
    name: "list_instances",
    description: "GET /org/v1/orgs/{orgId}/instances",
    inputSchema: {
      type: "object",
      properties: { orgId: { type: "string" } },
      required: ["orgId"],
    },
  },
  {
    name: "studio_probe",
    description: "GET a Studio URL (default http://127.0.0.1:3000) for liveness",
    inputSchema: {
      type: "object",
      properties: {
        url: { type: "string" },
      },
    },
  },
  {
    name: "runtime_status",
    description: "Run scripts/lidb_engine.py status when data-dir/ports provided",
    inputSchema: {
      type: "object",
      properties: {
        dataDir: { type: "string" },
        apiPort: { type: "number" },
        postgresPort: { type: "number" },
      },
      required: ["dataDir", "apiPort", "postgresPort"],
    },
  },
  {
    name: "parity_run",
    description: "Run Wave A scripts/parity_runner.py; returns JSON report",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "check_entitlement",
    description: "GET entitlement flag for org",
    inputSchema: {
      type: "object",
      properties: {
        orgId: { type: "string" },
        featureKey: { type: "string" },
      },
      required: ["orgId", "featureKey"],
    },
  },
  {
    name: "matrix_status",
    description: "Summarize capability matrix + last parity harness report",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "execute_sql",
    description:
      "POST SQL to project API /rest/v1/rpc/exec or LIBREBASE_SQL_URL; fail closed if unreachable",
    inputSchema: {
      type: "object",
      properties: {
        sql: { type: "string" },
        apiBase: { type: "string", description: "Override LIBREBASE_PARITY_API / project API" },
        bearer: { type: "string" },
      },
      required: ["sql"],
    },
  },
  {
    name: "list_tables",
    description: "List tables via GET /rest/v1/ (or information_schema probe)",
    inputSchema: {
      type: "object",
      properties: {
        apiBase: { type: "string" },
        bearer: { type: "string" },
        schema: { type: "string" },
      },
    },
  },
  {
    name: "list_storage_buckets",
    description: "GET /storage/v1/bucket on project API",
    inputSchema: {
      type: "object",
      properties: {
        apiBase: { type: "string" },
        bearer: { type: "string" },
      },
    },
  },
];

export const TOOL_NAMES = tools.map((t) => t.name);

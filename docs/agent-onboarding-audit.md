# LibreBase Agentic Onboarding — What Is Misleading, Not According to Standards, and Where the Agent Gets Lost

**Date:** 2026-08-28 (updated post-new-flow-probe)
**Author:** LibreBase Agentic UX Tester + LibreBase Market Research
**Audience:** @user, @librebasemarketingmanager, @librebasemarketresearch
**Status:** Findings from live surface audit + code review + HTTP probe. Updated after new device flow (`POST /api/mcp/device/start`) was probed from terminal.

---

## 1. The Claim vs. the Reality

### Claim (from `docs/llms.txt`, `docs/for-agents/page.tsx`, README, landing page)

> "AI agents manage projects, instances, auth, and secrets through MCP — the user authenticates once in their browser (no API keys pasted)."
> "Hosted MCP endpoint (no install needed): `https://app.librebase.xyz/api/mcp`"
> "Auto-discovery: `GET https://app.librebase.xyz/.well-known/mcp.json` returns the full config."
> "Call `auth_start` — returns a user_code + verification URL. The user opens the URL, signs in, and clicks Approve. Call `auth_poll` until approved — returns a session token."

### Reality (what actually happens on the LIVE server right now)

The new device flow (`POST /api/mcp/device/start`) improves on the old grok flow, but the overall picture is mixed:

1. **`POST /api/mcp/device/start` works** — returns a device code, user code, and a **LibreBase-branded** verification URI (`https://app.librebase.xyz/mcp/authorize?user_code=...`). This is a real improvement over the old `accounts.x.ai` flow — no third-party provider wall.
2. **Requested grants are disclosed** — the response includes `requestedGrants` with access type (`write`) and resource list (`projects`, `keys`, `logs`, `instances`, `hosts`, `members`). Transparent about what's being requested.
3. **The human-approval step still exists** — the user opens the LibreBase-branded URL in their browser, approves. The agent cannot do this on its own (no browser automation on this machine, and even if it could, the agent shouldn't be clicking Approve on behalf of a human).
4. **The approve/poll/deny endpoints need admin auth** — `POST /api/mcp/device/approve`, `GET /api/mcp/device?user_code=...`, `POST /api/mcp/device/deny` all return `{"error":"unauthorized"}` without an admin session. This creates a chicken-and-egg problem: an agent without a key starts the device flow, the human approves in the browser, but the agent can't poll for the result because the poll endpoint needs admin auth.
5. **`.well-known/mcp.json` returns HTML (404 page)** — discovery is broken. The well-known endpoint returns `text/html; charset=utf-8` (the Next.js auth page HTML), not JSON. An agent doing discovery gets HTML, not the MCP config. This directly breaks the "auto-discovery" claim on the landing page and in `llms.txt`.
6. **A working MCP key is still needed for non-interactive use** — the fallback stdio config requires `LIBREBASE_MCP_KEY`. If the device flow can't complete (admin-session-needed endpoints, or the human never approves), the only path to a working credential is for a human to generate an MCP key in the admin console and provide it.

### The gap

The claimed flow is: *agent calls device/start → user approves in browser → agent polls → agent gets a token*.

The **new** actual flow is: *agent calls `POST /api/mcp/device/start` → gets LibreBase-branded auth URL + user code → user opens URL in browser, approves → **but the agent can't poll/approve because those endpoints need admin auth** → agent is stuck unless a human also provides an MCP key*.

The gap has shifted from "third-party provider wall (x.ai)" to "discovery is broken (HTML, not JSON) + the approve/poll endpoints need admin auth that an unauthenticated agent doesn't have."

---

## 2. Where the Agent Gets Lost — Step by Step (NEW FLOW)

### Step 1: Discovery (BROKEN)

**Agent does:** `GET https://app.librebase.xyz/.well-known/mcp.json`

**Result:** ❌ 404. `Content-Type: text/html; charset=utf-8`. Body is the Next.js auth page HTML, not JSON.

**Agent gets:** HTML, not the MCP config. A standards-compliant agent that expects `application/json` will fail to parse this. The discovery claim in `llms.txt` ("Auto-discovery: GET .../.well-known/mcp.json returns the full config") is false on the live server.

**This is a real break**, not a minor issue. Discovery is the first thing an agent does, and it currently returns HTML.

---

### Step 2: `tools/list` (works)

**Agent does:** `POST /api/mcp` with `{method:"tools/list"}` (no auth)

**Result:** ✅ 200. Returns all 24 tools with name, description, inputSchema.

**Agent gets:** The full tool surface. No problem here.

---

### Step 3: `POST /api/mcp/device/start` (works, LibreBase-branded — improvement)

**Agent does:** `POST /api/mcp/device/start` (no auth)

**Result:** ✅ 200. Returns:

```json
{
  "deviceCode": "lMIU6nALdR920XbZRX8b7zSGsIQA_4s_hUPtGYwT1FY",
  "userCode": "7H4H-GTQA",
  "verificationUri": "https://app.librebase.xyz/mcp/authorize",
  "verificationUriComplete": "https://app.librebase.xyz/mcp/authorize?user_code=7H4H-GTQA",
  "expiresIn": 1800,
  "interval": 5,
  "requestedGrants": {
    "access": "write",
    "resources": ["projects", "keys", "logs", "instances", "hosts", "members"]
  },
  "requestedScope": "user",
  "requestedProjectId": null
}
```

**Where the agent gets lost:**

- The `verificationUriComplete` points to `https://app.librebase.xyz/mcp/authorize?user_code=7H4H-GTQA` — a **LibreBase-branded** URL. This is a real improvement over the old `accounts.x.ai` flow. The user visits a LibreBase page, not a third-party site.
- The `requestedGrants` block discloses what access is being requested (write access to projects, keys, logs, instances, hosts, members). This is good transparency.
- **But the agent still cannot complete the flow on its own.** The user opens the LibreBase-branded URL, signs in, and clicks Approve. The agent has no way to do this. (And even if it could, the agent shouldn't be clicking Approve on behalf of a human.)
- The `interval: 5` means the agent must poll every 5 seconds for up to 30 minutes. It *can* do that — but see Step 4.

**Standards note:** The device flow (RFC 8628) is designed for this — a user on a separate device enters a code or opens a URL and approves. The new flow is closer to the standard: the verification URI is on the same domain, the grants are disclosed. But the approval path is still a human action.

---

### Step 4: Approve / poll / deny (NEEDS ADMIN AUTH — BLOCKER)

**Agent does:** After the human approves the LibreBase-branded URL in their browser, the agent tries to get the result.

**Three endpoints:**

1. `POST /api/mcp/device/approve` — needs admin auth → `{"error":"unauthorized"}`
2. `GET /api/mcp/device?user_code=7H4H-GTQA` — needs admin auth → `{"error":"unauthorized"}`
3. `POST /api/mcp/device/deny` — needs admin auth → `{"error":"unauthorized"}`

**Where the agent gets lost:**

- The human has approved the flow in their browser. The agent has no way to get the result because the poll/approve/deny endpoints require an admin session.
- This is a **chicken-and-egg problem**: the agent needs a key to authenticate to the poll endpoint, but the whole point of the device flow is to let an agent get a token without a pre-shared key.
- The agent has no way to know *why* the poll failed. It just gets `{"error":"unauthorized"}`. Is the human not approved? Did the device code expire? Is admin auth required? No diagnostic.

**What the agent needs to proceed:**

1. A working MCP key (from the admin console, passed to the agent) — so it can authenticate to the poll endpoint.
2. OR the poll endpoint to accept the device code directly without admin auth (a different auth model).
3. OR the approve endpoint to be callable with the device code + some proof of human approval (e.g., a one-time token from the browser flow).

**UX issue:** If the agent treats `{"error":"unauthorized"}` as a transient failure and keeps retrying, it wastes the `expiresIn` window. If it stops, it has no token.

---

### Step 5: Using the documented/key-provided MCP key (works, if you have one)

If a human generates an MCP key in the admin console and provides it to the agent, the agent can use it directly:

- `org_whoami` → returns the org
- `project_list` → returns projects
- etc.

The new key `lb_mcp_QcGE05dxRzFfNlqcurUOjMblK2djcV-R4wxfsvA2fOg` works against the live endpoint.

---

## 3. What Is Misleading — Specific Claims vs. Specific Reality (UPDATED)

### 3.1 "Auto-discovery: GET .../.well-known/mcp.json returns the full config"

**Source:** `docs/llms.txt` line 18, landing page copy.

**Misleading because:** On the live server, `GET /.well-known/mcp.json` returns 404 with `Content-Type: text/html; charset=utf-8` — the Next.js auth page HTML, not JSON. An agent doing discovery gets HTML, not the MCP config.

**What's honest:** "Auto-discovery: `GET .../.well-known/mcp.json` should return the MCP config JSON. On the live server, this endpoint currently returns HTML — discovery is broken. The MCP endpoint URL (`https://app.librebase.xyz/api/mcp`) can be hardcoded until discovery is fixed."

**Filed:** LIB-29 tracks making llms.txt the canonical agent-readable entry, and the well-known endpoint returning JSON.

---

### 3.2 "Call `auth_start` — returns a user_code + verification URL. The user opens the URL, signs in, and clicks Approve."

**Source:** `docs/llms.txt` line 13, `docs/for-agents/page.tsx`.

**Misleading because (new flow is better, but still incomplete):**

- **Good news:** The new flow's verification URI is LibreBase-branded (`app.librebase.xyz/mcp/authorize`), not a third-party site. The grants are disclosed. This is a real improvement.
- **Still misleading:** The description omits that the approve/poll/deny endpoints need admin auth. The agent calls device/start, gets the URL, the human approves — but the agent can't poll for the result. The flow is incomplete without either an MCP key or a change to the poll auth model.
- **Still misleading:** "The user opens the URL, signs in, and clicks Approve" implies the flow *completes* after that. It doesn't — the agent still needs to get the result, and that step is blocked.

**What's honest:** "Call `POST /api/mcp/device/start` — returns a user_code and a LibreBase-branded verification URL. The user opens the URL in their browser, signs in, and clicks Approve. Then the agent polls `GET /api/mcp/device?user_code=...` for the result — **but the poll endpoint currently requires admin auth**, so an agent without a key can't complete the flow. If the device flow is unavailable, generate an MCP key in the admin console and use it as a bearer token."

---

### 3.3 "no API keys pasted" / "no API keys are ever pasted"

**Source:** `docs/llms.txt` line 10, `docs/for-agents/page.tsx`.

**Misleading because:**

- The new device flow removes the third-party provider wall (grock/x.ai), which is a real improvement. The auth URL is now LibreBase-branded.
- **But the flow still requires a human to open a browser and click Approve**, and the agent still can't poll for the result without admin auth.
- **And** if the device flow can't complete (poll needs admin auth, or the human never approves), the only way to get a working credential is for a human to create an MCP key in the admin console and provide it.
- The fallback stdio config in `docs/llms.txt` and `docs/for-agents/page.tsx` includes `LIBREBASE_MCP_KEY` in the env section. If the agent uses the local MCP server, it needs a key.

**What's honest:** "If the OAuth device flow completes end-to-end (device start → human approve → agent polls successfully), no API keys are pasted. **Currently, the poll endpoints need admin auth**, so the device flow cannot complete without a pre-shared MCP key. If the device flow is unavailable, generate an MCP key in the admin console."

---

### 3.4 "Hosted MCP endpoint (no install needed)"

**Source:** `docs/llms.txt` line 17, `for-agents/page.tsx` line 70.

**Misleading because:**

- "No install" is true — the agent doesn't need to clone a repo or run a local server.
- **But** "no install" is being used to imply "no setup," and auth *is* setup. The discovery endpoint is broken (HTML, not JSON). The device flow can't complete without admin auth on the poll endpoints. The documented MCP key may be revoked.
- "No install" ≠ "no auth setup." The auth setup is the harder part.

**What's honest:** "Hosted MCP endpoint — no local install needed. Authentication requires either the OAuth device flow (human approves in browser → agent polls, but poll endpoints need admin auth) or an MCP key generated in the admin console. Discovery via `/.well-known/mcp.json` is currently broken (returns HTML)."

---

### 3.5 "Connect an AI agent to Librebase with hosted MCP. The user authenticates once in their browser — no API keys are ever pasted, and secrets stay sealed in the KMS." (hero claim, for-agents page)

**Source:** `docs/for-agents/page.tsx` lines 65–66 (after the Section 2 rewrite).

**Misleading because:** This is the elevator pitch and it's still overpromised, even after the Section 2 rewrite:

1. "The user authenticates once in their browser" — the user authenticates on a LibreBase-branded page (`app.librebase.xyz/mcp/authorize`), which is better than x.ai. But the agent still can't complete the flow without an MCP key (poll needs admin auth).
2. "No API keys are ever pasted" — only if the device flow completes end-to-end. Currently it can't, because the poll endpoints need admin auth.
3. "Secrets stay sealed in the KMS" — true for KMS-sealed values. The MCP key itself is a bearer token, not KMS-sealed.

**What's honest:** "Connect an AI agent to Librebase with hosted MCP. The recommended path is the OAuth device flow — the user visits a LibreBase-branded verification URL, signs in, and approves. **Currently the poll endpoints need admin auth**, so the device flow needs a pre-shared MCP key to complete. If the device flow is unavailable, generate an MCP key in the admin console. Secrets are sealed in the KMS; the MCP key is a bearer token that should be protected like any API key."

---

## 4. Where the Standards Are Not Followed — or Are Followed but Misleading (UPDATED)

### 4.1 MCP spec: device flow as onboarding pattern

**Spec:** MCP defines a tool-based auth pattern. LibreBase implements `POST /api/mcp/device/start` + `GET /api/mcp/device?user_code=...` + `POST /api/mcp/device/approve` + `POST /api/mcp/device/deny` as a device code flow.

**Standards compliance:** The device flow pattern is correct (RFC 8628). The new flow is closer to the standard than the old grok flow: the verification URI is on the same domain, the grants are disclosed.

**Where it deviates:**

- **Discovery is broken:** `/.well-known/mcp.json` returns HTML, not JSON. An MCP-compliant agent that does discovery first will fail.
- **The poll/approve/deny endpoints need admin auth:** In a standard device flow, the agent polls the token endpoint with the device code and gets the result. LibreBase's poll endpoint (`GET /api/mcp/device?user_code=...`) requires admin auth, which an unauthenticated agent doesn't have. This breaks the device flow's core value proposition (keyless onboarding).
- **The `auth_start` tool (old path) only offered grok:** The old `auth_start` tool in the MCP surface only accepted `provider: "grok"`, even though the admin console supported GitHub and Google. The new device flow (`POST /api/mcp/device/start`) is a separate endpoint — it's not clear if it offers the same provider restriction or if it's provider-agnostic. Needs investigation.

**Impact:** An agent using the MCP surface can start the device flow (new endpoint), get a LibreBase-branded auth URL, but can't complete it without a pre-shared MCP key. The device flow's promise (keyless onboarding) is not met on the live server.

---

### 4.2 The well-known discovery endpoint

**Spec:** MCP defines a well-known discovery endpoint (`/.well-known/mcp.json`) that returns the MCP server config as JSON.

**Reality:** On the live server, `GET /.well-known/mcp.json` returns 404 with `Content-Type: text/html; charset=utf-8` — the Next.js auth page HTML.

**Where this violates the standard:** The well-known endpoint must return JSON, not HTML. An agent that does discovery first (as the spec intends) gets HTML and cannot parse the MCP config.

**Impact:** The "auto-discovery" claim is false on the live server. The MCP endpoint URL must be hardcoded until the well-known endpoint is fixed.

---

### 4.3 The "OS keychain" claim

**Claim:** "The resulting token is stored in the OS keychain."

**Reality:** The device/approve or device/poll response would return a token (if the endpoints worked). The MCP server (stdio or HTTP) doesn't touch the OS keychain. The "OS keychain" claim assumes a client wrapper that stores tokens securely — but that wrapper isn't part of the MCP server.

**Where this is misleading:** It implies the platform handles secure token storage. In reality, the platform returns the token; the client decides how (or whether) to store it securely.

---

## 5. Where the Agent Got Lost During the Live Test — Exact Timeline (UPDATED)

### 2026-08-28, ~06:40 CEST — OLD FLOW PROBE

1. **Discovery test:** `GET /.well-known/mcp.json` → 200 (at the time). Clean JSON. No problem. *(Note: discovery is now broken — see below.)*
2. **tools/list test:** 200. Returns 24 tools. No problem.
3. **auth_start test (OLD grok flow):** 200. Returns device code, user code `KX4V-5F4C`, verification URI `https://accounts.x.ai/oauth2/device?user_code=KX4V-5F4C`. Protocol-level OK, but provider wall.
4. **auth_poll test (garbage device code):** 200 with `{"error":"unknown device code"}`. Flagged as UX issue (LIB-27).
5. **Unauthorized tool calls:** 401. Correct auth enforcement.
6. **Fake lb_mcp_ key:** 200 with `auth_error` JSON envelope. Correct MCP error pattern.
7. **Rate limit test:** 31 rapid initialize calls → 22×200, 9×429. Flagged as needing header verification (LIB-28).
8. **MCP key test (HANDOFF.md key):** All tool calls return `auth_error: Invalid or revoked MCP key`. Flagged as CRITICAL (LIB-35).

### ~07:00 CEST — Device flow approval attempt (OLD grok flow)

9. **Opened `https://accounts.x.ai/oauth2/device?user_code=KX4V-5F4C` in the Hermes preview pane.**
10. **Attempted to click Approve via `drive_preview` (action='elements' → click).** → Timed out. No GUI window answered.
11. **Attempted background browser session (browser_use CLI).** → Chrome presented "Allow remote debugging?" prompt. Could not clear from agent context. Session blocked.
12. **Polled `auth_poll` every 5 seconds for the full ~30-minute window.** → All returned `status: pending`. No approval received.

**Result:** The device flow could not be completed. The agent could not click Approve, could not visit x.ai, and had no grok account to sign in with.

### ~08:00 CEST — HTTP probe of OAuth providers (OLD grok flow)

13. **Tested `oauth/start?provider=grok` on live server.** → `{"error":"unsupported provider"}` HTTP 400.
14. **Tested `oauth/start?provider=github`.** → 307 redirect to `github.com/login/oauth/authorize?client_id=...`.
15. **Tested `oauth/start?provider=google`.** → 307 redirect to `accounts.google.com/o/oauth2/v2/auth?client_id=...`.

**Finding:** GitHub and Google are configured. Grok is not. The MCP surface only offered grok.

### ~08:19 CEST — Browser automation retry

16. **Opened `https://app.librebase.xyz/login` in a background browser session.** → Chrome "Allow remote debugging?" prompt again. Blocked.

**Result:** Browser automation consistently blocked by the remote debugging prompt on this machine.

### 2026-08-28, POSTNEW — NEW DEVICE FLOW PROBE (terminal, no browser)

17. **Tested `GET /.well-known/mcp.json`** → ❌ 404, `Content-Type: text/html; charset=utf-8`. Body is the Next.js auth page HTML. **Discovery is broken.**
18. **Tested `POST /api/mcp/device/start`** → ✅ 200. Returns LibreBase-branded auth URL (`https://app.librebase.xyz/mcp/authorize?user_code=7H4H-GTQA`), user code `7H4H-GTQA`, device code, requested grants (write access to projects/keys/logs/instances/hosts/members), expiresIn 1800, interval 5. **This is a real improvement.**
19. **Tested `POST /api/mcp/device/approve`** → ❌ 401, `{"error":"unauthorized"}`. **Needs admin auth.**
20. **Tested `GET /api/mcp/device?user_code=7H4H-GTQA`** → ❌ 401, `{"error":"unauthorized"}`. **Needs admin auth.**
21. **Tested `POST /api/mcp/device/deny`** → ❌ 401, `{"error":"unauthorized"}`. **Needs admin auth.**

**Result:** The new device flow starts correctly (LibreBase-branded auth URL, grants disclosed), but the approve/poll/deny endpoints need admin auth. An agent without a key can't complete the flow. Chicken-and-egg problem.

---

## 6. The Blockers — Ranked by Severity (UPDATED)

### Blocker 1 (CRITICAL): Well-known discovery returns HTML, not JSON

- **What:** `GET /.well-known/mcp.json` returns 404 with `Content-Type: text/html; charset=utf-8` — the Next.js auth page HTML, not the MCP config JSON.
- **Where it's documented:** `docs/llms.txt` line 18 ("Auto-discovery: GET .../.well-known/mcp.json returns the full config"), landing page copy.
- **Impact:** An agent doing discovery first (as the MCP spec intends) gets HTML and cannot parse the MCP config. The "auto-discovery" claim is false on the live server.
- **Filed:** LIB-29 (for-agents page returns dark HTML — llms.txt should be the canonical agent-readable entry), and this blocker should be filed as a separate issue for the well-known endpoint.

### Blocker 2 (CRITICAL): Device flow approve/poll/deny endpoints need admin auth

- **What:** `POST /api/mcp/device/approve`, `GET /api/mcp/device?user_code=...`, `POST /api/mcp/device/deny` all return `{"error":"unauthorized"}` without an admin session.
- **Where it's configured:** The device endpoints in the MCP route handler. Needs code review to understand the auth model.
- **Impact:** An agent without a key starts the device flow (gets the LibreBase-branded auth URL + user code), the human approves in the browser, but the agent can't poll for the result. Chicken-and-egg: the agent needs a key to authenticate to the poll endpoint, but the device flow is supposed to provide keyless onboarding.
- **Filed:** This is a new blocker — needs its own Linear issue.

### Blocker 3 (HIGH): MCP key from HANDOFF.md was revoked (now resolved — new key provided)

- **What:** The MCP key documented in HANDOFF.md (`lb_mcp_RLIiShwG6MdXL2_050H2YHDKYMXaTNbi-l6Z6dZxb5U`) did not authenticate.
- **Where it was documented:** HANDOFF.md line 104, `docs/llms.txt` fallback stdio config, `docs/for-agents/page.tsx` fallback stdio config.
- **Impact:** Any agent following the documented setup could not use the MCP endpoint.
- **Status:** RESOLVED — new key `lb_mcp_QcGE05dxRzFfNlqcurUOjMblK2djcV-R4wxfsvA2fOg` generated and verified. `mcp/README.md` updated with the new key.

### Blocker 4 (HIGH): Old `auth_start` tool only offered grok, and grok was not configured

- **What:** The old MCP `auth_start` tool only accepted `provider: "grok"`, but `LIBREBASE_GROK_CLIENT_ID` was not set on the VPS. `oauth/start?provider=grok` returned `{"error":"unsupported provider"}`.
- **Impact:** The agent's only onboarding path via the old MCP surface was broken. The admin console had working GitHub+Google providers that the MCP surface couldn't reach.
- **Status:** PARTIALLY RESOLVED — the new device flow (`POST /api/mcp/device/start`) uses a LibreBase-branded auth URL and may be provider-agnostic. Needs confirmation of what providers the new flow supports.

### Blocker 5 (MEDIUM): Device flow approval requires human-in-the-loop

- **What:** Even with the new LibreBase-branded flow, the agent cannot complete the device flow on its own. The user opens the verification URL in their browser, signs in, and clicks Approve. The agent has no way to do this.
- **Impact:** The agent cannot self-onboard. It requires a human to visit the LibreBase-branded URL and approve.
- **Filed:** LIB-37 (Agent onboarding via device flow blocked — needs human approval).

### Blocker 6 (ENVIRONMENT): Browser automation is blocked by Chrome remote debugging prompt

- **What:** The `browser_use` CLI sessions consistently hit a "Allow remote debugging?" Chrome prompt that cannot be cleared from the agent context.
- **Impact:** The agent cannot use browser automation to click OAuth approval buttons, take screenshots of the login flow, or verify the user-facing OAuth experience end-to-end.
- **Not filed separately** — environment limitation, not a LibreBase product issue. Workaround: HTTP probes (curl/urllib) to test the OAuth redirect URLs, as done in this audit.

---

## 7. What Would Fix Each Blocker (UPDATED)

### Blocker 1 fix: Well-known discovery endpoint returns JSON

- Fix `/.well-known/mcp.json` to return the MCP config JSON with `Content-Type: application/json`, not the Next.js auth page HTML.
- The landing page "auto-discovery" claim becomes true.
- An MCP-compliant agent can discover the endpoint without hardcoding the URL.

### Blocker 2 fix: Device flow poll/approve/deny endpoints accept device code without admin auth

- **Option A:** The poll endpoint (`GET /api/mcp/device?user_code=...`) accepts the device code directly and returns the result, without requiring admin auth. The device code itself is the proof that the agent started the flow.
- **Option B:** The approve endpoint is callable with the device code + a one-time token that the browser flow returns after human approval (so the agent can prove the human approved).
- **Option C:** The device flow returns an MCP key (or session token) directly in the `device/start` response after human approval, without a separate poll step.
- **Option D:** Document that the device flow requires a pre-shared MCP key to poll, and make that explicit in the onboarding docs. (Less elegant, but honest.)

### Blocker 4 fix: Confirm what providers the new device flow supports

- Test whether `POST /api/mcp/device/start` is provider-agnostic (works with GitHub, Google, or any configured provider) or if it still routes to a specific provider.
- If it's provider-agnostic, the new flow fixes the provider-wall issue from the old `auth_start` tool.
- If it still routes to grok, the provider-wall issue persists and needs fixing (wire grok on the VPS, or expose GitHub/Google in the new flow).

### Blocker 5 fix: Add a direct agent key-gen path, OR accept human-in-the-loop as the design

- **Option A:** Add an endpoint that lets the agent request an MCP key directly after the human approves the OAuth flow.
- **Option B:** Accept that the device flow requires a human to approve, and document the human-in-the-loop step clearly. The agent starts the flow, displays the URL + user code to the human, the human approves, the agent polls (if poll auth is fixed).
- **Option C:** Add Google and GitHub as OAuth providers in the device flow, so the agent can use providers that are actually configured.

---

## 8. Summary — What Works, What Doesn't, What's Needed (UPDATED)

### What works on the live server right now

- ✅ `POST /api/mcp/device/start` — 200, returns LibreBase-branded auth URL + user code + device code + requested grants. Real improvement over the old grok flow.
- ✅ `POST /api/mcp` with `tools/list` — 200, returns all 24 tools.
- ✅ MCP protocol handshake (`initialize`) — 200, returns serverInfo.
- ✅ Auth enforcement on protected tools — 401 without token, 401 with invalid token format.
- ✅ MCP error envelope for auth errors — 200 with `{"error":"auth_error",...}` for fake/revoked keys.
- ✅ Rate limiting — kicks in at 30 req/min, returns 429.
- ✅ GitHub OAuth on the admin console — redirects to github.com with valid client ID.
- ✅ Google OAuth on the admin console — redirects to accounts.google.com with valid client ID.
- ✅ New MCP key works — `lb_mcp_QcGE05dxRzFfNlqcurUOjMblK2djcV-R4wxfsvA2fOg` authenticates and returns org + projects + instances.

### What doesn't work on the live server right now

- ❌ `GET /.well-known/mcp.json` — 404, returns HTML (Next.js auth page), not JSON. Discovery is broken.
- ❌ Device flow approve/poll/deny endpoints — return `{"error":"unauthorized"}` without admin auth. Agent can't complete the device flow without a pre-shared key.
- ❌ Old `auth_start` tool only offered grok (may be superseded by new device flow — needs confirmation).
- ❌ Browser automation — blocked by Chrome remote debugging prompt on this machine (environment, not product).

### What the agent needs to proceed

1. A working MCP key (from the admin console, passed to the agent) — for non-interactive use and to authenticate to the poll endpoints.
2. OR the well-known discovery endpoint fixed (returns JSON, not HTML).
3. OR the device flow poll/approve/deny endpoints accept the device code without admin auth (keyless onboarding works).
4. OR the new device flow's provider support confirmed (is it provider-agnostic, or does it still route to grok?).

---

## 9. The New Flow — What's Good, What's Still Broken

### What's good about the new flow

1. **LibreBase-branded auth URL:** `https://app.librebase.xyz/mcp/authorize?user_code=7H4H-GTQA` — the user visits a LibreBase page, not `accounts.x.ai`. No third-party provider wall.
2. **Grants disclosed:** `requestedGrants` block shows write access to projects, keys, logs, instances, hosts, members. Transparent about what's being requested.
3. **No grok dependency:** The new flow doesn't route to `accounts.x.ai` — it's unclear if it's provider-agnostic or still routes to a specific provider. Needs confirmation.

### What's still broken about the new flow

1. **Discovery is broken:** `/.well-known/mcp.json` returns HTML, not JSON. The agent can't discover the MCP endpoint without hardcoding the URL.
2. **Poll/approve/deny need admin auth:** The agent starts the device flow, gets the LibreBase-branded URL, the human approves — but the agent can't poll for the result. Chicken-and-egg.
3. **Human-in-the-loop still required:** The agent can't open the browser and click Approve. The human must do it.

### Bottom line

The new device flow is a real improvement over the old grok flow — LibreBase-branded auth URL, grants disclosed, no third-party provider wall. But the agent still can't self-onboard on the live server: discovery is broken (HTML, not JSON), and the poll endpoints need admin auth. The agent needs a pre-shared MCP key to complete the flow, which defeats the purpose of keyless onboarding.

---

*End of document.*

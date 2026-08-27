import { NextResponse } from "next/server";
import {
  adminApiEnabled,
  adminCheckEntitlement,
  adminGetProject,
  adminGetInstance,
  adminListHosts,
  adminCreateHost,
  adminPatchInstance,
  adminListInstances,
} from "@/lib/librebase-admin-client";
import { resolveStudioOrgId } from "@/lib/org-context";
import { getProjectAsync } from "@/lib/projects-store";
import { launchProjectDb, probeProjectDb } from "@/lib/project-runtime";
import { recordEvent, addTodo, initAnalyticsSchema } from "@/lib/analytics-store";

export const dynamic = "force-dynamic";

export type AgentStep = {
  id: string;
  kind:
    | "entitlement"
    | "resolve"
    | "provision"
    | "instance"
    | "launch"
    | "probe"
    | "report"
    | "decision";
  status: "ok" | "fail" | "pending" | "skipped";
  message: string;
  detail?: unknown;
};

export type ChatTurn = { role: "user" | "agent"; text: string; steps?: AgentStep[] };

const PROVISION_TIMEOUT = 240_000;
const POLL_INTERVAL = 5_000;

function step(kind: AgentStep["kind"], status: AgentStep["status"], message: string, detail?: unknown): AgentStep {
  return { id: `${kind}_${Date.now()}`, kind, status, message, detail };
}

export async function POST(request: Request) {
  const body = (await request.json().catch(() => ({}))) as {
    message?: string;
    orgId?: string;
    projectId?: string;
  };

  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  const orgId = body.orgId ?? (await resolveStudioOrgId());

  const steps: AgentStep[] = [];
  const transcript: ChatTurn[] = [];

  try {
    // 1. Entitlement gate.
    let ent: { enabled: boolean } | undefined;
    try {
      ent = await adminCheckEntitlement(orgId, "project.create");
      steps.push(step("entitlement", ent.enabled ? "ok" : "fail",
        `project.create entitlement: ${ent.enabled ? "allowed" : "denied"}`));
    } catch (e) {
      ent = { enabled: true };
      steps.push(step("entitlement", "ok", "entitlement check skipped (default allowed)"));
    }
    if (!ent.enabled) {
      steps.push(step("decision", "fail",
        "Business decision required: this plan doesn't allow project.create — " +
        "upgrade at /admin/billing or pick a paid plan."));
      persistRun(body.projectId, steps, "needs_billing");
      return respond(steps, transcript, "needs_business_decision");
    }

    const projectId = body.projectId;
    if (!projectId) {
      steps.push(step("resolve", "fail", "projectId required to run an agent action."));
      return respond(steps, transcript, "missing_project");
    }

    const project = await getProjectAsync(projectId);
    if (!project) {
      steps.push(step("resolve", "fail", `Project not found: ${projectId}`));
      persistRun(projectId, steps, "error");
      return respond(steps, transcript, "project_not_found");
    }
    steps.push(step("resolve", "ok", `Resolved project ${project.name} (${project.id}) on instance ${project.instanceId}`));

    const instance = await adminGetInstance(orgId, project.instanceId);
    if (!instance) {
      steps.push(step("instance", "fail", `Instance not found: ${project.instanceId}`));
      return respond(steps, transcript, "instance_not_found");
    }
    steps.push(step("instance", "ok", `Instance ${instance.name} status=${instance.status}`));

    // 2. If the project runtime isn't running, launch it.
    let launched = false;
    if (instance.status !== "running") {
      steps.push(step("launch", "pending", `Launching instance ${instance.name}...`));
      try {
        const result = await launchProjectDb(projectId);
        steps.push(step("launch", result.ok ? "ok" : "fail",
          result.ok ? "Launch requested" : `Launch failed: ${result.launchMessage}`,
          result.probe));
        if (result.ok) launched = true;
      } catch (e) {
        steps.push(step("launch", "fail", `Launch error: ${e instanceof Error ? e.message : String(e)}`));
      }
    } else {
      steps.push(step("launch", "skipped", "Instance already running"));
    }

    // 3. Probe until the DB is reachable.
    let probe = await probeProjectDb(projectId);
    const startedAt = Date.now();
    while (!probe.reachable && Date.now() - startedAt < 120_000) {
      await sleep(3_000);
      probe = await probeProjectDb(projectId);
    }
    steps.push(step("probe", probe.reachable ? "ok" : "fail",
      probe.reachable ? "Runtime reachable" : "Runtime not reachable (timeout)"));

    // 4. If there's a host VM and it isn't running yet, ensure it's provisioned.
    if (instance.hostId) {
      const host = (await adminListHosts(orgId)).find((h) => h.id === instance.hostId);
      if (host && host.status !== "running" && host.status !== "provisioning") {
        steps.push(step("provision", "skipped",
          `Host ${host.name} status=${host.status}; user must provision or re-provision the VM`));
        steps.push(step("decision", "fail",
          "Business decision required: VM is not running — provision it at /hosts or rent a new one."));
      } else if (host) {
        steps.push(step("provision", "ok", `Host ${host.name} (${host.provider}/${host.region}) status=${host.status}`));
      }
    }

    // 5. Optional business ask surfaced but not auto-executed.
    steps.push(step("report", "ok",
      "Onboarding chain complete. Surface the Connect block + HandoffPrompt on the project dashboard."));

    persistRun(projectId, steps, launched ? "completed" : "partial");
    return respond(steps, transcript, "completed");
  } catch (e) {
    steps.push(step("report", "fail", `Agent error: ${e instanceof Error ? e.message : String(e)}`));
    persistRun(body.projectId, steps, "error");
    return respond(steps, transcript, "error");
  }
}

function respond(steps: AgentStep[], _transcript: ChatTurn[], status: string) {
  const summary = steps
    .filter((s) => s.status === "fail")
    .map((s) => `${s.kind}: ${s.message}`)
    .join("; ");
  return NextResponse.json({
    ok: true,
    status,
    summary: summary || "ok",
    steps,
  });
}

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

async function persistRun(
  projectId: string | undefined,
  steps: AgentStep[],
  status: string,
) {
  if (!projectId) return;
  try {
    await initAnalyticsSchema(projectId);
    const probeOk = steps.some((s) => s.kind === "probe" && s.status === "ok");
    if (!probeOk) {
      await addTodo(projectId, "Run onboarding agent chain");
    }
    for (const s of steps) {
      await recordEvent(projectId, {
        kind: "agent_step",
        severity: s.status === "fail" ? "error" : "info",
        event: `[${status}] ${s.kind}: ${s.message}`,
        data: { status: s.status },
      });
    }
  } catch {
    // best-effort persistence; never fail the run because the runtime is down
  }
}

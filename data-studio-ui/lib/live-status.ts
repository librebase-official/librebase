import type { Host, InstanceStatus } from "./types";

export function hostIsProvisioning(host?: Host | null): boolean {
  if (!host) return false;
  return host.status === "provisioning" || host.status === "starting";
}

export function liveInstanceView(opts: {
  host?: Host | null;
  reachable: boolean;
  status: InstanceStatus;
  /** Row status from the control plane — not the wait-for-VM probe overlay. */
  persistedStatus?: InstanceStatus;
}): { variant: "running" | "starting" | "stopped"; label: string; spinner: boolean } {
  if (hostIsProvisioning(opts.host)) {
    return { variant: "starting", label: "Provisioning VM", spinner: true };
  }
  if (opts.reachable) {
    return { variant: "running", label: "Running", spinner: false };
  }
  // Probe reports "starting" while the VM boots, but we do not persist that.
  // Once the VM is up, show Stopped unless the user actually launched.
  if (opts.persistedStatus === "starting") {
    return { variant: "starting", label: "Starting", spinner: true };
  }
  return { variant: "stopped", label: "Stopped", spinner: false };
}

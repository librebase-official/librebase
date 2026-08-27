import { readJsonFile, writeJsonFile } from "./json-store";

export interface AuthSettings {
  projectId: string;
  allowSignup: boolean;
  confirmEmail: boolean;
  allowAnonymous: boolean;
  allowManualLinking: boolean;
  emailProvider: boolean;
  githubProvider: boolean;
  googleProvider: boolean;
}

const FILE = "auth-settings.json";

const DEFAULTS: Omit<AuthSettings, "projectId"> = {
  allowSignup: true,
  confirmEmail: true,
  allowAnonymous: false,
  allowManualLinking: false,
  emailProvider: true,
  githubProvider: false,
  googleProvider: false,
};

export function getAuthSettings(projectId: string): AuthSettings {
  const all = readJsonFile<AuthSettings[]>(FILE, []);
  return all.find((s) => s.projectId === projectId) ?? { projectId, ...DEFAULTS };
}

export function saveAuthSettings(
  projectId: string,
  patch: Partial<Omit<AuthSettings, "projectId">>,
): AuthSettings {
  const all = readJsonFile<AuthSettings[]>(FILE, []);
  const index = all.findIndex((s) => s.projectId === projectId);
  const next: AuthSettings = {
    ...(index >= 0 ? all[index] : { projectId, ...DEFAULTS }),
    ...patch,
    projectId,
  };
  if (index >= 0) all[index] = next;
  else all.push(next);
  writeJsonFile(FILE, all);
  return next;
}

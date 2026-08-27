import type { ReactNode } from "react";
import { ProjectChromeSetter } from "@/components/studio/StudioFrame";

export type ProjectSection = "home" | "database" | "sql" | "settings";

export function ProjectShell({
  projectId,
  projectName,
  children,
}: {
  projectId: string;
  projectName: string;
  active?: ProjectSection;
  children: ReactNode;
}) {
  return (
    <>
      <ProjectChromeSetter id={projectId} name={projectName} />
      {children}
    </>
  );
}

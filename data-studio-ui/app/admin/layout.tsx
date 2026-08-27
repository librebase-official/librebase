import { OrgShell } from "@/components/OrgShell";
import { resolveStudioOrgId } from "@/lib/org-context";

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const orgId = await resolveStudioOrgId();
  return <OrgShell orgId={orgId}>{children}</OrgShell>;
}

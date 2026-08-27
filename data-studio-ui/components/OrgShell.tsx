import { StudioProvider } from "@/components/studio/StudioFrame";

export function OrgShell({
  orgId,
  children,
}: {
  orgId: string;
  children: React.ReactNode;
}) {
  return <StudioProvider orgId={orgId}>{children}</StudioProvider>;
}

import { OrgShell } from "@/components/OrgShell";

export default function StudioCloudLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <OrgShell>{children}</OrgShell>;
}

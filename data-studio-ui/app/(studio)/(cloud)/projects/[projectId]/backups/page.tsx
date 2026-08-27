import { requireProjectPage } from "@/lib/projects-store";
import { ProjectShell } from "../_components/project-shell";

export const dynamic = "force-dynamic";

interface PageProps {
  params: Promise<{ projectId: string }>;
}

export default async function BackupsPage({ params }: PageProps) {
  const { projectId } = await params;
  const project = await requireProjectPage(projectId);

  return (
    <ProjectShell projectId={projectId} projectName={project.name} active="settings">
      <div className="p-6 max-w-4xl">
        <h1 className="text-2xl font-semibold">Backups — hourly, 30d WORM, per-instance Volumes</h1>
        <p className="text-muted-foreground mt-2">
          Per-instance volume <code>lb-bak-{'{instance_id}'}</code> <span className="font-mono">60/100/500GB</span> caps (starter/pro/scale, 80% margin),
          <span className="ml-1">hourly incremental</span> + weekly full <span className="font-mono">≈1.3× DB</span>,
          <span className="ml-1">AES-256-GCM</span> via Li-native <code>li-kms</code>, <code>chattr +i 30d</code> WORM,
          <span className="ml-1">RPO 1h / RTO &lt;1h</span> (SOC2/GDPR). Additional replication to your own S3 bucket via MCP.
        </p>
        <div className="mt-6 rounded border p-4">
          <h2 className="font-medium">External bucket replication (MCP)</h2>
          <pre className="mt-2 text-xs bg-muted p-3 rounded overflow-auto">{`bucket_create_external {name:"my-r2", endpoint:"https://<acct>.r2.cloudflarestorage.com", bucket:"my-snapshots", accessKey:"...", secretKey:"..."}
backup_link_external {projectId:"${projectId}", bucketId:"bkt_..."}  # hourly snapshots additionally to your bucket
bucket_list / backup_external_status / bucket_delete`}</pre>
        </div>
        <div className="mt-6 rounded border p-4">
          <h2 className="font-medium">Status</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Primary: per-instance volume <code>/var/lib/librebase-backups/{'{instance_id}'}/</code> — hourly, 30d retention, quota {`60/100/500GB`}.
            External: <code>project_backups.external_bucket_id</code> → S3 SigV4 PUT after volume write (host-agent).
          </p>
        </div>
      </div>
    </ProjectShell>
  );
}

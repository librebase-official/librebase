import type { Instance, Project } from "./types";

/** Placeholder image until a published lidb runtime exists. */
export const LIDB_RUNTIME_IMAGE =
  process.env.LIBREBASE_K8S_IMAGE ?? "ghcr.io/librebase-official/lidb-runtime:stub";

const DEFAULT_API_PORT = 54320;
const DEFAULT_POSTGRES_PORT = 54322;

export function dedicatedNamespace(instanceId: string): string {
  return `librebase-inst-${instanceId}`;
}

export function sharedNamespace(orgId: string): string {
  const slug = orgId.replace(/[^a-z0-9-]/gi, "-").toLowerCase() || "default";
  return `librebase-shared-${slug}`;
}

export function instanceLabels(
  instance: Instance,
  project?: Pick<Project, "id">,
): Record<string, string> {
  const labels: Record<string, string> = {
    "app.kubernetes.io/name": "librebase-instance",
    "app.kubernetes.io/part-of": "librebase",
    "librebase.io/org": instance.orgId,
    "librebase.io/instance": instance.id,
    "librebase.io/deployment-mode": instance.deploymentMode,
  };
  if (project) {
    labels["librebase.io/project"] = project.id;
  }
  return labels;
}

function probeCommand(apiPort: number, postgresPort: number): string[] {
  return [
    "python3",
    "/opt/librebase/scripts/lidb_engine.py",
    "status",
    "--data-dir",
    "/data",
    "--api-port",
    String(apiPort),
    "--postgres-port",
    String(postgresPort),
  ];
}

export interface DedicatedManifestInput {
  instance: Instance;
  image?: string;
  apiPort?: number;
  postgresPort?: number;
}

export function buildDedicatedManifests(input: DedicatedManifestInput): string {
  const { instance } = input;
  const image = input.image ?? LIDB_RUNTIME_IMAGE;
  const apiPort = input.apiPort ?? DEFAULT_API_PORT;
  const postgresPort = input.postgresPort ?? DEFAULT_POSTGRES_PORT;
  const ns = dedicatedNamespace(instance.id);
  const labels = instanceLabels(instance);
  const labelLines = Object.entries(labels)
    .map(([k, v]) => `    ${k}: "${v}"`)
    .join("\n");

  return `---
apiVersion: v1
kind: Namespace
metadata:
  name: ${ns}
  labels:
${labelLines}
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: librebase-data
  namespace: ${ns}
  labels:
${labelLines}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: librebase-config
  namespace: ${ns}
  labels:
${labelLines}
data:
  LI_DATA_DIR: "/data"
  LIBREBASE_API_PORT: "${apiPort}"
  LIBREBASE_PG_PORT: "${postgresPort}"
  LIBREBASE_INSTANCE_ID: "${instance.id}"
  LIBREBASE_ORG_ID: "${instance.orgId}"
---
apiVersion: v1
kind: Secret
metadata:
  name: librebase-secrets
  namespace: ${ns}
  labels:
${labelLines}
type: Opaque
stringData:
  # TODO: wire real credentials when lidb embed ships
  POSTGRES_PASSWORD: "librebase-dev-only"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: librebase-runtime
  namespace: ${ns}
  labels:
${labelLines}
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: librebase-instance
      librebase.io/instance: "${instance.id}"
  template:
    metadata:
      labels:
${labelLines}
    spec:
      containers:
        - name: lis-lidb
          image: ${image}
          imagePullPolicy: IfNotPresent
          ports:
            - name: api
              containerPort: ${apiPort}
            - name: postgres
              containerPort: ${postgresPort}
          envFrom:
            - configMapRef:
                name: librebase-config
            - secretRef:
                name: librebase-secrets
          volumeMounts:
            - name: data
              mountPath: /data
          livenessProbe:
            exec:
              command:
${probeCommand(apiPort, postgresPort)
  .map((c) => `                - "${c}"`)
  .join("\n")}
            initialDelaySeconds: 15
            periodSeconds: 20
            failureThreshold: 3
          readinessProbe:
            tcpSocket:
              port: api
            initialDelaySeconds: 5
            periodSeconds: 10
          resources:
            requests:
              cpu: 100m
              memory: 256Mi
            limits:
              cpu: "1"
              memory: 1Gi
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: librebase-data
---
apiVersion: v1
kind: Service
metadata:
  name: librebase-api
  namespace: ${ns}
  labels:
${labelLines}
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/name: librebase-instance
    librebase.io/instance: "${instance.id}"
  ports:
    - name: api
      port: ${apiPort}
      targetPort: api
    - name: postgres
      port: ${postgresPort}
      targetPort: postgres
`;
}

export interface SharedProjectManifestInput {
  instance: Instance;
  project: Project;
}

/** Shared pattern: project namespace config in the instance's shared namespace. */
export function buildSharedProjectConfigMap(input: SharedProjectManifestInput): string {
  const { instance, project } = input;
  const ns = sharedNamespace(instance.orgId);
  const labels = instanceLabels(instance, project);
  const labelLines = Object.entries(labels)
    .map(([k, v]) => `    ${k}: "${v}"`)
    .join("\n");

  return `---
apiVersion: v1
kind: ConfigMap
metadata:
  name: librebase-project-${project.id}
  namespace: ${ns}
  labels:
${labelLines}
data:
  LIBREBASE_PROJECT_ID: "${project.id}"
  LIBREBASE_PROJECT_NAME: "${project.name}"
  LIBREBASE_INSTANCE_ID: "${instance.id}"
  LIBREBASE_SCHEMA_NAMESPACE: "${project.id}"
`;
}

/** Base shared namespace + single runtime deployment (one instance, N project ConfigMaps). */
export function buildSharedInstanceManifests(input: DedicatedManifestInput): string {
  const { instance } = input;
  const image = input.image ?? LIDB_RUNTIME_IMAGE;
  const apiPort = input.apiPort ?? DEFAULT_API_PORT;
  const postgresPort = input.postgresPort ?? DEFAULT_POSTGRES_PORT;
  const ns = sharedNamespace(instance.orgId);
  const labels = instanceLabels(instance);
  const labelLines = Object.entries(labels)
    .map(([k, v]) => `    ${k}: "${v}"`)
    .join("\n");

  return `---
apiVersion: v1
kind: Namespace
metadata:
  name: ${ns}
  labels:
${labelLines}
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: librebase-data-${instance.id}
  namespace: ${ns}
  labels:
${labelLines}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: librebase-config-${instance.id}
  namespace: ${ns}
  labels:
${labelLines}
data:
  LI_DATA_DIR: "/data"
  LIBREBASE_API_PORT: "${apiPort}"
  LIBREBASE_PG_PORT: "${postgresPort}"
  LIBREBASE_INSTANCE_ID: "${instance.id}"
  LIBREBASE_ORG_ID: "${instance.orgId}"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: librebase-runtime-${instance.id}
  namespace: ${ns}
  labels:
${labelLines}
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: librebase-instance
      librebase.io/instance: "${instance.id}"
  template:
    metadata:
      labels:
${labelLines}
    spec:
      containers:
        - name: lis-lidb
          image: ${image}
          imagePullPolicy: IfNotPresent
          ports:
            - name: api
              containerPort: ${apiPort}
            - name: postgres
              containerPort: ${postgresPort}
          envFrom:
            - configMapRef:
                name: librebase-config-${instance.id}
          volumeMounts:
            - name: data
              mountPath: /data
          livenessProbe:
            exec:
              command:
${probeCommand(apiPort, postgresPort)
  .map((c) => `                - "${c}"`)
  .join("\n")}
            initialDelaySeconds: 15
            periodSeconds: 20
          readinessProbe:
            tcpSocket:
              port: api
            initialDelaySeconds: 5
            periodSeconds: 10
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: librebase-data-${instance.id}
---
apiVersion: v1
kind: Service
metadata:
  name: librebase-api-${instance.id}
  namespace: ${ns}
  labels:
${labelLines}
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/name: librebase-instance
    librebase.io/instance: "${instance.id}"
  ports:
    - name: api
      port: ${apiPort}
      targetPort: api
    - name: postgres
      port: ${postgresPort}
      targetPort: postgres
`;
}

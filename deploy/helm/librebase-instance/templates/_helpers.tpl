{{- define "librebase.labels" -}}
app.kubernetes.io/name: librebase-instance
app.kubernetes.io/part-of: librebase
librebase.io/org: {{ .Values.orgId | quote }}
librebase.io/instance: {{ .Values.instanceId | quote }}
librebase.io/deployment-mode: {{ .Values.deploymentMode | quote }}
{{- if .Values.projectId }}
librebase.io/project: {{ .Values.projectId | quote }}
{{- end }}
{{- end }}

{{- define "librebase.namespace" -}}
{{- if eq .Values.deploymentMode "shared" -}}
librebase-shared-{{ .Values.orgId | lower | replace "_" "-" }}
{{- else -}}
librebase-inst-{{ .Values.instanceId }}
{{- end -}}
{{- end }}

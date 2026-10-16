{{/* Release-scoped name prefix, at most 40 characters so component names fit. */}}
{{- define "world.fullname" -}}
{{- if contains .Chart.Name .Release.Name -}}
{{- .Release.Name | trunc 40 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 40 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "world.name" -}}
{{- printf "%s-%s" (include "world.fullname" .root) .component -}}
{{- end -}}

{{- define "world.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .root.Chart.Name .root.Chart.Version | quote }}
app.kubernetes.io/managed-by: {{ .root.Release.Service }}
app.kubernetes.io/part-of: hangang-world
{{ include "world.selectorLabels" . }}
{{- end -}}

{{- define "world.selectorLabels" -}}
app.kubernetes.io/name: {{ .component }}
app.kubernetes.io/instance: {{ .root.Release.Name }}
{{- end -}}

{{/* Service DNS name used in certificates and peer configuration. */}}
{{- define "world.host" -}}
{{- printf "%s.%s.svc" (include "world.name" .) .root.Release.Namespace -}}
{{- end -}}

{{/* repository[:tag]@digest — the digest is always present for enabled components. */}}
{{- define "world.image" -}}
{{- $image := .image -}}
{{- if not $image.digest -}}
{{- fail (printf "%s.image.digest is required: images are pinned by digest (sha256:...)" .component) -}}
{{- end -}}
{{- if $image.tag -}}
{{- printf "%s:%s@%s" $image.repository $image.tag $image.digest -}}
{{- else -}}
{{- printf "%s@%s" $image.repository $image.digest -}}
{{- end -}}
{{- end -}}

{{- define "world.tlsSecret" -}}
{{- if eq .root.Values.tls.mode "existingSecrets" -}}
{{- index .root.Values.tls.existingSecrets .component -}}
{{- else -}}
{{- printf "%s-tls" (include "world.name" .) -}}
{{- end -}}
{{- end -}}

{{/* Client TLS block for a peer, as the component configurations expect it. */}}
{{- define "world.peerTls" -}}
{"server_name":{{ include "world.host" . | quote }},"ca":"/tls/ca.crt","certificate":"/tls/tls.crt","key":"/tls/tls.key"}
{{- end -}}

{{- define "world.secretEnv" -}}
- name: {{ .name }}
  valueFrom:
    secretKeyRef:
      name: {{ .root.Values.credentials.existingSecret }}
      key: {{ index .root.Values.credentials.keys .key }}
{{- end -}}

{{- define "world.podSecurityContext" -}}
runAsNonRoot: true
runAsUser: 65532
runAsGroup: 65532
fsGroup: 65532
fsGroupChangePolicy: OnRootMismatch
seccompProfile:
  type: RuntimeDefault
{{- end -}}

{{- define "world.containerSecurityContext" -}}
runAsNonRoot: true
runAsUser: 65532
runAsGroup: 65532
allowPrivilegeEscalation: false
readOnlyRootFilesystem: true
privileged: false
capabilities:
  drop: ["ALL"]
seccompProfile:
  type: RuntimeDefault
{{- end -}}

{{/* Scheduling and pull secrets shared by every Pod. */}}
{{- define "world.podCommon" -}}
{{- $values := .values -}}
{{- with .root.Values.global.imagePullSecrets }}
imagePullSecrets:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- with $values.nodeSelector }}
nodeSelector:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- with $values.tolerations }}
tolerations:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- with $values.affinity }}
affinity:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- with $values.priorityClassName }}
priorityClassName: {{ . }}
{{- end }}
{{- end -}}

{{- define "world.tlsVolume" -}}
- name: tls
  secret:
    secretName: {{ include "world.tlsSecret" . }}
    defaultMode: 0440
{{- end -}}

{{- define "world.pvc" -}}
{{- $values := index .root.Values .component -}}
{{- if not $values.persistence.existingClaim }}
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "world.name" . }}-state
  labels:
    {{- include "world.labels" . | nindent 4 }}
  annotations:
    # Keep component state when the release is uninstalled.
    helm.sh/resource-policy: keep
spec:
  accessModes: ["ReadWriteOnce"]
  {{- with $values.persistence.storageClassName }}
  storageClassName: {{ . }}
  {{- end }}
  resources:
    requests:
      storage: {{ $values.persistence.size }}
{{- end }}
{{- end -}}

{{- define "world.stateClaim" -}}
{{- $values := index .root.Values .component -}}
{{- default (printf "%s-state" (include "world.name" .)) $values.persistence.existingClaim -}}
{{- end -}}

{{- define "world.pdb" -}}
{{- $values := index .root.Values .component -}}
{{- if and $values.enabled $values.pdb $values.pdb.enabled (gt (int $values.replicas) 1) }}
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: {{ include "world.name" . }}
  labels:
    {{- include "world.labels" . | nindent 4 }}
spec:
  maxUnavailable: {{ $values.pdb.maxUnavailable }}
  selector:
    matchLabels:
      {{- include "world.selectorLabels" . | nindent 6 }}
{{- end }}
{{- end -}}

{{- define "world.peer" -}}
- podSelector:
    matchLabels:
      {{- include "world.selectorLabels" . | nindent 6 }}
{{- end -}}

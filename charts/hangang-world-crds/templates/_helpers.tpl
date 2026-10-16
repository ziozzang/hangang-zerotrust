{{- define "hangang-world-crds.labels" -}}
app.kubernetes.io/name: hangang-world-crds
app.kubernetes.io/part-of: hangang-world
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | quote }}
{{- end -}}

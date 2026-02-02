{{/*
Expand the name of the chart.
*/}}
{{- define "secapi.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "secapi.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "secapi.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "secapi.labels" -}}
helm.sh/chart: {{ include "secapi.chart" . }}
{{ include "secapi.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "secapi.selectorLabels" -}}
app.kubernetes.io/name: {{ include "secapi.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
API labels
*/}}
{{- define "secapi.api.labels" -}}
{{ include "secapi.labels" . }}
app.kubernetes.io/component: api
{{- end }}

{{/*
Worker labels
*/}}
{{- define "secapi.worker.labels" -}}
{{ include "secapi.labels" . }}
app.kubernetes.io/component: worker
{{- end }}

{{/*
Flower labels
*/}}
{{- define "secapi.flower.labels" -}}
{{ include "secapi.labels" . }}
app.kubernetes.io/component: flower
{{- end }}

{{/*
PostgreSQL labels
*/}}
{{- define "secapi.postgres.labels" -}}
{{ include "secapi.labels" . }}
app.kubernetes.io/component: postgres
{{- end }}

{{/*
Redis labels
*/}}
{{- define "secapi.redis.labels" -}}
{{ include "secapi.labels" . }}
app.kubernetes.io/component: redis
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "secapi.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "secapi.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Database connection string for PostgreSQL
*/}}
{{- define "secapi.databaseUrl" -}}
postgresql+asyncpg://{{ .Values.postgres.postgresUser }}:{{ .Values.postgres.postgresPassword | default "changeme" }}@{{ include "secapi.fullname" . }}-postgres:5432/{{ .Values.postgres.postgresDatabase }}
{{- end }}

{{/*
Redis connection string
*/}}
{{- define "secapi.redisUrl" -}}
redis://{{ include "secapi.fullname" . }}-redis:6379/0
{{- end }}

{{/*
Celery broker URL
*/}}
{{- define "secapi.celeryBrokerUrl" -}}
redis://{{ include "secapi.fullname" . }}-redis:6379/1
{{- end }}

{{/*
Celery result backend URL
*/}}
{{- define "secapi.celeryResultBackend" -}}
redis://{{ include "secapi.fullname" . }}-redis:6379/2
{{- end }}

{{/*
Image pull secret name
*/}}
{{- define "secapi.imagePullSecrets" -}}
{{- if .Values.imagePullSecrets }}
imagePullSecrets:
{{- range .Values.imagePullSecrets }}
  - name: {{ . }}
{{- end }}
{{- end }}
{{- end }}

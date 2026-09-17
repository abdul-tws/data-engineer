{{/*
Expand the name of the chart.
*/}}
{{- define "fund-reconciliation.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "fund-reconciliation.fullname" -}}
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
{{- define "fund-reconciliation.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "fund-reconciliation.labels" -}}
helm.sh/chart: {{ include "fund-reconciliation.chart" . }}
{{ include "fund-reconciliation.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "fund-reconciliation.selectorLabels" -}}
app.kubernetes.io/name: {{ include "fund-reconciliation.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app: fund-reconciliation
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "fund-reconciliation.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "fund-reconciliation.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Container environment variables
*/}}
{{- define "fund-reconciliation.containerEnv" -}}
# Configuration from ConfigMap
- name: ENVIRONMENT
  valueFrom:
    configMapKeyRef:
      name: {{ include "fund-reconciliation.fullname" . }}
      key: ENVIRONMENT
- name: LOG_LEVEL
  valueFrom:
    configMapKeyRef:
      name: {{ include "fund-reconciliation.fullname" . }}
      key: LOG_LEVEL
- name: PYTHONUNBUFFERED
  valueFrom:
    configMapKeyRef:
      name: {{ include "fund-reconciliation.fullname" . }}
      key: PYTHONUNBUFFERED

# Database configuration
{{- if .Values.database.enabled }}
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: {{ include "fund-reconciliation.fullname" . }}
      key: database-url
{{- end }}

# Redis configuration
{{- if .Values.redis.enabled }}
- name: REDIS_URL
  valueFrom:
    secretKeyRef:
      name: {{ include "fund-reconciliation.fullname" . }}
      key: redis-url
{{- end }}

# Application mode
- name: MODE
  value: {{ .Values.app.mode | quote }}
{{- end }}

{{/*
Container volume mounts
*/}}
{{- define "fund-reconciliation.volumeMounts" -}}
{{- if .Values.persistence.data.enabled }}
- name: data
  mountPath: /app/data
{{- end }}
{{- if .Values.persistence.output.enabled }}
- name: output
  mountPath: /app/output
{{- end }}
- name: config
  mountPath: /app/config
  readOnly: true
{{- end }}

{{/*
Volumes
*/}}
{{- define "fund-reconciliation.volumes" -}}
- name: config
  configMap:
    name: {{ include "fund-reconciliation.fullname" . }}
{{- if .Values.persistence.data.enabled }}
- name: data
  persistentVolumeClaim:
    claimName: {{ include "fund-reconciliation.fullname" . }}-data
{{- end }}
{{- if .Values.persistence.output.enabled }}
- name: output
  persistentVolumeClaim:
    claimName: {{ include "fund-reconciliation.fullname" . }}-output
{{- end }}
{{- end }}

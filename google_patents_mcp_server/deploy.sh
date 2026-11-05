#!/usr/bin/env bash
# Deploy Google Patents MCP Server to Google Cloud Run (with Option 1 OAuth 2.0 for Gemini Enterprise)
set -euo pipefail

SERVICE_NAME="${SERVICE_NAME:-google-patents-mcp-server}"
REGION="${REGION:-us-central1}"
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || echo "")}"
GOOGLE_OAUTH_CLIENT_ID="${GOOGLE_OAUTH_CLIENT_ID:-}"
GOOGLE_OAUTH_CLIENT_SECRET="${GOOGLE_OAUTH_CLIENT_SECRET:-}"
GOOGLE_ALLOWED_DOMAIN="${GOOGLE_ALLOWED_DOMAIN:-}"
REQUIRE_OAUTH="${REQUIRE_OAUTH:-true}"
ALLOW_UNAUTHENTICATED="${ALLOW_UNAUTHENTICATED:-true}"

if [ -z "$PROJECT_ID" ]; then
    echo "ERROR: GCP project is not set. Please set PROJECT_ID or configure 'gcloud config set project <PROJECT_ID>'."
    exit 1
fi

PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")

echo "============================================================"
echo " Deploying Google Patents MCP Server to Cloud Run"
echo " Project:        $PROJECT_ID ($PROJECT_NUMBER)"
echo " Region:         $REGION"
echo " Service:        $SERVICE_NAME"
echo " Transport:      streamable-http (/mcp) + sse (/sse)"
echo " OAuth Enabled:  $REQUIRE_OAUTH"
echo " OAuth Client:   ${GOOGLE_OAUTH_CLIENT_ID:-<not set - any valid Google OAuth token accepted>}"
echo "============================================================"

# Navigate to server directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# 1. Enable required GCP APIs (Cloud Run, Cloud Build, Artifact Registry, BigQuery, Discovery Engine)
echo ""
echo "[1/4] Enabling required Google Cloud APIs in ${PROJECT_ID}..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    bigquery.googleapis.com \
    discoveryengine.googleapis.com \
    --project "$PROJECT_ID"

# 2. Ensure Cloud Run & Cloud Build runtime Service Account has required BigQuery & Build permissions
RUNTIME_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
echo ""
echo "[2/4] Granting BigQuery & Cloud Build permissions to ${RUNTIME_SA}..."
for ROLE in \
    "roles/bigquery.jobUser" \
    "roles/bigquery.dataViewer" \
    "roles/cloudbuild.builds.builder" \
    "roles/storage.objectAdmin" \
    "roles/artifactregistry.writer" \
    "roles/logging.logWriter"; do
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${RUNTIME_SA}" \
        --role="$ROLE" \
        --condition=None >/dev/null
done

ENV_VARS="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,MCP_TRANSPORT=streamable-http,REQUIRE_OAUTH=$REQUIRE_OAUTH"
if [ -n "$GOOGLE_OAUTH_CLIENT_ID" ]; then
    ENV_VARS="${ENV_VARS},GOOGLE_OAUTH_CLIENT_ID=${GOOGLE_OAUTH_CLIENT_ID}"
fi
if [ -n "$GOOGLE_OAUTH_CLIENT_SECRET" ]; then
    ENV_VARS="${ENV_VARS},GOOGLE_OAUTH_CLIENT_SECRET=${GOOGLE_OAUTH_CLIENT_SECRET}"
fi
if [ -n "$GOOGLE_ALLOWED_DOMAIN" ]; then
    ENV_VARS="${ENV_VARS},GOOGLE_ALLOWED_DOMAIN=${GOOGLE_ALLOWED_DOMAIN}"
fi
if [ -n "${GOOGLE_PATENTS_COOKIE:-}" ]; then
    ENV_VARS="${ENV_VARS},GOOGLE_PATENTS_COOKIE=${GOOGLE_PATENTS_COOKIE}"
fi
if [ -n "${PATENTS_PROXY_URL:-}" ]; then
    ENV_VARS="${ENV_VARS},PATENTS_PROXY_URL=${PATENTS_PROXY_URL}"
fi

AUTH_FLAG="--no-allow-unauthenticated"
if [ "$ALLOW_UNAUTHENTICATED" = "true" ]; then
    AUTH_FLAG="--allow-unauthenticated"
fi

# 3. Deploy directly using Cloud Build & Cloud Run
echo ""
echo "[3/4] Deploying ${SERVICE_NAME} to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --platform managed \
    "$AUTH_FLAG" \
    --set-env-vars "$ENV_VARS" \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 5 \
    --session-affinity \
    --quiet

# 4. Grant Cloud Run Invoker to the Gemini Enterprise (Discovery Engine) Service Agent
DISCOVERY_ENGINE_SA="service-${PROJECT_NUMBER}@gcp-sa-discoveryengine.iam.gserviceaccount.com"
echo ""
echo "[4/4] Granting roles/run.invoker to Gemini Enterprise Service Agent: ${DISCOVERY_ENGINE_SA} ..."
gcloud beta services identity create --service=discoveryengine.googleapis.com --project="$PROJECT_ID" 2>/dev/null || true
gcloud run services add-iam-policy-binding "$SERVICE_NAME" \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --member="serviceAccount:${DISCOVERY_ENGINE_SA}" \
    --role="roles/run.invoker" >/dev/null || echo "Note: Could not bind ${DISCOVERY_ENGINE_SA} (it will be created automatically when Discovery Engine is first used in the project)."

SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --project "$PROJECT_ID" --region "$REGION" --format 'value(status.url)')

echo ""
echo "============================================================"
echo " Deployment Complete!"
echo " Service URL:             ${SERVICE_URL}"
echo " StreamableHTTP Endpoint: ${SERVICE_URL}/mcp"
echo " SSE Endpoint:            ${SERVICE_URL}/sse"
echo " OAuth Authorize Proxy:   ${SERVICE_URL}/authorize"
echo " OAuth Token Proxy:       ${SERVICE_URL}/token"
echo " Health Check:            ${SERVICE_URL}/healthz"
echo "------------------------------------------------------------"
echo " Gemini Enterprise Datastore Configuration (OAuth 2.0):"
echo " 1. MCP Server URL:               ${SERVICE_URL}/mcp"
echo " 2. Authorization URL:            ${SERVICE_URL}/authorize"
echo " 3. Authorization URL Parameters: &access_type=offline&prompt=consent"
echo " 4. Token URL:                    ${SERVICE_URL}/token"
echo " 5. Client ID:                    ${GOOGLE_OAUTH_CLIENT_ID:-<YOUR_GOOGLE_OAUTH_CLIENT_ID>}"
echo " 6. Client Secret:                <YOUR_GOOGLE_OAUTH_CLIENT_SECRET>"
echo " 7. Scopes:                       openid email profile"
echo " 8. Enable PKCE Support:          Checked"
echo " 9. Use HTTP Basic Authentication: Checked"
echo "============================================================"


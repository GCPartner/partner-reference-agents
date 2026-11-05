#!/usr/bin/env bash
# Deploy Dun & Bradstreet (D&B) MCP Apps Server to Google Cloud Run
# Automatically loads local gitignored `.env.deploy` or `.env` if present.
set -euo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

if [ -f "$DIR/.env.deploy" ]; then
    echo "Loading deployment settings from .env.deploy..."
    set -a
    # shellcheck disable=SC1091
    source "$DIR/.env.deploy"
    set +a
elif [ -f "$DIR/.env" ]; then
    echo "Loading deployment settings from .env..."
    set -a
    # shellcheck disable=SC1091
    source "$DIR/.env"
    set +a
fi

SERVICE_NAME="${SERVICE_NAME:-dnb-mcp-apps-server}"
REGION="${REGION:-us-central1}"
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || echo "")}"
DNB_UPSTREAM_MCP_URL="${DNB_UPSTREAM_MCP_URL:-https://plus.dnb.com/v2/mcp}"
ALLOW_UNAUTHENTICATED="${ALLOW_UNAUTHENTICATED:-true}"

if [ -z "$PROJECT_ID" ]; then
    echo "ERROR: GCP project is not set. Please set PROJECT_ID in .env.deploy or run 'gcloud config set project <PROJECT_ID>'."
    exit 1
fi

PROJECT_NUMBER="${PROJECT_NUMBER:-$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")}"
PUBLIC_BASE_URL="${PUBLIC_BASE_URL:-https://${SERVICE_NAME}-${PROJECT_NUMBER}.${REGION}.run.app}"

echo "============================================================"
echo " Deploying D&B MCP Apps Server to Google Cloud Run"
echo " Project:         $PROJECT_ID ($PROJECT_NUMBER)"
echo " Region:          $REGION"
echo " Service:         $SERVICE_NAME"
echo " Public Base URL: $PUBLIC_BASE_URL"
echo " Upstream D&B:    $DNB_UPSTREAM_MCP_URL"
echo "============================================================"

ENV_VARS="MCP_TRANSPORT=streamable-http,DNB_UPSTREAM_MCP_URL=${DNB_UPSTREAM_MCP_URL},PUBLIC_BASE_URL=${PUBLIC_BASE_URL}"

for VAR_NAME in \
    GOOGLE_OAUTH_CLIENT_ID \
    GOOGLE_OAUTH_CLIENT_SECRET \
    MCP_AUTH_SIGNING_SECRET \
    DNB_MCP_BEARER_TOKEN \
    DNB_GE_PROJECT_NUMBER \
    DNB_GE_CONNECTOR_RESOURCE \
    GOOGLE_ADC_CLIENT_ID \
    GOOGLE_ADC_CLIENT_SECRET \
    GOOGLE_ADC_REFRESH_TOKEN; do
    VAL="${!VAR_NAME:-}"
    if [ -n "$VAL" ]; then
        ENV_VARS="${ENV_VARS},${VAR_NAME}=${VAL}"
    fi
done

AUTH_FLAG="--allow-unauthenticated"
if [ "$ALLOW_UNAUTHENTICATED" != "true" ]; then
    AUTH_FLAG="--no-allow-unauthenticated"
fi

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
    --quiet

SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --project "$PROJECT_ID" --region "$REGION" --format 'value(status.url)')

echo ""
echo "============================================================"
echo " Deployment Complete!"
echo " Service URL:             ${SERVICE_URL}"
echo " StreamableHTTP Endpoint: ${SERVICE_URL}/mcp"
echo " SSE Endpoint:            ${SERVICE_URL}/sse"
echo " OAuth Authorize Proxy:   ${SERVICE_URL}/authorize"
echo " OAuth Token Proxy:       ${SERVICE_URL}/token"
echo " Health Check:            ${SERVICE_URL}/health"
echo "============================================================"

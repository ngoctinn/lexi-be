#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Verify Cognito auth configuration (UserPool triggers + app client + IdPs).

Usage:
  verify-cognito-auth.sh <user-pool-id> <app-client-id> [region]

Examples:
  ./scripts/verify-cognito-auth.sh ap-southeast-1_XXXX 123abc456def ap-southeast-1

Outputs:
  - UserPool LambdaConfig (attached triggers)
  - Identity providers configured in the user pool
  - App client OAuth settings (flows/scopes/callback/logout URLs, supported IdPs)
EOF
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -lt 2 ]]; then
  usage
  exit 2
fi

USER_POOL_ID="$1"
CLIENT_ID="$2"
REGION="${3:-${AWS_REGION:-}}"

if [[ -z "${REGION}" ]]; then
  echo "ERROR: region not provided. Pass as 3rd arg or set AWS_REGION." >&2
  exit 2
fi

echo "=== User pool: LambdaConfig (attached triggers) ==="
aws cognito-idp describe-user-pool \
  --user-pool-id "$USER_POOL_ID" \
  --region "$REGION" \
  --query 'UserPool.LambdaConfig' \
  --output json

echo

echo "=== User pool: Identity providers ==="
aws cognito-idp list-identity-providers \
  --user-pool-id "$USER_POOL_ID" \
  --region "$REGION" \
  --max-results 60 \
  --query 'Providers[].{Name:ProviderName,Type:ProviderType}' \
  --output table

echo

echo "=== App client: OAuth + supported IdPs ==="
aws cognito-idp describe-user-pool-client \
  --user-pool-id "$USER_POOL_ID" \
  --client-id "$CLIENT_ID" \
  --region "$REGION" \
  --query '{
    ClientName: UserPoolClient.ClientName,
    SupportedIdentityProviders: UserPoolClient.SupportedIdentityProviders,
    AllowedOAuthFlowsUserPoolClient: UserPoolClient.AllowedOAuthFlowsUserPoolClient,
    AllowedOAuthFlows: UserPoolClient.AllowedOAuthFlows,
    AllowedOAuthScopes: UserPoolClient.AllowedOAuthScopes,
    CallbackURLs: UserPoolClient.CallbackURLs,
    LogoutURLs: UserPoolClient.LogoutURLs
  }' \
  --output json

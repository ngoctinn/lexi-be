# Verify Cognito triggers (manual workflow)

This repo deploys Cognito triggers in a separate SAM stack and attaches them to the User Pool with a manual step. Configuration drift is the most common reason the triggers "don’t work".

## What AWS expects

- Cognito triggers must return the _same_ `event` object.
- Federated users (Google) invoke:
  - First sign-in: `PreSignUp_ExternalProvider` + `PostConfirmation_ConfirmSignUp`
  - Subsequent sign-ins: `PostAuthentication_Authentication`

Reference: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-working-with-lambda-triggers.html

## Quick verification (AWS CLI)

Run:

```bash
./scripts/verify-cognito-auth.sh <user-pool-id> <app-client-id> <region>
```

You want to see:

- `LambdaConfig.PreSignUp`, `LambdaConfig.PostConfirmation`, `LambdaConfig.PostAuthentication` are present and point to the expected Lambda ARNs.
- Identity provider list includes `Google`.
- App client shows `SupportedIdentityProviders` includes `Google` and `COGNITO`.

## If triggers are missing

Re-attach triggers (from the `auth-lambdas` stack output `AttachTriggersCommand`) and re-run the verification.

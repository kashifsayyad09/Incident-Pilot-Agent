# AWS permissions

IncidentPilot never changes AWS. Give it only what it uses.

| File | Purpose |
|---|---|
| `iam/incidentpilot-readonly-policy.json` | The nine read-only API calls the diagnostic tools make |
| `iam/bedrock-invoke-policy.json` | Invoke one Bedrock model for the analysis |
| `cloudformation/incidentpilot-role.yaml` | Both as a role you can assume (**not deployed or tested by the authors**; review first) |

Replace the `REGION`, `ACCOUNT_ID`, `LOG_GROUP_NAME`, `MODEL_ID`, `INFERENCE_PROFILE_ID`
placeholders. Prefer an assumed role or SSO profile over long-lived access keys.

Two layers enforce read-only: this IAM policy, and an in-process allowlist
(`backend/app/tools/aws_guard.py`) that refuses any other API call. A test checks that the
policy and the allowlist list exactly the same actions and that no action is a write.

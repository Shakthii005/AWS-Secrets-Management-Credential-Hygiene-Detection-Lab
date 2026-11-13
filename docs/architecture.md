# Architecture — AWS Secrets Management & Credential-Hygiene Detection Lab

This is the implemented single-account lab architecture. It separates Mumbai secret/Lambda detections from N. Virginia IAM global-service event detection.

![Architecture diagram](architecture.png)

## Editable source files

- `architecture.svg` — vector diagram source; edit labels and positions in `render_architecture.py`.
- `architecture.png` — rendered diagram for GitHub README and portfolio presentations.
- `architecture.dot` — original Graphviz source draft.
- `architecture.mmd` — Mermaid version for Markdown renderers that support Mermaid.
- `render_architecture.py` — script used to render the PNG/SVG.

## Key flows

1. **Application retrieval:** the Boto3 example client uses `SecretsAppReader` to call `GetSecretValue` for the one lab secret. Its output redacts the password.
2. **Rotation:** Secrets Manager invokes `secrets-lab-rotation`. The handler executes the four rotation stages and updates the secret version in Secrets Manager. Backend update and authentication are simulated; no database is connected.
3. **Audit:** the multi-Region CloudTrail management trail records API activity and delivers audit logs to S3.
4. **Mumbai detections:** EventBridge in `ap-south-1` handles the secret-version label update, denied secret-read, denied secret-modification, and Lambda configuration-change rules. Matching events publish to `secrets-security-alerts` and its confirmed email subscription.
5. **IAM detections:** IAM is a global service. The observed role-policy management event was recorded with `awsRegion=us-east-1`; EventBridge in `us-east-1` evaluates `secrets-lab-iam-role-change`, then publishes to `secrets-security-alerts-iam` and its confirmed email subscription.

## Validation evidence to capture

For a public portfolio, capture sanitized screenshots of:

- Secrets Manager secret metadata and version stages (never reveal secret values).
- Lambda configuration and successful rotation execution logs, with account identifiers redacted.
- CloudTrail records for a successful secret-version event and denied `GetSecretValue` / `PutSecretValue` calls.
- Email notifications for secret-version change, denied read, denied modification, Lambda configuration change, and IAM role policy change/deletion.
- EventBridge rule names, states and SNS targets in each Region.
- Confirmed SNS subscriptions, with email addresses obscured.
- CloudWatch metrics for successful rule matching/invocation. Optionally document the failed SNS invocation and its resolution as a troubleshooting case study.

Never publish secret values, credentials, raw `.env` contents, unredacted CloudTrail identities, personal email addresses, subscription ARNs, or account-specific ARNs. Replace them with placeholders in screenshots and sample files.

## Accuracy notes

- This is one AWS account, not a multi-account Organizations deployment.
- The rotation workflow updates the Secrets Manager secret version. It does not connect to, update, or authenticate against a real database.
- The supplied project tree showed an empty `terraform/` directory; this diagram does not imply Terraform-managed deployment.
- The IAM detection rule is regionalized in `us-east-1`; do not depict it as a Mumbai EventBridge rule.

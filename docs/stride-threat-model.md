# STRIDE Threat Model — AWS Secrets Management & Credential-Hygiene Detection Lab

## 1. Purpose and scope

This document records the STRIDE threat analysis for the Secrets Management & Credential-Hygiene Detection Lab. The project demonstrates secret storage, least-privilege access, synthetic secret rotation, AWS management-event auditing, and email alerting.

**Environment scope**

- One AWS account: `121592733055` (use a redacted account identifier in public screenshots and publications).
- Mumbai (`ap-south-1`): AWS Secrets Manager, the rotation Lambda function, CloudTrail management trail, and secret/Lambda EventBridge detections.
- N. Virginia (`us-east-1`): EventBridge detection for IAM global-service role-policy changes and a regional SNS topic.
- Primary secret: `lab/database/credentials`.
- Rotation function: `secrets-lab-rotation`.
- Rotation execution role: `SecretsRotationLambdaRole`.
- Application identity: `SecretsAppReader`.
- Operator identity: `SecretsLabOperator` through IAM Identity Center.

This analysis covers the implemented lab configuration. It is not a claim of production certification or a complete enterprise threat assessment.

## 2. Assets and trust boundaries

| Asset | Security value | Main trust boundary |
|---|---|---|
| Secrets Manager secret value | Synthetic database credentials | Secrets Manager API and IAM authorization |
| Secret versions and staging labels | Integrity and recovery of the current credential version | Secrets Manager version/label operations |
| `SecretsAppReader` identity | Limits application access to the intended secret | IAM Identity Center permission set / assumed role |
| `SecretsLabOperator` identity | Administrative lab operations | IAM Identity Center permission set / assumed role |
| `SecretsRotationLambdaRole` | Controls what rotation code can do | Lambda execution-role trust and permissions |
| `secrets-lab-rotation` Lambda | Orchestrates the four rotation stages | Lambda service invocation and function configuration |
| CloudTrail trail and S3 archive | Audit evidence | Account-level logging configuration and S3 access policy |
| EventBridge rules | Detection of selected management events | Event pattern, event-bus Region, and target configuration |
| SNS topics and email subscriptions | Security notification delivery | SNS topic resource policy and subscription confirmation |
| Local repository | Source code, patterns, samples, and evidence | Developer workstation and Git repository controls |

## 3. STRIDE analysis

### S — Spoofing

**Threat:** An attacker obtains or reuses an operator or application session and makes AWS API calls while appearing to be a legitimate principal.

**Potential impact:** Unauthorized secret reads, secret changes, Lambda modifications, or IAM changes under a compromised identity.

**Implemented controls and evidence**

- IAM Identity Center profiles are used for CLI access (`secrets-lab` and `secrets-reader`) rather than embedding AWS access keys in application source.
- The application-reader permission set is restricted to `GetSecretValue` and `DescribeSecret` for the lab secret ARN.
- CloudTrail records the principal and API activity for investigations.

**Residual risk / follow-up**

- A stolen authenticated session can still be abused until it expires or is revoked. Enforce MFA and appropriate session controls in the account's Identity Center configuration; do not claim these are enabled unless separately verified.
- Review Identity Center assignments and remove unused users or permission-set assignments.

**Assessment:** Partially mitigated. Identity authorization is implemented; session-compromise controls require separate account-level verification.

### T — Tampering

**Threat:** An attacker attempts to alter the secret value, version labels, resource policy, Lambda code/configuration, or rotation role permissions.

**Potential impact:** Applications receive an attacker-controlled credential; rotation behavior is modified; or the Lambda execution role gains unintended permissions.

**Implemented controls and evidence**

- `SecretsAppReader` does not have `PutSecretValue`; a real `PutSecretValue` attempt returned `AccessDenied`.
- EventBridge detects selected denied Secrets Manager modification events, including `PutSecretValue` and policy/version operations, using the observed CloudTrail event shape.
- The Lambda execution role is scoped to the lab secret ARN for its Secrets Manager rotation operations.
- A real Lambda configuration change generated an email alert.
- A temporary inline policy added to `SecretsRotationLambdaRole` generated an IAM role-change email alert; the temporary policy was then deleted, and the deletion alert was received.

**Residual risk / follow-up**

- EventBridge rules detect selected events; they do not prevent an authorized principal from making a change. Prevention depends on IAM permissions and any applicable organizational controls.
- Review event patterns periodically against real CloudTrail events. Patterns that require fields omitted from denied events can fail to match.
- The IAM global-service detection is deployed in `us-east-1`; Lambda and secret detections are in `ap-south-1`.

**Assessment:** Prevention and detection are demonstrated for selected paths. Coverage is limited to the named secret, function, role, event names, account, and Regions in the rules.

### R — Repudiation

**Threat:** A user or attacker denies performing a secret read, secret update, policy change, or Lambda configuration change.

**Potential impact:** Security investigations cannot reliably attribute actions or reconstruct what happened.

**Implemented controls and evidence**

- A multi-Region CloudTrail management-event trail is configured and logging.
- CloudTrail Event History was used to retrieve actual `GetSecretValue`, denied `PutSecretValue`, `PutRolePolicy`, and related management events.
- The trail delivers log files to the lab S3 archive bucket, and log file validation is enabled.

**Residual risk / follow-up**

- Log-file validation supports integrity checking but is not the same as S3 Object Lock or immutable retention.
- Review S3 bucket policy, access logging, lifecycle, retention, and administrative access. Consider Object Lock only if the project is extended to a formal immutable audit archive.
- Confirm trail logging and delivery health periodically.

**Assessment:** Auditability is demonstrated. Strong immutability and long-term retention have not been established by this lab.

### I — Information Disclosure

**Threat:** An unauthorized user or process reads secret values, credentials are committed to source control, or logs/screenshots expose sensitive values or identifiers.

**Potential impact:** Credential theft, unauthorized access to dependent systems, or leakage of account and identity details.

**Implemented controls and evidence**

- Synthetic database connection details are stored in Secrets Manager rather than being treated as production credentials in application code.
- `SecretsAppReader` is restricted to read the exact lab secret; it cannot list or modify secrets under the tested permission set.
- The application example redacts the password when displaying secret metadata.
- `.gitignore` excludes `.env` files; `.env.example` provides safe placeholders.
- The secret uses the AWS-managed Secrets Manager KMS key (`aws/secretsmanager`).

**Residual risk / follow-up**

- The lab uses synthetic credentials and has no real database. Do not place production credentials in this repository or screenshots.
- Before publishing, inspect `.env`, terminal output, CloudTrail event JSON, screenshots, and Git history. Redact account IDs, full ARNs, email addresses, request IDs, and any secret values where practical.
- Avoid logging `SecretString` or passwords. Keep the public sample files synthetic.

**Assessment:** Least-privilege read access and repository hygiene are demonstrated. Public-release review is still required.

### D — Denial of Service

**Threat:** An attacker or misconfigured principal deletes a secret, cancels rotation, disrupts Lambda configuration, or otherwise prevents an application from retrieving a usable credential.

**Potential impact:** Application authentication failures or interruption of dependent workloads.

**Implemented controls and evidence**

- Secret read and modification permissions are separated between application-reader and operator identities.
- CloudTrail records secret and Lambda management operations.
- EventBridge patterns include selected secret lifecycle and modification events, and notifications are sent through SNS.
- Secret version staging (`AWSCURRENT` and `AWSPREVIOUS`) provides version history for the lab workflow.

**Residual risk / follow-up**

- The lab does not demonstrate a production recovery-time objective, multi-Region secret replication, or an application failover strategy.
- Rotation is currently disabled after testing. This was intentional to avoid unattended lab activity and cost; it must be explicitly re-enabled and tested before any future demonstration that requires scheduled rotation.
- Confirm deletion recovery settings and define a recovery procedure before using this pattern for production workloads.

**Assessment:** Selected lifecycle actions are monitored. Resilience and recovery objectives are not fully implemented or tested.

### E — Elevation of Privilege

**Threat:** An attacker modifies the rotation role trust policy, attaches a broader managed policy, inserts an inline policy, changes a Lambda function, or exploits `iam:PassRole` to execute code with a more privileged role.

**Potential impact:** Code running in Lambda gains access beyond the intended secret or uses the role to access other AWS resources.

**Implemented controls and evidence**

- `SecretsRotationLambdaRole` is used as the function execution role and its Secrets Manager permissions are scoped to the lab secret ARN.
- The IAM detection rule in `us-east-1` monitors selected role-policy and trust-policy change operations for `SecretsRotationLambdaRole`.
- A real `PutRolePolicy` event and a subsequent `DeleteRolePolicy` event were generated and both produced email alerts.
- Lambda configuration changes to `secrets-lab-rotation` are monitored in Mumbai.

**Residual risk / follow-up**

- The current event pattern focuses on one role and selected event names. Extend coverage deliberately for `iam:PassRole`, role creation/deletion, managed-policy changes, policy-version changes, and other roles if the architecture expands.
- Detection is not prevention. Restrict who can update the role, pass it to services, or modify the Lambda function.
- Review role trust policy and effective permissions for privilege-escalation paths.

**Assessment:** Selected IAM and Lambda privilege-change paths are live-tested. Broader privilege-escalation coverage remains future work.

## 4. Validation evidence matrix

| Test scenario | Expected control behavior | Observed result | Status |
|---|---|---|---|
| Application identity calls `GetSecretValue` for the permitted lab secret | Read is permitted | Reader retrieved the synthetic secret; application output redacts the password | Verified |
| Application identity calls `PutSecretValue` | IAM denies modification | CloudTrail recorded `AccessDenied`; corrected EventBridge rule matched and email was received | Verified |
| Application identity attempts unauthorized secret read | IAM denies access | CloudTrail recorded `AccessDenied`; EventBridge/SNS email was received | Verified |
| Secret version label changes | EventBridge detects `AWSCURRENT` label update | Email notification was received | Verified |
| Lambda configuration description changes | EventBridge detects function configuration change | Email notification was received; original empty description restored | Verified |
| Inline policy added to `SecretsRotationLambdaRole` | IAM global event is detected in `us-east-1` | `PutRolePolicy` email received | Verified |
| Temporary inline policy removed from `SecretsRotationLambdaRole` | IAM global event is detected in `us-east-1` | `DeleteRolePolicy` email received | Verified |
| Four-stage Lambda rotation | Secret version progresses through rotation stages | AWSPENDING creation, simulated `setSecret`, synthetic `testSecret`, and AWSCURRENT promotion observed in Lambda logs | Verified with simulation limitation |

Store sanitized screenshots in `docs/screenshots/` and reference them from the README. Do not commit unredacted event payloads or secret values.

## 5. Important implementation limitations

1. **No live database is connected.** The Lambda `setSecret` and `testSecret` stages are simulations. The workflow updates Secrets Manager versions, but it does not update or authenticate against a database.
2. **Rotation is disabled after the lab test.** The secret's rotation configuration was disabled after the successful demonstration. Do not describe scheduled rotation as currently running.
3. **Detection is scoped.** The rules monitor selected event names, a particular secret/function/role, and the Regions configured in the rules. They are not a complete account-wide threat-detection platform.
4. **Email alerting is asynchronous.** CloudTrail, EventBridge, SNS, and email delivery can be delayed. Email is not a guaranteed real-time response mechanism.
5. **SNS encryption configuration differs by Region.** The Mumbai alert topic had server-side encryption disabled after troubleshooting the EventBridge-to-SNS delivery failure. The N. Virginia IAM alert topic was created without server-side encryption for this lab. Revisit encryption design before production use; a customer-managed KMS key and appropriate key policy are required when encrypting an SNS topic targeted by EventBridge.
6. **Terraform is not implemented.** The repository's `terraform/` directory was empty in the captured project tree. Do not claim Terraform-based deployment until code is added and applied.

## 6. Recommended future improvements

- Connect a disposable test database and implement actual credential update and authentication checks in the rotation stages.
- Add automated tests for every EventBridge pattern using sanitized real CloudTrail event fixtures.
- Expand IAM coverage to policy-version changes, role trust changes, `iam:PassRole`, role lifecycle operations, and additional sensitive roles.
- Add operational alerting for EventBridge failed invocations, SNS delivery failures, CloudTrail delivery health, and rotation failures.
- Define retention, recovery, and immutable-audit requirements for CloudTrail logs.
- Add infrastructure as code for the complete multi-Region deployment and test teardown.
- Add a runbook for incident triage, secret rollback, role-policy review, and alert acknowledgement.


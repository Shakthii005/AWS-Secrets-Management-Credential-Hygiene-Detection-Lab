
# Security Audit Findings

This document records four controlled security incidents observed during live AWS testing. Personal identity details and account-specific identifiers are omitted.

## Finding 1 — Denied Secret Retrieval

**What fired:** The restricted application-reader identity attempted to retrieve a secret without effective permission. The denied-secret-read EventBridge rule matched the event and SNS delivered an email alert.

**What CloudTrail showed:** A `GetSecretValue` API event from `secretsmanager.amazonaws.com` in `ap-south-1`, with an `AccessDenied` error.

**Who did it:** The request was made using the `SecretsAppReader` IAM Identity Center permission set.

**Conclusion:** IAM prevented unauthorized retrieval. CloudTrail recorded the attempt, and EventBridge and SNS provided detection and notification.

## Finding 2 — Denied Secret Modification

**What fired:** The restricted reader attempted `PutSecretValue`. IAM denied the operation. After correcting the EventBridge pattern to account for the missing `requestParameters.secretId` field, the rule matched and SNS delivered an email alert.

**What CloudTrail showed:** A `PutSecretValue` management event in `ap-south-1` with an `AccessDenied` error. The observed denied event did not contain the expected secret identifier in its request parameters.

**Who did it:** The operation was attempted using the restricted `SecretsAppReader` identity.

**Conclusion:** Least-privilege IAM prevented the secret modification. Inspecting the actual CloudTrail event structure was necessary to correct the detection rule.

## Finding 3 — Lambda Configuration Change

**What fired:** During a controlled detection test, the description of `secrets-lab-rotation` was temporarily changed. The Lambda configuration-change EventBridge rule matched the event, and SNS delivered an email alert. The original description was restored after testing.

**What CloudTrail showed:** An `UpdateFunctionConfiguration` API event for the rotation Lambda in `ap-south-1`.

**Who did it:** The change was performed by the authorized lab operator session for detection testing.

**Conclusion:** Configuration changes to a security-critical Lambda function can be detected and reported. This was a controlled test, not an actual compromise.

## Finding 4 — IAM Role Policy Addition and Deletion

**What fired:** A temporary inline policy named `TemporaryDetectionTestOnly` was added to `SecretsRotationLambdaRole` and subsequently deleted. The dedicated N. Virginia EventBridge rule generated email alerts for both operations.

**What CloudTrail showed:** Successful `PutRolePolicy` and `DeleteRolePolicy` management events for `SecretsRotationLambdaRole`, recorded in `us-east-1`.

**Who did it:** Both operations were performed by the authorized lab operator during controlled detection testing.

**Conclusion:** Changes to a Lambda execution role can affect the function's privileges. Monitoring global IAM events in `us-east-1` successfully detected both policy addition and removal.

## Scope and Limitations

These findings represent controlled lab tests, not confirmed malicious activity.

CloudTrail provides the audit records, EventBridge evaluates configured event patterns, and SNS delivers notifications.

The denied secret-modification rule does not filter by secret ID because that field was absent from the denied CloudTrail event observed during testing. Review this detection scope before reusing the pattern in production.


# Secrets Management - Audit Findings

## Finding 1: Authorized Secret Retrieval

**Service:** AWS Secrets Manager

**Event:** GetSecretValue

**Account:** 121592733055

**Identity:** shakthivel-cloudsec

**Permission Set:** SecretsAppReader

**Secret:** lab/database/credentials

**Authentication:** IAM Identity Center

### Security Analysis

CloudTrail recorded the GetSecretValue API operation.

The sessionIssuer field identified the
SecretsAppReader permission set.

The onBehalfOf field provided the originating
IAM Identity Center user identifier.

### Security Result

The application successfully retrieved its
authorized synthetic database credential.

Attempts to enumerate all secrets were denied.

### Conclusion

Resource-specific IAM permissions reduced
the application's access to the intended secret.

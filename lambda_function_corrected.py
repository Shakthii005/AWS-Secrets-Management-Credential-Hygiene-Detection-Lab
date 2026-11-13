import json
import logging
import os
import secrets
import string

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# This function is intentionally restricted to one Secrets Manager secret.
SECRET_ARN = os.environ.get("SECRET_ARN", "").strip()
if not SECRET_ARN:
    raise RuntimeError("Required environment variable SECRET_ARN is not set.")

AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")
secrets_manager = boto3.client("secretsmanager", region_name=AWS_REGION)

REQUIRED_FIELDS = {"username", "password", "host", "port", "database"}
PASSWORD_ALPHABET = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"


def describe_secret():
    """Return metadata for the configured secret."""
    return secrets_manager.describe_secret(SecretId=SECRET_ARN)


def get_secret(version_id=None, version_stage="AWSCURRENT"):
    """Retrieve one JSON secret version without logging its contents."""
    request = {
        "SecretId": SECRET_ARN,
        "VersionStage": version_stage,
    }
    if version_id is not None:
        request["VersionId"] = version_id

    response = secrets_manager.get_secret_value(**request)
    secret_string = response.get("SecretString")
    if not secret_string:
        raise ValueError("SecretString is missing or empty.")

    value = json.loads(secret_string)
    if not isinstance(value, dict):
        raise ValueError("SecretString must be a JSON object.")
    return value


def validate_secret_shape(value):
    """Validate the JSON structure used by this synthetic lab."""
    missing = REQUIRED_FIELDS.difference(value.keys())
    if missing:
        raise ValueError(
            "Secret is missing required fields: "
            + ", ".join(sorted(missing))
        )

    password = value.get("password")
    if not isinstance(password, str) or not password:
        raise ValueError("Secret password must be a non-empty string.")


def validate_same_resource(current, pending):
    """Prevent the rotation from changing the represented database identity."""
    for field in ("username", "host", "port", "database"):
        if current.get(field) != pending.get(field):
            raise ValueError(
                f"Rotation cannot change target field: {field}"
            )


def generate_password(length=32):
    """Generate a cryptographically random synthetic password."""
    return "".join(
        secrets.choice(PASSWORD_ALPHABET)
        for _ in range(length)
    )


def create_secret(token, rotation_token=None):
    """
    Stage 1: create the AWSPENDING value.

    AWS may call createSecret with a token that is not yet in
    VersionIdsToStages. It may also retry a token whose AWSPENDING
    version exists but whose SecretString was not written. Both are handled.
    """
    metadata = describe_secret()
    versions = metadata.get("VersionIdsToStages", {})

    current_version_id = next(
        (
            version_id
            for version_id, stages in versions.items()
            if "AWSCURRENT" in stages
        ),
        None,
    )
    if not current_version_id:
        raise ValueError("No AWSCURRENT version was found.")

    # AWSPENDING on the current version is an acceptable post-rotation state.
    # A different non-current AWSPENDING version indicates another unfinished
    # rotation, so do not overwrite it.
    for version_id, stages in versions.items():
        if (
            version_id not in (token, current_version_id)
            and "AWSPENDING" in stages
        ):
            raise ValueError(
                "A different non-current AWSPENDING version exists. "
                "Resolve that rotation before continuing."
            )

    current = get_secret(version_stage="AWSCURRENT")
    validate_secret_shape(current)

    # Idempotency: if this exact token already has a retrievable pending value,
    # reuse it. If the token is absent, or its staged version has no value yet,
    # create the value using the same token.
    if token in versions:
        token_stages = versions[token]

        if "AWSCURRENT" in token_stages:
            logger.info("This request token is already AWSCURRENT.")
            return

        if "AWSPENDING" not in token_stages:
            raise ValueError(
                "Request token exists but is not staged as AWSPENDING."
            )

        try:
            pending_existing = get_secret(
                version_id=token,
                version_stage="AWSPENDING",
            )
            validate_secret_shape(pending_existing)
            validate_same_resource(current, pending_existing)
            logger.info(
                "AWSPENDING value already exists for this request token."
            )
            return
        except secrets_manager.exceptions.ResourceNotFoundException:
            logger.info(
                "AWSPENDING version has no value yet; creating its value."
            )

    pending = current.copy()
    pending["password"] = generate_password()

    put_request = {
        "SecretId": SECRET_ARN,
        "ClientRequestToken": token,
        "SecretString": json.dumps(pending),
        "VersionStages": ["AWSPENDING"],
    }

    # AWS supplies RotationToken for assumed-role/cross-account rotation.
    if rotation_token:
        put_request["RotationToken"] = rotation_token

    secrets_manager.put_secret_value(**put_request)
    logger.info("Stage 1 complete: new AWSPENDING value stored.")


def set_secret(token):
    """
    Stage 2: validate the pending credential and simulate the backend update.

    LAB SIMULATION ONLY: no real database/service is connected or modified.
    """
    current = get_secret(version_stage="AWSCURRENT")
    pending = get_secret(
        version_id=token,
        version_stage="AWSPENDING",
    )

    validate_secret_shape(current)
    validate_secret_shape(pending)
    validate_same_resource(current, pending)

    if pending["password"] == current["password"]:
        raise ValueError("Pending password must differ from current password.")

    logger.warning(
        "SIMULATION ONLY: no live database/service credential was changed."
    )
    logger.info("Stage 2 complete: simulated backend checks passed.")


def test_secret(token):
    """
    Stage 3: validate the pending synthetic credential.

    LAB SIMULATION ONLY: this does not authenticate to a real database.
    """
    current = get_secret(version_stage="AWSCURRENT")
    pending = get_secret(
        version_id=token,
        version_stage="AWSPENDING",
    )

    validate_secret_shape(current)
    validate_secret_shape(pending)
    validate_same_resource(current, pending)

    if len(pending["password"]) < 20:
        raise ValueError("Pending password is shorter than 20 characters.")

    if pending["password"] == current["password"]:
        raise ValueError("Pending password matches current password.")

    logger.warning(
        "SIMULATION ONLY: no live database/service authentication was performed."
    )
    logger.info("Stage 3 complete: synthetic credential validation passed.")


def finish_secret(token):
    """Stage 4: move AWSCURRENT to the pending version."""
    metadata = describe_secret()
    versions = metadata.get("VersionIdsToStages", {})
    token_stages = versions.get(token, [])

    # Idempotent retry after a successful promotion.
    if "AWSCURRENT" in token_stages:
        logger.info("This version is already AWSCURRENT.")
        return

    if "AWSPENDING" not in token_stages:
        raise ValueError("Requested version is not staged as AWSPENDING.")

    current_version_id = next(
        (
            version_id
            for version_id, stages in versions.items()
            if "AWSCURRENT" in stages
        ),
        None,
    )
    if not current_version_id:
        raise ValueError("No AWSCURRENT version was found.")

    # Moving AWSCURRENT to this version also removes AWSPENDING from it
    # as part of the same Secrets Manager operation.
    secrets_manager.update_secret_version_stage(
        SecretId=SECRET_ARN,
        VersionStage="AWSCURRENT",
        MoveToVersionId=token,
        RemoveFromVersionId=current_version_id,
    )

    logger.info("Stage 4 complete: new version promoted to AWSCURRENT.")


def lambda_handler(event, context):
    """Handle AWS Secrets Manager createSecret/setSecret/testSecret/finishSecret."""
    logger.info("Received rotation request.")

    try:
        secret_id = event["SecretId"]
        token = event["ClientRequestToken"]
        step = event["Step"]
        rotation_token = event.get("RotationToken")

        if secret_id != SECRET_ARN:
            raise ValueError("Secret ARN is not allowed.")

        if not isinstance(token, str) or not token:
            raise ValueError("ClientRequestToken is missing or invalid.")

        valid_steps = {
            "createSecret",
            "setSecret",
            "testSecret",
            "finishSecret",
        }
        if step not in valid_steps:
            raise ValueError("Invalid rotation step.")

        metadata = describe_secret()
        if not metadata.get("RotationEnabled", False):
            raise ValueError("Rotation is not enabled for this secret.")

        versions = metadata.get("VersionIdsToStages", {})
        token_stages = versions.get(token, [])

        # createSecret is allowed to receive a token not yet present in
        # VersionIdsToStages. It creates the pending value using that token.
        if step == "createSecret":
            if "AWSCURRENT" in token_stages:
                logger.info("Request token is already AWSCURRENT.")
                return {
                    "statusCode": 200,
                    "step": step,
                    "status": "SUCCESS",
                }

            if token in versions and "AWSPENDING" not in token_stages:
                raise ValueError(
                    "Request token exists but is not staged as AWSPENDING."
                )

            create_secret(token, rotation_token)

        else:
            # The remaining three steps require a pending version created
            # by createSecret.
            if token not in versions or "AWSPENDING" not in token_stages:
                if "AWSCURRENT" in token_stages:
                    logger.info("Request token is already AWSCURRENT.")
                    return {
                        "statusCode": 200,
                        "step": step,
                        "status": "SUCCESS",
                    }
                raise ValueError(
                    "Request token is not staged as AWSPENDING."
                )

            if step == "setSecret":
                set_secret(token)
            elif step == "testSecret":
                test_secret(token)
            elif step == "finishSecret":
                finish_secret(token)

        return {
            "statusCode": 200,
            "step": step,
            "status": "SUCCESS",
        }

    except ClientError:
        logger.exception("AWS API error during rotation.")
        raise
    except (KeyError, TypeError, ValueError):
        logger.exception("Invalid rotation request or secret state.")
        raise
    except Exception:
        logger.exception("Unexpected rotation failure.")
        raise

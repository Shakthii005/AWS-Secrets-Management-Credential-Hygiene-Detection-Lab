
import json
import logging
import sys

import boto3
from botocore.exceptions import ClientError, BotoCoreError

# Configuration
AWS_PROFILE = "secrets-reader"
AWS_REGION = "ap-south-1"
SECRET_NAME = "lab/database/credentials"

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)


def get_db_credentials() -> dict:
    """Retrieve database credentials from AWS Secrets Manager."""

    try:
        session = boto3.Session(
            profile_name=AWS_PROFILE,
            region_name=AWS_REGION
        )

        client = session.client("secretsmanager")

        response = client.get_secret_value(
            SecretId=SECRET_NAME
        )

        secret_string = response.get("SecretString")

        if not secret_string:
            raise ValueError("SecretString is missing or empty.")

        credentials = json.loads(secret_string)

        required_fields = {
            "username",
            "password",
            "host",
            "port",
            "database"
        }

        if not required_fields.issubset(credentials):
            raise ValueError("Secret is missing required fields.")

        logger.info("Database secret retrieved successfully.")
        return credentials

    except ClientError as error:
        code = error.response.get("Error", {}).get("Code", "Unknown")
        logger.error("AWS Secrets Manager request failed: %s", code)
        raise

    except (BotoCoreError, ValueError, json.JSONDecodeError):
        logger.exception("Could not process the database secret.")
        raise


def main() -> None:
    try:
        credentials = get_db_credentials()

        # Demonstrate successful retrieval without exposing secrets.
        print("\nSecure retrieval successful.")
        print("Database host:", credentials["host"])
        print("Database username:", credentials["username"])
        print("Database name:", credentials["database"])
        print("Database password: [REDACTED]")
        print("API credentials: [NOT REQUESTED]")

    except (ClientError, BotoCoreError, ValueError):
        sys.exit(1)


if __name__ == "__main__":
    main()

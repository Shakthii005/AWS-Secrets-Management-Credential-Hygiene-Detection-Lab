
import json
import getpass
import sys

import boto3
from botocore.exceptions import ClientError, BotoCoreError

AWS_PROFILE = "secrets-lab"
AWS_REGION = "ap-south-1"
SECRET_NAME = "lab/database/credentials"


def rotate_secret():
    session = boto3.Session(
        profile_name=AWS_PROFILE,
        region_name=AWS_REGION
    )

    client = session.client("secretsmanager")

    try:
        # Retrieve the existing secret using the admin profile.
        response = client.get_secret_value(
            SecretId=SECRET_NAME
        )

        credentials = json.loads(response["SecretString"])

        # Collect the new password without displaying it.
        new_password = getpass.getpass("Enter new synthetic password: ")
        confirm_password = getpass.getpass("Confirm new password: ")

        if len(new_password) < 16:
            raise ValueError("Password must contain at least 16 characters.")

        if new_password != confirm_password:
            raise ValueError("Passwords do not match.")

        if new_password == credentials["password"]:
            raise ValueError("New password must differ from the old one.")

        # Update the password in the secret document.
        credentials["password"] = new_password

        # Create a new secret version.
        result = client.put_secret_value(
            SecretId=SECRET_NAME,
            SecretString=json.dumps(credentials)
        )

        print("\nSecret rotation completed successfully.")
        print("Secret name:", SECRET_NAME)
        print("New version ID:", result["VersionId"])
        print("Current version staging label: AWSCURRENT")
        print("Password: [REDACTED]")

    except (ClientError, BotoCoreError, ValueError, KeyError, json.JSONDecodeError) as error:
        print("Secret rotation failed:", str(error))
        sys.exit(1)


if __name__ == "__main__":
    rotate_secret()

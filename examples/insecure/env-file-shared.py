
# INSECURE EXAMPLE
# Demonstrates credentials stored in a .env file.

import os
from pathlib import Path
from dotenv import load_dotenv

# Load the .env file from this script's directory.
env_path = Path(__file__).with_name(".env")
load_dotenv(dotenv_path=env_path)

DB_HOST = os.getenv("DB_HOST")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
API_KEY = os.getenv("API_KEY")

def connect_to_database():
    print("Connecting to:", DB_HOST)
    print("Username:", DB_USERNAME)

    if DB_PASSWORD:
        print("Database password loaded successfully.")

    if API_KEY:
        print("API key loaded successfully.")

if __name__ == "__main__":
    connect_to_database()

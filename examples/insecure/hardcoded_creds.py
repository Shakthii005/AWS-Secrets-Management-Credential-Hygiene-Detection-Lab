
# INSECURE EXAMPLE
# Never store real credentials this way.

DB_HOST = "database.example.com"
DB_USERNAME = "admin"
DB_PASSWORD = "FakePassword123!"

API_KEY = "FAKE_API_KEY_123456"

def connect_to_database():
    print("Connecting to:", DB_HOST)
    print("Username:", DB_USERNAME)

    # Password is directly embedded in source code.
    # Anyone with repository access can read it.

if __name__ == "__main__":
    connect_to_database()

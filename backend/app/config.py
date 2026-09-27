import os

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

AUTHORIZED_ADMINS = [
    "support@apexingoodcompany.co.uk",
    "business@apexingoodcompany.co.uk",
]
SUPER_USER_EMAIL = "support@apexingoodcompany.co.uk"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./assets.db")
DEFAULT_LOCATION = os.getenv("DEFAULT_LOCATION", "APEX HUB")

USER_INACTIVITY_DAYS = int(os.getenv("USER_INACTIVITY_DAYS", "30"))

import firebase_admin
from firebase_admin import credentials, db
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv()

# Initialize Firebase with error handling
try:
    logger.info("Initializing Firebase...")
    if not os.path.exists('app/core/firebase_credentials.json'):
        raise FileNotFoundError("Firebase credentials file not found")

    cred = credentials.Certificate('app/core/firebase_credentials.json')
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://spotlight-2e6e9-default-rtdb.europe-west1.firebasedatabase.app/'
    })
    logger.info("Firebase initialized successfully")

    # Database references
    users_ref = db.reference('users')
    sessions_ref = db.reference('sessions')
    profiles_ref = db.reference('profiles')
    tags_ref = db.reference('tags')
    logger.info("Firebase database references created")

except Exception as e:
    logger.error(f"Failed to initialize Firebase: {e}", exc_info=True)
    # Don't exit, but set to None - app might still work without Firebase
    users_ref = None
    sessions_ref = None
    profiles_ref = None
    tags_ref = None

# JWT settings
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
if not JWT_SECRET_KEY:
    logger.warning("JWT_SECRET_KEY not found in environment variables")

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
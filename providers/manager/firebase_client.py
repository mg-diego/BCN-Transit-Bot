import os
import json
import firebase_admin
from firebase_admin import credentials

from providers.helpers import logger

firebase_credentials_file = "firebase-credentials.json"

def initialize_firebase():
    if firebase_admin._apps:
        # Ya inicializado, no hacer nada
        return firebase_admin.get_app()
    
    # FIREBASE
    if os.path.isfile(firebase_credentials_file):
        logger.info(f"Loading credentials from file '{firebase_credentials_file}'")
        cred = credentials.Certificate(firebase_credentials_file)
        firebase_admin.initialize_app(cred)
    else:
        firebase_creds_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
        if firebase_creds_json:
            logger.info("Loading credentials from environment variable 'FIREBASE_CREDENTIALS_JSON'")
            try:
                creds_dict = json.loads(firebase_creds_json)
                cred = credentials.Certificate.from_json(creds_dict)
            except Exception:
                import tempfile
                with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
                    tmp.write(firebase_creds_json)
                    tmp.flush()
                    cred = credentials.Certificate(tmp.name)
            firebase_admin.initialize_app(cred)
        else:
            raise FileNotFoundError(
                f"Credentials file '{firebase_credentials_file}' not found and 'FIREBASE_CREDENTIALS_JSON' environment variable is not set."
                        )

initialize_firebase()

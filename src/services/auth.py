import base64
import requests
import logging
from config import Config

class Authenticator:
    def __init__(self):
        self.logger = logging.getLogger('authenticator')
        self.api_key = Config.HUME_API_KEY
        self.secret_key = Config.HUME_SECRET_KEY
        self.host = Config.HUME_API_HOST
        self.logger = logging.getLogger(__name__)

    def fetch_access_token(self) -> str:
        self.logger.info("Fetching access token")
        auth_string = f"{self.api_key}:{self.secret_key}"
        encoded = base64.b64encode(auth_string.encode()).decode()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded}",
        }

        data = {
            "grant_type": "client_credentials",
        }

        # Using v0 endpoint
        response = requests.post(
            f"https://{self.host}/v0/oauth2/token",  # Updated token endpoint
            headers=headers, 
            data=data
        )

        data = response.json()
        self.logger.info("Access token fetched successfully")

        if "access_token" not in data:
            self.logger.error("Access token not found in response")
            raise ValueError("Access token not found in response")

        return data["access_token"]
import base64
import requests
import logging
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class Authenticator:
    def __init__(self, api_key: str = None, secret_key: str = None, host: str = "api.hume.ai"):
        """
        Initialize the authenticator with API credentials
        
        Args:
            api_key (str): Hume AI API key (optional, will use env var if not provided)
            secret_key (str): Hume AI secret key (optional, will use env var if not provided)
            host (str): API host domain
        """
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key or os.getenv('HUME_API_KEY')
        self.secret_key = secret_key or os.getenv('HUME_SECRET_KEY')
        self.host = host
        
        if not self.api_key or not self.secret_key:
            self.logger.error("Missing API credentials")
            raise ValueError("API key and secret key are required")

    def fetch_access_token(self) -> str:
        """
        Fetch an access token from the Hume AI API
        
        Returns:
            str: Access token if successful, None otherwise
        """
        self.logger.info("Fetching access token")
        try:
            # Create base64 encoded auth string
            auth_string = f"{self.api_key}:{self.secret_key}"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()

            # Set up request headers and data
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {encoded_auth}",
            }

            data = {
                "grant_type": "client_credentials",
            }

            # Make the request
            response = requests.post(
                f"https://{self.host}/oauth2-cc/token",
                headers=headers,
                data=data
            )
            
            # Check response status
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            if "access_token" not in data:
                self.logger.error("Access token not found in response")
                return None

            self.logger.info("Access token fetched successfully")
            return data["access_token"]

        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP request failed: {str(e)}")
            return None
        except ValueError as e:
            self.logger.error(f"Failed to parse response: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return None

    def validate_token(self, token: str) -> bool:
        """
        Validate an existing access token
        
        Args:
            token (str): Access token to validate
            
        Returns:
            bool: True if token is valid, False otherwise
        """
        try:
            # Set up request headers
            headers = {
                "Authorization": f"Bearer {token}"
            }
            
            # Make validation request
            response = requests.get(
                f"https://{self.host}/v0/auth/validate",
                headers=headers
            )
            
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"Token validation failed: {str(e)}")
            return False
import os
from dotenv import load_dotenv

load_dotenv()

class SecretsManager:
    def __init__(self):
        # We use the keys confirmed by the user
        self.secrets = {
            "[APP_ADMIN_USERNAME]": os.getenv("APP_ADMIN_USERNAME", os.getenv("APP_USERNAME", "admin")),
            "[APP_ADMIN_PASSWORD]": os.getenv("APP_ADMIN_PASSWORD", os.getenv("APP_PASSWORD", "admin123")),
        }

    def resolve(self, value: str) -> str:
        """
        Replaces placeholders with real secrets.
        Example: "[APP_ADMIN_PASSWORD]" -> "admin123"
        """
        if not value:
            return value
            
        resolved_value = value
        for placeholder, secret in self.secrets.items():
            if placeholder in resolved_value:
                resolved_value = resolved_value.replace(placeholder, secret)
        
        return resolved_value

    def get_placeholders(self):
        return list(self.secrets.keys())

    def mask(self, value: str) -> str:
        """
        Replaces real secrets with placeholders to prevent leakage.
        Example: "admin123" -> "[APP_ADMIN_PASSWORD]"
        """
        if not value:
            return value
            
        masked_value = value
        for placeholder, secret in self.secrets.items():
            if secret and secret in masked_value:
                # To prevent eager replacement of common words like 'admin', we can be selective,
                # but since 'admin' is specifically requested to be masked as username:
                masked_value = masked_value.replace(secret, placeholder)
        
        return masked_value

# Singleton instance
secrets_manager = SecretsManager()

import os
import uuid
import platform
import json
import logging

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Config:
    def __init__(self, config_path=None):
        # Default values
        self.SERVER_URL = os.environ.get("AGENT_SERVER_URL", "http://127.0.0.1:5700")
        self.API_KEY = os.environ.get("AGENT_API_KEY", "default_secret_key")
        self.AGENT_ID = os.environ.get("AGENT_ID")
        self.OS_TYPE = platform.system()
        self.HOSTNAME = platform.node()
        self.CONFIG_FILE = config_path or self._get_default_config_path()
        
        # Load from file if exists
        self.load_from_file()
        
        # Generate AGENT_ID if not set
        if not self.AGENT_ID:
            self.AGENT_ID = str(uuid.uuid4())
            self.save_to_file()

    def _get_default_config_path(self):
        if self.OS_TYPE == "Windows":
            return os.path.join(os.environ.get("PROGRAMDATA", "C:\\ProgramData"), "Agent", "config.json")
        else:
            return "/etc/agent/config.json"

    def load_from_file(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.SERVER_URL = data.get("server_url", self.SERVER_URL)
                    self.API_KEY = data.get("api_key", self.API_KEY)
                    self.AGENT_ID = data.get("agent_id", self.AGENT_ID)
                logger.info(f"Configuration loaded from {self.CONFIG_FILE}")
            except Exception as e:
                logger.error(f"Failed to load config from {self.CONFIG_FILE}: {e}")

    def save_to_file(self):
        try:
            os.makedirs(os.path.dirname(self.CONFIG_FILE), exist_ok=True)
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump({
                    "server_url": self.SERVER_URL,
                    "api_key": self.API_KEY,
                    "agent_id": self.AGENT_ID
                }, f, indent=4)
            logger.info(f"Configuration saved to {self.CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Failed to save config to {self.CONFIG_FILE}: {e}")

# Global config instance
agent_config = Config()
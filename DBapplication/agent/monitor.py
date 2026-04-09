import psutil
from config import agent_config

# Initialize to start tracking CPU usage accurately between calls
psutil.cpu_percent(interval=None)

def get_stats_dict():
    """Returns a dictionary of current system stats."""
    return {
        "agent_id": agent_config.AGENT_ID,
        "os": agent_config.OS_TYPE,
        "cpu_usage": psutil.cpu_percent(interval=None),
        "ram_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "status": "online"
    }

def get_stats():
    """Legacy/Compatibility function for Flask-style responses."""
    # Since this is run on the agent (client side), we should avoid using Flask's jsonify
    return get_stats_dict()
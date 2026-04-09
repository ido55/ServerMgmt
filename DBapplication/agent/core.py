import time
import requests
import logging
from config import agent_config
import monitor
import executor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def register():
    """Handshake with the Flask server to register the agent."""
    url = f"{agent_config.SERVER_URL}/agent/register"
    data = {
        "agent_id": agent_config.AGENT_ID,
        "hostname": agent_config.HOSTNAME,
        "os": agent_config.OS_TYPE,
        "version": "1.0.0"
    }
    headers = {"X-API-KEY": agent_config.API_KEY}
    
    while True:
        try:
            logger.info(f"Attempting to register with {url}...")
            response = requests.post(url, json=data, headers=headers, timeout=10)
            if response.status_code == 200:
                logger.info("Registration successful.")
                return True
            else:
                logger.error(f"Registration failed with status {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Registration error: {e}")
        
        logger.info("Retrying in 10 seconds...")
        time.sleep(10)

def heartbeat():
    logger.info(f"Agent {agent_config.AGENT_ID} starting heartbeat on {agent_config.OS_TYPE}")
    
    # Ensure registered first
    register()
    
    while True:
        try:
            # get_stats should return a dict, not a Flask response
            stats = monitor.get_stats_dict() 
            logger.info(f"Sending heartbeat stats: {stats}")
            headers = {"X-API-KEY": agent_config.API_KEY}
            response = requests.post(f"{agent_config.SERVER_URL}/agent/heartbeat", 
                                     json=stats, 
                                     headers=headers,
                                     timeout=10)

            if response.status_code == 200:
                payload = response.json()
                tasks = payload.get("tasks", [])
                for task in tasks:
                    logger.info(f"Executing task: {task.get('name')}")
                    # executor.exec_task can now handle sudo
                    result = executor.exec_task(
                        task.get('command'),
                        use_sudo=task.get('use_sudo', False),
                        sudo_password=task.get('sudo_password')
                    )
                    # Send result back
                    requests.post(f"{agent_config.SERVER_URL}/agent/task_result", 
                                  json={"task_id": task.get('id'), "result": result},
                                  headers=headers,
                                  timeout=10)
            else:
                logger.warning(f"Heartbeat failed with status {response.status_code}")

        except Exception as e:
            logger.error(f"Heartbeat loop error: {e}")
        
        time.sleep(30)

if __name__ == "__main__":
    heartbeat()

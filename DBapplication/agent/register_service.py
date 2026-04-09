import os
import sys
import platform
import subprocess

def create_linux_service():
    service_content = f"""[Unit]
Description=Server Management Agent
After=network.target

[Service]
Type=simple
User={os.getlogin()}
WorkingDirectory={os.getcwd()}
ExecStart={sys.executable} {os.path.join(os.getcwd(), 'core.py')}
Restart=always

[Install]
WantedBy=multi-user.target
"""
    service_path = "/etc/systemd/system/server-agent.service"
    try:
        with open("server-agent.service", "w") as f:
            f.write(service_content)
        print(f"Created server-agent.service locally. Run 'sudo cp server-agent.service {service_path} && sudo systemctl enable server-agent --now' to install.")
    except Exception as e:
        print(f"Error creating service file: {e}")

def create_windows_service():
    print("For Windows, it is recommended to use NSSM (Non-Sucking Service Manager) to wrap this python script as a service.")
    print(f"Command: nssm install ServerAgent {sys.executable} {os.path.join(os.getcwd(), 'core.py')}")

if __name__ == "__main__":
    if platform.system() == "Linux":
        create_linux_service()
    elif platform.system() == "Windows":
        create_windows_service()
    else:
        print(f"Unsupported OS: {platform.system()}")

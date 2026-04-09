# Server Management Console

A cross-platform management console built with Flask to orchestrate Windows and Linux servers through a lightweight Python agent.

## Features
- **Cross-Platform Support**: Manage both Windows (via PowerShell) and Linux (via Shell) servers.
- **Real-time Dashboard**: Monitor CPU, RAM, and Disk usage for all connected servers.
- **Script Orchestration**: Create scripts in the UI and deploy them to target servers.
- **Terminal Output**: View the exact stdout/stderr from executed scripts directly in the web interface.
- **Secure Communication**: All agent-to-server communication is protected by an API key.

## Project Structure
- `DBapplication/`: The Flask web application and API.
- `DBapplication/agent/`: The Python agent code to be installed on target servers.
- `instance/`: SQLite database storage.

---

## 1. Server Installation (Management Console)

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize Database**:
   ```bash
   cd DBapplication
   flask db upgrade
   ```

3. **Run the Application**:
   ```bash
   python run.py
   ```
   The console will be available at `http://localhost:5700`.

---

## 2. Agent Installation (Target Servers)

### Prerequisites
- Python 3.x
- `requests` and `psutil` libraries:
  ```bash
  pip install requests psutil
  ```

### Configuration
The agent needs a `config.json` file to know where to connect.
- **Linux**: `/etc/agent/config.json`
- **Windows**: `C:\ProgramData\Agent\config.json`

**Example `config.json`**:
```json
{
    "server_url": "http://<YOUR_SERVER_IP>:5700",
    "api_key": "default_secret_key"
}
```

### OS Specific Setup

#### Linux (Systemd)
1. Navigate to the `agent` folder.
2. Run the helper script:
   ```bash
   sudo python3 register_service.py
   ```
3. Follow the instructions to copy the service file and start it:
   ```bash
   sudo cp server-agent.service /etc/systemd/system/
   sudo systemctl enable server-agent --now
   ```

#### Windows
1. Navigate to the `agent` folder.
2. Run `python register_service.py` to see the recommended NSSM command.
3. Use [NSSM](https://nssm.cc/) to install `core.py` as a service:
   ```bash
   nssm install ServerAgent python.exe C:\path\to\agent\core.py
   nssm start ServerAgent
   ```

---

## 3. Usage Guide

### Running Scripts
1. Navigate to **Scripts** in the sidebar.
2. Create a new script (e.g., `Check Uptime`).
3. Go back to the **Home** dashboard.
4. Click **Run Script** on a server, enter the **Script ID**, and click OK.
5. The agent will pick up the task within 30 seconds.

### Viewing Results
1. Click **Details** on a server.
2. Scroll to **Job History**.
3. Click **View Terminal Output** to see the execution results.

### Monitoring
The main dashboard updates automatically every time an agent sends a heartbeat (every 30 seconds), showing current CPU, RAM, and Disk metrics.

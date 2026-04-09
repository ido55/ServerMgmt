import subprocess
import shlex
from config import agent_config
import logging

logger = logging.getLogger(__name__)

def exec_task(command, use_sudo=False, sudo_password=None):
    """Executes a command on the local system."""
    try:
        # Use shell=True for convenience, with appropriate shell for OS
        shell_executable = None
        input_data = None
        
        # Normalize line endings and whitespace
        if command:
            # First handle all combinations of line endings to prevent hidden characters
            command = command.replace('\r\n', '\n').replace('\r', '\n')
            # Strip outer whitespace but keep internal newlines
            command = command.strip()
        
        if agent_config.OS_TYPE == 'Windows':
            shell_executable = "powershell.exe"
            # For Windows, we still use shell=True and let PowerShell handle it.
        elif use_sudo:
            # Wrap the whole command in sh -c to ensure multi-line scripts work correctly with sudo -S
            # shlex.quote handles nested quotes and multi-line scripts safely.
            if sudo_password:
                # -S reads password from stdin, -p '' suppresses the prompt
                # IMPORTANT: Use a space after sh -c but keep the quote tight.
                command = f"sudo -S -p '' sh -c {shlex.quote(command)}"
                input_data = f"{sudo_password}\n"
            else:
                # No password provided, try sudo without it
                command = f"sudo sh -c {shlex.quote(command)}"
        
        logger.info(f"Executing task (Sudo: {use_sudo})")
        result = subprocess.run(command,
                                shell=True,
                                executable=shell_executable,
                                capture_output=True,
                                text=True,
                                input=input_data,
                                timeout=60)
        
        return {
            "status": "success" if result.returncode == 0 else "failed",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        return {"status": "error", "error": str(e)}
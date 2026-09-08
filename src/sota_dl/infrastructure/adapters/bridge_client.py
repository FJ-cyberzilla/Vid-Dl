import json
import subprocess
import logging
from typing import Any

logger = logging.getLogger(__name__)

class BridgeClient:
    def __init__(self, bridge_path: str = "bin/bridge"):
        self.bridge_path = bridge_path

    def call(self, action: str, params: dict[str, Any]) -> dict[str, Any]:
        """Sends a request to the bridge and returns the response."""
        request = {
            "action": action,
            "params": params
        }
        
        try:
            # We use subprocess to run the bridge binary and communicate via pipes.
            process = subprocess.Popen(
                [self.bridge_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=json.dumps(request))
            
            if process.returncode != 0:
                logger.error(f"Bridge error: {stderr}")
                return {"status": "error", "error": stderr}
            
            return json.loads(stdout)
            
        except Exception as e:
            logger.exception("Failed to communicate with bridge")
            return {"status": "error", "error": str(e)}

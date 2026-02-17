import requests
import os
from typing import Dict, Any, Optional

class APIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def _get(self, endpoint: str) -> Dict[str, Any]:
        try:
            response = requests.get(f"{self.base_url}{endpoint}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = requests.post(f"{self.base_url}{endpoint}", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Try to return the error detail from the API if available
            try:
                return response.json()
            except:
                return {"error": str(e)}

    def get_status(self):
        return self._get("/")

    def get_blockchain_status(self):
        return self._get("/blockchain/status")

    def parse_intent(self, user_intent: str, to_address: Optional[str] = None, amount: Optional[float] = None):
        payload = {"user_intent": user_intent}
        if to_address:
            payload["to_address"] = to_address
        if amount:
            payload["amount"] = amount
        return self._post("/ai/parse-intent", payload)

    def validate_transaction(self, tx_data: Dict[str, Any]):
        return self._post("/guardian/validate", tx_data)

    def execute_transaction(self, tx_data: Dict[str, Any]):
        return self._post("/blockchain/execute", tx_data)

    def get_policies(self):
        return self._get("/guardian/policies")

    def whitelist_address(self, address: str):
        return self._post("/guardian/whitelist", {"address": address})

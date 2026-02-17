import requests
from typing import Dict, Any, Optional

class APIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = 30  # seconds

    def _get(self, endpoint: str) -> Dict[str, Any]:
        """GET request with error handling"""
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            return {"error": "Request timeout - backend may be slow"}
        except requests.exceptions.ConnectionError:
            return {"error": "Cannot connect to backend - is it running?"}
        except requests.exceptions.RequestException as e:
            try:
                return response.json()
            except:
                return {"error": str(e)}

    def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """POST request with error handling"""
        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            return {"error": "Request timeout - transaction may take longer"}
        except requests.exceptions.ConnectionError:
            return {"error": "Cannot connect to backend"}
        except requests.exceptions.HTTPError as e:
            # Try to get detailed error from response
            try:
                error_detail = response.json()
                return {"error": error_detail.get("detail", str(e)), "status_code": response.status_code}
            except:
                return {"error": str(e), "status_code": response.status_code}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    # System Endpoints
    def get_status(self) -> Dict[str, Any]:
        """Get API status and system info"""
        return self._get("/")

    def get_health(self) -> Dict[str, Any]:
        """Health check"""
        return self._get("/health")

    # Blockchain Endpoints
    def get_blockchain_status(self) -> Dict[str, Any]:
        """Get blockchain connection status"""
        return self._get("/blockchain/status")

    def get_contract_info(self, address: str) -> Dict[str, Any]:
        """Get contract information for an address"""
        return self._get(f"/blockchain/contract-info/{address}")

    # AI Agent Endpoints
    def parse_intent(
        self, 
        user_intent: str, 
        to_address: Optional[str] = None, 
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """Parse natural language transaction intent"""
        payload: Dict[str, Any] = {"user_intent": user_intent}
        if to_address:
            payload["to_address"] = to_address
        if amount:
            payload["amount"] = amount
        return self._post("/ai/parse-intent", payload)

    # Guardian Endpoints
    def validate_transaction(self, tx_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate transaction through Guardian"""
        return self._post("/guardian/validate", tx_data)

    def get_policies(self) -> Dict[str, Any]:
        """Get current Guardian policies"""
        return self._get("/guardian/policies")

    def whitelist_address(self, address: str) -> Dict[str, Any]:
        """Add address to whitelist"""
        return self._post("/guardian/whitelist", {"address": address})

    # Execution Endpoints
    def execute_transaction(self, tx_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute transaction on blockchain"""
        return self._post("/blockchain/execute", tx_data)

    def execute_contract_interaction(
        self,
        contract_address: str,
        amount: float,
        function_data: str = "0x"
    ) -> Dict[str, Any]:
        """Execute smart contract interaction"""
        payload = {
            "contract_address": contract_address,
            "amount": amount,
            "function_data": function_data
        }
        return self._post("/blockchain/contract-interaction", payload)
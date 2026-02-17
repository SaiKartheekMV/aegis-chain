from typing import Dict

class GuardianEngine:
    def __init__(self):
        # Transfer limits
        self.max_transfer_limit = 0.1  # ETH for EOA transfers
        self.max_contract_value = 0.05  # ETH for contract interactions
        
        # Address whitelists
        self.whitelist = [
            "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        ]
        self.blacklist = []
        
        # Smart Contract Protocol Whitelist (Known DeFi on Sepolia/Mainnet)
        self.approved_contracts = {
            # Uniswap V2 Router
            "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D": {
                "name": "Uniswap V2 Router",
                "protocol": "DEX",
                "risk_level": "low",
                "description": "Decentralized token swaps"
            },
            # Aave V3 Pool (example)
            "0x794a61358D6845594F94dc1DB02A252b5b4814aD": {
                "name": "Aave V3 Pool",
                "protocol": "Lending",
                "risk_level": "medium",
                "description": "Supply/borrow assets"
            },
        }
        
        # Dangerous function signatures (first 4 bytes of function hash)
        self.dangerous_functions = [
            "0x23b872dd",  # transferFrom - can drain tokens
            "0x095ea7b3",  # approve - unlimited approvals risky
            "0xa9059cbb",  # transfer - token transfers
        ]
        
        # Protocol-specific limits
        self.protocol_limits = {
            "DEX": 0.05,      # Max ETH for DEX swaps
            "Lending": 0.03,  # Max ETH for lending protocols
            "Bridge": 0.02,   # Max ETH for bridges
            "NFT": 0.1,       # Max ETH for NFT marketplaces
        }
        
        # Gas safety limits
        self.max_gas_price_gwei = 100
        self.max_gas_limit = 500000
    
    def validate_policy(self, transaction: Dict) -> Dict:
        """
        Policy validation with smart contract awareness
        """
        violations = []
        warnings = []
        
        to_address = transaction['to_address']
        amount = transaction['amount']
        is_contract = transaction.get('is_contract', False)
        
        # Check blacklist (applies to both EOA and contracts)
        if to_address in self.blacklist:
            violations.append("⛔ Recipient is blacklisted")
        
        # CONTRACT INTERACTION PATH
        if is_contract:
            # Check if contract is approved
            if to_address in self.approved_contracts:
                contract_info = self.approved_contracts[to_address]
                warnings.append(f"✓ Verified protocol: {contract_info['name']} ({contract_info['protocol']})")
                
                # Check protocol-specific limits
                protocol_type = contract_info['protocol']
                max_allowed = self.protocol_limits.get(protocol_type, self.max_contract_value)
                
                if amount > max_allowed:
                    violations.append(f"Exceeds {protocol_type} limit of {max_allowed} ETH")
            else:
                # Unknown contract - CRITICAL VIOLATION
                violations.append(f"⚠️ Unknown/unverified smart contract")
                warnings.append("Contract not in approved protocol list")
            
            # Check general contract value limit
            if amount > self.max_contract_value:
                violations.append(f"Contract value exceeds {self.max_contract_value} ETH limit")
        
        # EOA TRANSFER PATH
        else:
            # Check whitelist for wallet-to-wallet transfers
            if to_address not in self.whitelist:
                violations.append("Address not in whitelist")
            
            # Check transfer limit
            if amount > self.max_transfer_limit:
                violations.append(f"Exceeds transfer limit of {self.max_transfer_limit} ETH")
        
        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "interaction_type": "smart_contract" if is_contract else "wallet_transfer"
        }
    
    def calculate_risk_score(self, transaction: Dict) -> Dict:
        """
        Enhanced risk scoring for autonomous agents
        """
        risk_score = 0
        reasons = []
        risk_factors = []
        
        to_address = transaction['to_address']
        amount = transaction['amount']
        is_contract = transaction.get('is_contract', False)
        ai_confidence = transaction.get('ai_confidence', 100)
        
        # SMART CONTRACT INTERACTION RISKS
        if is_contract:
            if to_address in self.approved_contracts:
                contract_info = self.approved_contracts[to_address]
                
                # Risk based on protocol type
                if contract_info['risk_level'] == 'high':
                    risk_score += 40
                    reasons.append(f"High-risk protocol: {contract_info['name']}")
                    risk_factors.append("HIGH_RISK_PROTOCOL")
                elif contract_info['risk_level'] == 'medium':
                    risk_score += 20
                    reasons.append(f"Medium-risk protocol: {contract_info['name']}")
                    risk_factors.append("MEDIUM_RISK_PROTOCOL")
                else:
                    risk_score += 10
                    reasons.append(f"Verified safe protocol: {contract_info['name']}")
                    risk_factors.append("VERIFIED_PROTOCOL")
            else:
                # UNKNOWN CONTRACT = CRITICAL RISK
                risk_score += 70
                reasons.append("⚠️ Unverified smart contract - potential malicious code")
                risk_factors.append("UNVERIFIED_CONTRACT")
            
            # High value to contract
            if amount > 0.03:
                risk_score += 25
                reasons.append("High value sent to smart contract")
                risk_factors.append("HIGH_CONTRACT_VALUE")
        
        # EOA TRANSFER RISKS
        else:
            if to_address not in self.whitelist:
                risk_score += 50
                reasons.append("Unknown recipient address")
                risk_factors.append("UNKNOWN_RECIPIENT")
            
            if amount > 0.05:
                risk_score += 30
                reasons.append("High transfer amount")
                risk_factors.append("HIGH_AMOUNT")
        
        # AI HALLUCINATION RISK
        if ai_confidence < 70:
            risk_score += 25
            reasons.append("⚠️ Low AI confidence - possible hallucination")
            risk_factors.append("AI_HALLUCINATION_RISK")
        elif ai_confidence < 85:
            risk_score += 10
            reasons.append("Moderate AI confidence")
            risk_factors.append("MODERATE_AI_CONFIDENCE")
        
        # GAS PRICE ANOMALY (front-running protection)
        gas_price = transaction.get('gas_price_gwei', 0)
        if gas_price > self.max_gas_price_gwei:
            risk_score += 15
            reasons.append("Unusually high gas price - potential front-running")
            risk_factors.append("HIGH_GAS_PRICE")
        
        # Determine final status
        if risk_score >= 70:
            status = "REJECTED"
            recommendation = "❌ BLOCKED - High risk detected. Transaction rejected by Guardian."
            action = "BLOCK"
        elif risk_score >= 40:
            status = "REQUIRES_REVIEW"
            recommendation = "⚠️ REVIEW REQUIRED - Manual approval needed before execution."
            action = "MANUAL_REVIEW"
        else:
            status = "APPROVED"
            recommendation = "✅ APPROVED - Transaction meets safety criteria."
            action = "PROCEED"
        
        return {
            "risk_score": risk_score,
            "status": status,
            "reasons": reasons,
            "risk_factors": risk_factors,
            "recommendation": recommendation,
            "action": action,
            "interaction_type": "smart_contract" if is_contract else "wallet_transfer"
        }
    
    def add_approved_contract(self, address: str, name: str, protocol: str, risk_level: str = "medium"):
        """
        Dynamically add approved contracts
        """
        self.approved_contracts[address] = {
            "name": name,
            "protocol": protocol,
            "risk_level": risk_level,
            "description": f"{protocol} protocol"
        }
    
    def whitelist_address(self, address: str):
        """Add address to whitelist"""
        self.whitelist.append(address)
    
    def blacklist_address(self, address: str):
        """Add address to blacklist"""
        self.blacklist.append(address)
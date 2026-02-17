import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from guardian import GuardianEngine
from blockchain import BlockchainConnector
from ai_agent import AIAgent


# ----------------------------
# App Initialization
# ----------------------------

app = FastAPI(
    title="AegisChain Guardian API",
    version="2.0.0",
    description="AI-Powered Transaction Guardrails for Autonomous On-Chain Agents - Sepolia Testnet"
)

# CORS Configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------
# Dependency Injection
# ----------------------------

def get_guardian():
    return GuardianEngine()

def get_blockchain():
    return BlockchainConnector()

def get_ai_agent():
    return AIAgent()


# ----------------------------
# Request/Response Models
# ----------------------------

class TransactionRequest(BaseModel):
    user_intent: str = Field(..., min_length=3, description="Natural language transaction description")
    to_address: Optional[str] = Field(None, description="Optional explicit recipient address")
    amount: Optional[float] = Field(None, gt=0, description="Optional explicit amount in ETH")


class TransactionProposal(BaseModel):
    to_address: str = Field(..., description="Recipient address (EOA or contract)")
    amount: float = Field(..., gt=0, description="Amount in ETH")
    ai_confidence: int = Field(100, ge=0, le=100, description="AI parsing confidence score")
    is_protocol_interaction: bool = Field(False, description="Is this a smart contract interaction")
    protocol_name: Optional[str] = Field(None, description="DeFi protocol name if applicable")


class WhitelistRequest(BaseModel):
    address: str = Field(..., description="Address to whitelist")


class ContractInteractionRequest(BaseModel):
    contract_address: str = Field(..., description="Smart contract address")
    amount: float = Field(..., gt=0, description="ETH amount to send")
    function_data: str = Field("0x", description="Encoded function call data")


# ----------------------------
# Root + Health Check
# ----------------------------

@app.get("/", tags=["System"])
def root(blockchain: BlockchainConnector = Depends(get_blockchain)):
    """
    API root endpoint - System status overview
    """
    return {
        "service": "AegisChain Guardian API",
        "version": "2.0.0",
        "status": "active",
        "description": "AI Transaction Guardrails for Autonomous On-Chain Agents",
        "network": "Sepolia Testnet",
        "blockchain_connected": blockchain.is_connected(),
        "wallet_balance": blockchain.get_balance(),
        "features": [
            "AI Intent Parsing",
            "Smart Contract Detection",
            "Risk Scoring Engine",
            "Transaction Simulation",
            "Multi-layer Validation",
            "DeFi Protocol Support"
        ]
    }


@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AegisChain Guardian"
    }


# ----------------------------
# AI Intent Parsing
# ----------------------------

@app.post("/ai/parse-intent", tags=["AI Agent"])
def parse_intent(
    request: TransactionRequest,
    ai_agent: AIAgent = Depends(get_ai_agent)
) -> Dict[str, Any]:
    """
    Parse natural language into structured transaction intent.
    Supports both wallet transfers and smart contract interactions.
    
    Examples:
    - "Send 0.01 ETH to 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    - "Swap 0.05 ETH on Uniswap"
    - "Supply 0.02 ETH to Aave"
    """
    try:
        # Manual input override
        if request.to_address and request.amount:
            return {
                "to_address": request.to_address,
                "amount": request.amount,
                "ai_confidence": 100,
                "reasoning": "Manual input provided",
                "parsed_from": "manual_input",
                "transaction_type": "wallet_transfer",
                "is_protocol_interaction": False
            }

        # AI parsing
        result = ai_agent.parse_transaction_intent(request.user_intent)
        
        # Add hallucination risk assessment
        hallucination_assessment = ai_agent.assess_hallucination_risk(result)
        result["hallucination_assessment"] = hallucination_assessment
        result["parsed_from"] = "ai_agent"
        
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI parsing failed: {str(e)}"
        )


# ----------------------------
# Guardian Validation
# ----------------------------

@app.post("/guardian/validate", tags=["Guardian"])
def validate_transaction(
    transaction: TransactionProposal,
    guardian: GuardianEngine = Depends(get_guardian),
    blockchain: BlockchainConnector = Depends(get_blockchain),
) -> Dict[str, Any]:
    """
    Multi-layer transaction validation through Guardian engine.
    
    Validation Steps:
    1. Policy check (whitelists, limits, blacklists)
    2. Blockchain simulation (gas estimation, contract detection)
    3. Risk scoring (0-100 scale)
    4. Final decision (APPROVED/REQUIRES_REVIEW/REJECTED)
    """
    try:
        tx_dict = transaction.model_dump()

        # Step 1: Policy Validation
        policy_result = guardian.validate_policy(tx_dict)

        # Step 2: Blockchain Simulation
        simulation_result = blockchain.simulate_transaction(tx_dict)
        
        # Add contract detection to transaction dict
        tx_dict["is_contract"] = simulation_result.get("is_contract", False)
        tx_dict["gas_price_gwei"] = simulation_result.get("max_fee_gwei", 0)

        # Step 3: Risk Scoring
        risk_result = guardian.calculate_risk_score(tx_dict)

        # Step 4: Build comprehensive response
        return {
            "transaction": tx_dict,
            "policy_check": policy_result,
            "simulation": simulation_result,
            "risk_analysis": risk_result,
            "final_decision": risk_result["status"],
            "recommended_action": risk_result["action"],
            "validation_summary": {
                "policy_passed": policy_result["passed"],
                "simulation_successful": simulation_result["success"],
                "risk_score": risk_result["risk_score"],
                "status": risk_result["status"]
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )


# ----------------------------
# Blockchain Execution
# ----------------------------

@app.post("/blockchain/execute", tags=["Blockchain"])
def execute_transaction(
    transaction: TransactionProposal,
    guardian: GuardianEngine = Depends(get_guardian),
    blockchain: BlockchainConnector = Depends(get_blockchain),
) -> Dict[str, Any]:
    """
    Execute transaction on Sepolia testnet.
    Only executes if Guardian approves (risk_score < 70).
    
    Security: Multi-layer validation before execution.
    """
    try:
        tx_dict = transaction.model_dump()

        # Pre-execution validation
        simulation_result = blockchain.simulate_transaction(tx_dict)
        tx_dict["is_contract"] = simulation_result.get("is_contract", False)
        tx_dict["gas_price_gwei"] = simulation_result.get("max_fee_gwei", 0)
        
        risk_result = guardian.calculate_risk_score(tx_dict)

        # Block if not approved
        if risk_result["status"] != "APPROVED":
            raise HTTPException(
                status_code=403,
                detail={
                    "message": "❌ Transaction BLOCKED by Guardian",
                    "status": risk_result["status"],
                    "risk_score": risk_result["risk_score"],
                    "reasons": risk_result["reasons"],
                    "risk_factors": risk_result.get("risk_factors", []),
                    "recommendation": risk_result["recommendation"]
                }
            )

        # Check simulation success
        if not simulation_result.get("success"):
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Transaction simulation failed",
                    "error": simulation_result.get("error", "Unknown error")
                }
            )

        # Execute on blockchain
        result = blockchain.execute_transaction(
            transaction.to_address,
            transaction.amount
        )

        # Add guardian metadata to response
        result["guardian_approval"] = {
            "risk_score": risk_result["risk_score"],
            "status": "APPROVED",
            "validation_passed": True
        }

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Execution failed: {str(e)}"
        )


# ----------------------------
# Smart Contract Interaction
# ----------------------------

@app.post("/blockchain/contract-interaction", tags=["Blockchain"])
def execute_contract_interaction(
    request: ContractInteractionRequest,
    guardian: GuardianEngine = Depends(get_guardian),
    blockchain: BlockchainConnector = Depends(get_blockchain),
) -> Dict[str, Any]:
    """
    Execute smart contract interaction (DeFi protocols).
    
    Examples:
    - Uniswap swaps
    - Aave deposits/withdrawals
    - Custom contract calls
    """
    try:
        # Validate contract address
        contract_info = blockchain.get_contract_info(request.contract_address)
        
        if not contract_info.get("is_contract"):
            raise HTTPException(
                status_code=400,
                detail="Target address is not a smart contract"
            )

        # Guardian validation for contract interaction
        tx_dict = {
            "to_address": request.contract_address,
            "amount": request.amount,
            "ai_confidence": 100,
            "is_contract": True
        }
        
        risk_result = guardian.calculate_risk_score(tx_dict)

        if risk_result["status"] == "REJECTED":
            raise HTTPException(
                status_code=403,
                detail={
                    "message": "Contract interaction blocked",
                    "risk_score": risk_result["risk_score"],
                    "reasons": risk_result["reasons"]
                }
            )

        # Execute contract interaction
        result = blockchain.execute_contract_interaction(
            request.contract_address,
            request.amount,
            request.function_data
        )

        result["guardian_check"] = risk_result

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Contract interaction failed: {str(e)}"
        )


# ----------------------------
# Blockchain Status & Info
# ----------------------------

@app.get("/blockchain/status", tags=["Blockchain"])
def blockchain_status(blockchain: BlockchainConnector = Depends(get_blockchain)):
    """
    Get current blockchain connection status and wallet info
    """
    balance = blockchain.get_balance()

    return {
        "connected": blockchain.is_connected(),
        "network": "Sepolia Testnet",
        "chain_id": blockchain.chain_id,
        "wallet_address": blockchain.account.address,
        "balance_eth": balance,
        "has_sufficient_funds": balance > 0.01,
        "rpc_provider": "Alchemy"
    }


@app.get("/blockchain/contract-info/{address}", tags=["Blockchain"])
def get_contract_info(
    address: str,
    blockchain: BlockchainConnector = Depends(get_blockchain)
):
    """
    Get information about a contract address
    """
    try:
        info = blockchain.get_contract_info(address)
        return info
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to get contract info: {str(e)}"
        )


# ----------------------------
# Guardian Management
# ----------------------------

@app.post("/guardian/whitelist", tags=["Guardian"])
def whitelist_address(
    request: WhitelistRequest,
    guardian: GuardianEngine = Depends(get_guardian)
):
    """
    Add address to Guardian whitelist
    """
    try:
        guardian.whitelist_address(request.address)
        return {
            "success": True,
            "message": f"Address {request.address} added to whitelist",
            "whitelist_size": len(guardian.whitelist)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/guardian/policies", tags=["Guardian"])
def get_guardian_policies(guardian: GuardianEngine = Depends(get_guardian)):
    """
    Get current Guardian policies and limits
    """
    return {
        "transfer_limits": {
            "max_transfer_limit": guardian.max_transfer_limit,
            "max_contract_value": guardian.max_contract_value
        },
        "whitelisted_addresses": guardian.whitelist,
        "blacklisted_addresses": guardian.blacklist,
        "approved_contracts": {
            addr: info["name"] 
            for addr, info in guardian.approved_contracts.items()
        },
        "gas_limits": {
            "max_gas_price_gwei": guardian.max_gas_price_gwei,
            "max_gas_limit": guardian.max_gas_limit
        }
    }


# ----------------------------
# Run Server
# ----------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
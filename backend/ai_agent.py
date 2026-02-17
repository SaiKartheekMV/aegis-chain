from groq import Groq
import os
import json
import re
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)


class AIAgent:
    # Default fallback values
    DEFAULT_ADDRESS = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    DEFAULT_AMOUNT = 0.01

    # Validation patterns
    ADDRESS_REGEX = re.compile(r"^0x[a-fA-F0-9]{40}$")
    
    # Known DeFi protocols for intent recognition
    KNOWN_PROTOCOLS = {
        "uniswap": {
            "address": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
            "type": "DEX",
            "keywords": ["swap", "trade", "exchange", "uniswap"]
        },
        "aave": {
            "address": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
            "type": "Lending",
            "keywords": ["lend", "borrow", "supply", "aave", "deposit"]
        },
    }

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env")

        self.client = Groq(api_key=api_key)
        logging.info("✅ AI Agent initialized with Groq")

    # -------------------------
    # Main Public Methods
    # -------------------------

    def parse_transaction_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Parse natural language into structured transaction intent.
        Handles both wallet transfers AND smart contract interactions.
        """
        try:
            # First, check if user is requesting a protocol interaction
            protocol_intent = self._detect_protocol_intent(user_input)
            
            if protocol_intent:
                logging.info(f"🎯 Protocol detected: {protocol_intent['protocol_name']}")
                return self._parse_protocol_transaction(user_input, protocol_intent)
            
            # Otherwise, treat as regular wallet transfer
            return self._parse_wallet_transfer(user_input)

        except Exception as e:
            logging.error(f"AI Parsing Error: {e}")
            return self._fallback_response(str(e))

    # -------------------------
    # Protocol Detection
    # -------------------------

    def _detect_protocol_intent(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        Detect if user wants to interact with a known DeFi protocol
        """
        user_lower = user_input.lower()
        
        for protocol_name, protocol_info in self.KNOWN_PROTOCOLS.items():
            # Check if any protocol keywords are mentioned
            if any(keyword in user_lower for keyword in protocol_info['keywords']):
                return {
                    "protocol_name": protocol_name,
                    "protocol_address": protocol_info['address'],
                    "protocol_type": protocol_info['type']
                }
        
        return None

    # -------------------------
    # Wallet Transfer Parsing
    # -------------------------

    def _parse_wallet_transfer(self, user_input: str) -> Dict[str, Any]:
        """
        Parse regular wallet-to-wallet transfer intent
        """
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                temperature=0,
                max_tokens=250,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a blockchain transaction parser. "
                            "Extract Ethereum wallet transfer details. "
                            "Respond ONLY with valid JSON."
                        ),
                    },
                    {
                        "role": "user",
                        "content": self._build_wallet_prompt(user_input),
                    },
                ],
            )

            raw_content = response.choices[0].message.content
            if raw_content is None:
                raise ValueError("Empty response from AI model")
            
            parsed = json.loads(raw_content)
            validated = self._validate_and_sanitize(parsed)
            validated['transaction_type'] = 'wallet_transfer'
            validated['is_protocol_interaction'] = False
            
            return validated

        except Exception as e:
            logging.error(f"Wallet parsing error: {e}")
            return self._fallback_response(str(e))

    # -------------------------
    # Protocol Transaction Parsing
    # -------------------------

    def _parse_protocol_transaction(self, user_input: str, protocol_intent: Dict) -> Dict[str, Any]:
        """
        Parse smart contract protocol interaction intent
        """
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                temperature=0,
                max_tokens=300,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a DeFi protocol transaction parser. "
                            "Extract smart contract interaction details. "
                            "Respond ONLY with valid JSON."
                        ),
                    },
                    {
                        "role": "user",
                        "content": self._build_protocol_prompt(user_input, protocol_intent),
                    },
                ],
            )

            raw_content = response.choices[0].message.content
            if raw_content is None:
                raise ValueError("Empty response from AI model")
            
            parsed = json.loads(raw_content)
            
            # Override address with protocol contract
            parsed['to_address'] = protocol_intent['protocol_address']
            parsed['protocol_name'] = protocol_intent['protocol_name']
            parsed['protocol_type'] = protocol_intent['protocol_type']
            parsed['transaction_type'] = 'protocol_interaction'
            parsed['is_protocol_interaction'] = True
            
            validated = self._validate_and_sanitize(parsed)
            
            # Add protocol-specific metadata
            validated['protocol_name'] = protocol_intent['protocol_name']
            validated['protocol_type'] = protocol_intent['protocol_type']
            validated['transaction_type'] = 'protocol_interaction'
            validated['is_protocol_interaction'] = True
            
            return validated

        except Exception as e:
            logging.error(f"Protocol parsing error: {e}")
            fallback = self._fallback_response(str(e))
            fallback['transaction_type'] = 'protocol_interaction'
            fallback['is_protocol_interaction'] = True
            return fallback

    # -------------------------
    # Prompt Builders
    # -------------------------

    def _build_wallet_prompt(self, user_input: str) -> str:
        return f"""
Extract Ethereum wallet transfer details from this message:

"{user_input}"

Return JSON with this exact structure:
{{
  "to_address": "0x...",
  "amount": float,
  "confidence": int (0-100),
  "reasoning": "brief explanation"
}}

Rules:
- Extract the recipient Ethereum address (0x...)
- Extract the amount in ETH
- Confidence reflects parsing certainty
- If address/amount missing, note in reasoning
"""

    def _build_protocol_prompt(self, user_input: str, protocol_intent: Dict) -> str:
        protocol_name = protocol_intent['protocol_name'].capitalize()
        protocol_type = protocol_intent['protocol_type']
        
        return f"""
Extract {protocol_name} protocol interaction details from this message:

"{user_input}"

Protocol: {protocol_name} ({protocol_type})

Return JSON with this exact structure:
{{
  "amount": float,
  "action": "string (e.g., 'swap', 'supply', 'borrow')",
  "confidence": int (0-100),
  "reasoning": "brief explanation",
  "additional_params": {{}}
}}

Rules:
- Extract the amount of ETH for the transaction
- Identify the specific action (swap, supply, borrow, etc.)
- Confidence reflects parsing certainty
- Include any additional parameters if mentioned
"""

    # -------------------------
    # Validation Layer
    # -------------------------

    def _validate_and_sanitize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize parsed data
        """
        address = data.get("to_address", self.DEFAULT_ADDRESS)
        amount = data.get("amount", self.DEFAULT_AMOUNT)
        confidence = data.get("confidence", 50)
        reasoning = data.get("reasoning", "")

        # Address validation
        if not isinstance(address, str) or not self.ADDRESS_REGEX.match(address):
            logging.warning(f"⚠️ Invalid address detected: {address}")
            address = self.DEFAULT_ADDRESS
            confidence = max(0, confidence - 30)

        # Amount validation
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be positive")
            if amount > 1000:
                logging.warning(f"⚠️ Unusually high amount: {amount} ETH")
                confidence = max(0, confidence - 20)
        except Exception as e:
            logging.warning(f"⚠️ Invalid amount: {e}")
            amount = self.DEFAULT_AMOUNT
            confidence = max(0, confidence - 20)

        # Confidence normalization
        try:
            confidence = int(confidence)
        except Exception:
            confidence = 50

        confidence = max(0, min(confidence, 100))

        # Build result
        result = {
            "to_address": address,
            "amount": amount,
            "confidence": confidence,
            "reasoning": reasoning.strip(),
            "ai_model": "llama-3.3-70b-versatile",
        }
        
        # Preserve protocol-specific fields if present
        if 'action' in data:
            result['action'] = data['action']
        if 'additional_params' in data:
            result['additional_params'] = data['additional_params']
        
        return result

    # -------------------------
    # Fallback Response
    # -------------------------

    def _fallback_response(self, error_msg: str) -> Dict[str, Any]:
        """
        Return safe fallback when AI parsing fails
        """
        return {
            "to_address": self.DEFAULT_ADDRESS,
            "amount": self.DEFAULT_AMOUNT,
            "confidence": 40,
            "reasoning": f"AI parsing failed: {error_msg}",
            "ai_model": "fallback",
            "transaction_type": "wallet_transfer",
            "is_protocol_interaction": False
        }

    # -------------------------
    # Risk Assessment Helper
    # -------------------------

    def assess_hallucination_risk(self, parsed_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess if AI might be hallucinating transaction details
        """
        confidence = parsed_result.get('confidence', 50)
        is_protocol = parsed_result.get('is_protocol_interaction', False)
        
        risk_score = 0
        risk_factors = []
        
        # Low confidence = hallucination risk
        if confidence < 60:
            risk_score += 40
            risk_factors.append("Low AI confidence")
        elif confidence < 80:
            risk_score += 20
            risk_factors.append("Medium AI confidence")
        
        # Protocol interactions need higher confidence
        if is_protocol and confidence < 70:
            risk_score += 30
            risk_factors.append("Protocol interaction with low confidence")
        
        # Using fallback values = high risk
        if parsed_result.get('to_address') == self.DEFAULT_ADDRESS:
            risk_score += 25
            risk_factors.append("Using default address")
        
        if parsed_result.get('amount') == self.DEFAULT_AMOUNT:
            risk_score += 15
            risk_factors.append("Using default amount")
        
        return {
            "hallucination_risk_score": min(risk_score, 100),
            "risk_factors": risk_factors,
            "is_likely_hallucination": risk_score >= 60
        }
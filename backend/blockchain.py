from web3 import Web3
from typing import Dict, Optional
import os
from dotenv import load_dotenv
from hexbytes import HexBytes

load_dotenv()

class BlockchainConnector:
    def __init__(self):
        rpc_url = os.getenv("ALCHEMY_RPC_URL")
        private_key = os.getenv("PRIVATE_KEY")

        if not rpc_url:
            raise ValueError("ALCHEMY_RPC_URL not found in .env")
        if not private_key:
            raise ValueError("PRIVATE_KEY not found in .env")

        self.w3 = Web3(Web3.HTTPProvider(rpc_url))

        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to Sepolia RPC")

        self.account = self.w3.eth.account.from_key(private_key)
        self.chain_id = self.w3.eth.chain_id

        print(f"🔗 Connected: {self.w3.is_connected()}")
        print(f"🌐 Chain ID: {self.chain_id}")
        print(f"💰 Wallet: {self.account.address}")
        print(f"💵 Balance: {self.get_balance()} ETH")

    def is_connected(self) -> bool:
        return self.w3.is_connected()

    def get_balance(self, address: Optional[str] = None) -> float:
        addr = address or self.account.address
        balance_wei = self.w3.eth.get_balance(Web3.to_checksum_address(addr))
        return float(self.w3.from_wei(balance_wei, 'ether'))

    def is_contract(self, address: str) -> bool:
        """
        Check if address is a smart contract
        """
        try:
            checksum_addr = Web3.to_checksum_address(address)
            code = self.w3.eth.get_code(checksum_addr)
            return len(code) > 0
        except:
            return False

    def get_contract_info(self, address: str) -> Dict:
        """
        Get detailed contract information
        """
        try:
            checksum_addr = Web3.to_checksum_address(address)
            code = self.w3.eth.get_code(checksum_addr)
            
            if len(code) == 0:
                return {
                    "is_contract": False,
                    "type": "EOA",
                    "code_size": 0
                }
            
            return {
                "is_contract": True,
                "type": "Smart Contract",
                "code_size": len(code),
                "code_hash": self.w3.keccak(code).hex(),
                "has_code": True
            }
        except Exception as e:
            return {
                "is_contract": False,
                "error": str(e)
            }

    def simulate_transaction(self, transaction: Dict) -> Dict:
        """
        Enhanced simulation with contract detection and gas analysis
        """
        try:
            to_address = Web3.to_checksum_address(transaction['to_address'].lower())
            amount_wei = self.w3.to_wei(transaction['amount'], 'ether')

            # Get contract info
            contract_info = self.get_contract_info(to_address)
            is_contract = contract_info.get('is_contract', False)

            # Estimate gas
            gas_estimate = self.w3.eth.estimate_gas({
                'from': self.account.address,
                'to': to_address,
                'value': amount_wei
            })

            # Get gas price info
            block = self.w3.eth.get_block('latest')
            base_fee = block.get('baseFeePerGas') or self.w3.to_wei(1, 'gwei')
            priority_fee = self.w3.to_wei(2, 'gwei')
            max_fee = base_fee + priority_fee

            gas_cost_eth = self.w3.from_wei(gas_estimate * max_fee, 'ether')
            gas_price_gwei = float(self.w3.from_wei(max_fee, 'gwei'))

            # Calculate total cost
            total_cost = float(transaction['amount']) + float(gas_cost_eth)

            # Check if user has enough balance
            current_balance = self.get_balance()
            has_sufficient_balance = current_balance >= total_cost

            return {
                "success": True,
                "is_contract": is_contract,
                "contract_type": contract_info.get('type', 'EOA'),
                "estimated_gas": gas_estimate,
                "base_fee_gwei": float(self.w3.from_wei(base_fee, 'gwei')),
                "priority_fee_gwei": float(self.w3.from_wei(priority_fee, 'gwei')),
                "max_fee_gwei": gas_price_gwei,
                "gas_cost_eth": float(gas_cost_eth),
                "total_cost_eth": total_cost,
                "current_balance_eth": current_balance,
                "has_sufficient_balance": has_sufficient_balance,
                "network": "Sepolia Testnet",
                "simulation_status": "✅ Will succeed" if has_sufficient_balance else "❌ Insufficient balance"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "simulation_status": f"❌ Simulation failed: {str(e)}"
            }

    def execute_transaction(self, to_address: str, amount_eth: float) -> Dict:
        """
        Execute transaction with enhanced safety checks
        """
        try:
            to_addr = Web3.to_checksum_address(to_address)
            amount_wei = self.w3.to_wei(amount_eth, 'ether')

            # Check if it's a contract
            is_contract = self.is_contract(to_addr)

            # Balance check
            balance = self.w3.eth.get_balance(self.account.address)
            if balance < amount_wei:
                return {
                    "success": False,
                    "error": "Insufficient balance",
                    "current_balance": float(self.w3.from_wei(balance, 'ether')),
                    "required": amount_eth
                }

            nonce = self.w3.eth.get_transaction_count(self.account.address)

            # Get gas parameters
            block = self.w3.eth.get_block('latest')
            base_fee = block.get('baseFeePerGas') or self.w3.to_wei(1, 'gwei')
            priority_fee = self.w3.to_wei(2, 'gwei')
            max_fee = base_fee + priority_fee

            # Estimate gas
            gas_estimate = self.w3.eth.estimate_gas({
                'from': self.account.address,
                'to': to_addr,
                'value': amount_wei
            })

            # Add 10% buffer to gas estimate
            gas_limit = int(gas_estimate * 1.1)

            # Build transaction
            txn = {
                'chainId': self.chain_id,
                'from': self.account.address,
                'to': to_addr,
                'value': amount_wei,
                'nonce': nonce,
                'gas': gas_limit,
                'maxFeePerGas': max_fee,
                'maxPriorityFeePerGas': priority_fee,
                'type': 2  # EIP-1559
            }

            # Sign transaction
            signed_txn = self.account.sign_transaction(txn)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            print(f"⏳ Transaction sent: {tx_hash.hex()}")
            print(f"⏳ Waiting for confirmation...")

            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            # Get actual gas used
            gas_used = receipt["gasUsed"]
            gas_price = receipt["effectiveGasPrice"]
            gas_cost = self.w3.from_wei(gas_used * gas_price, 'ether')

            return {
                "success": receipt["status"] == 1,
                "tx_hash": tx_hash.hex(),
                "block_number": receipt["blockNumber"],
                "gas_used": gas_used,
                "gas_cost_eth": float(gas_cost),
                "total_cost_eth": amount_eth + float(gas_cost),
                "is_contract_interaction": is_contract,
                "explorer_url": f"https://sepolia.etherscan.io/tx/{tx_hash.hex()}",
                "status_message": "✅ Transaction confirmed" if receipt["status"] == 1 else "❌ Transaction failed"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status_message": f"❌ Transaction failed: {str(e)}"
            }

    def execute_contract_interaction(self, contract_address: str, amount_eth: float, function_data: str = "0x") -> Dict:
        """
        Execute smart contract interaction with function call data
        For future DeFi protocol interactions (Uniswap swaps, Aave deposits, etc.)
        """
        try:
            contract_addr = Web3.to_checksum_address(contract_address)
            amount_wei = self.w3.to_wei(amount_eth, 'ether')

            # Verify it's a contract
            if not self.is_contract(contract_addr):
                return {
                    "success": False,
                    "error": "Target address is not a smart contract"
                }

            nonce = self.w3.eth.get_transaction_count(self.account.address)

            # Get gas parameters
            block = self.w3.eth.get_block('latest')
            base_fee = block.get('baseFeePerGas') or self.w3.to_wei(1, 'gwei')
            priority_fee = self.w3.to_wei(2, 'gwei')
            max_fee = base_fee + priority_fee

            # Convert function_data to HexBytes
            data_bytes = HexBytes(function_data) if function_data != "0x" else HexBytes("0x")

            # Estimate gas with function data - FIXED TYPE
            gas_estimate = self.w3.eth.estimate_gas({
                'from': self.account.address,
                'to': contract_addr,
                'value': amount_wei,
                'data': data_bytes  # Fixed: Use HexBytes
            })

            gas_limit = int(gas_estimate * 1.2)  # 20% buffer for contract calls

            # Build transaction
            txn = {
                'chainId': self.chain_id,
                'from': self.account.address,
                'to': contract_addr,
                'value': amount_wei,
                'data': data_bytes,  # Fixed: Use HexBytes
                'nonce': nonce,
                'gas': gas_limit,
                'maxFeePerGas': max_fee,
                'maxPriorityFeePerGas': priority_fee,
                'type': 2
            }

            signed_txn = self.account.sign_transaction(txn)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            print(f"⏳ Contract interaction sent: {tx_hash.hex()}")
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            return {
                "success": receipt["status"] == 1,
                "tx_hash": tx_hash.hex(),
                "block_number": receipt["blockNumber"],
                "gas_used": receipt["gasUsed"],
                "contract_address": contract_addr,
                "explorer_url": f"https://sepolia.etherscan.io/tx/{tx_hash.hex()}",
                "interaction_type": "smart_contract_call"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_transaction_details(self, tx_hash: str) -> Dict:
        """
        Get detailed transaction information - FIXED TYPE ERRORS
        """
        try:
            # Convert string to HexBytes - FIXED
            tx_hash_bytes = HexBytes(tx_hash)
            
            tx = self.w3.eth.get_transaction(tx_hash_bytes)
            receipt = self.w3.eth.get_transaction_receipt(tx_hash_bytes)

            return {
                "from": tx.get('from', 'Unknown'),  # FIXED: Use .get()
                "to": tx.get('to', None),  # FIXED: Use .get()
                "value_eth": float(self.w3.from_wei(tx.get('value', 0), 'ether')),  # FIXED: Use .get()
                "gas_used": receipt['gasUsed'],
                "status": "Success" if receipt['status'] == 1 else "Failed",
                "block_number": receipt['blockNumber'],
                "is_contract_creation": tx.get('to') is None  # FIXED: Use .get()
            }
        except Exception as e:
            return {
                "error": str(e)
            }
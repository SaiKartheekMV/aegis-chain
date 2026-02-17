import streamlit as st
import pandas as pd
import requests
from api_client import APIClient
import time

# Initialize API Client
api = APIClient(base_url="http://localhost:8000")

# Page Configuration
st.set_page_config(
    page_title="AegisChain Guardian",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-weight: 600;
    }
    .approved {
        background-color: #d4edda;
        color: #155724;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 10px 0;
    }
    .rejected {
        background-color: #f8d7da;
        color: #721c24;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 10px 0;
    }
    .review {
        background-color: #fff3cd;
        color: #856404;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 10px 0;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        text-align: center;
        border: 1px solid #e0e0e0;
    }
    .info-box {
        background-color: #e7f3ff;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #2196F3;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.title("🛡️ AegisChain Guardian")
st.sidebar.markdown("**AI Transaction Guardrails**")
st.sidebar.markdown("*Innofusion'26 - Round 2*")

page = st.sidebar.radio(
    "Navigation",
    ["🏠 Dashboard", "🤖 AI Agent", "🛡️ Guardian", "📊 Analytics", "⚙️ Settings"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")

# System Status in Sidebar
st.sidebar.markdown("### 🔧 System Status")
try:
    health = api.get_health()
    if health.get("status") == "healthy":
        st.sidebar.success("✅ Backend: Online")
    else:
        st.sidebar.warning("⚠️ Backend: Degraded")
except:
    st.sidebar.error("❌ Backend: Offline")

try:
    bc_status = api.get_blockchain_status()
    if bc_status.get("connected"):
        st.sidebar.success(f"✅ Blockchain: Connected")
        st.sidebar.caption(f"Network: {bc_status.get('network')}")
        st.sidebar.caption(f"Balance: {bc_status.get('balance_eth', 0):.4f} ETH")
    else:
        st.sidebar.error("❌ Blockchain: Disconnected")
except:
    st.sidebar.error("❌ Blockchain: Error")

st.sidebar.markdown("---")
st.sidebar.caption("Team Innofusion | 2026")

# ============================================================
# PAGE: DASHBOARD
# ============================================================
if page == "🏠 Dashboard":
    st.title("🛡️ AegisChain Guardian Dashboard")
    st.markdown("**Real-time monitoring of AI transaction security**")
    
    # System Overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        try:
            status = api.get_status()
            st.metric(
                "System Status",
                "🟢 Active" if status.get("status") == "active" else "🔴 Inactive"
            )
        except:
            st.metric("System Status", "🔴 Error")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        try:
            bc_status = api.get_blockchain_status()
            st.metric(
                "Network",
                bc_status.get("network", "Unknown")
            )
        except:
            st.metric("Network", "Disconnected")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        try:
            bc_status = api.get_blockchain_status()
            balance = bc_status.get("balance_eth", 0)
            st.metric(
                "Wallet Balance",
                f"{balance:.4f} ETH",
                delta="Sufficient" if balance > 0.01 else "Low"
            )
        except:
            st.metric("Wallet Balance", "N/A")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        try:
            policies = api.get_policies()
            whitelist_count = len(policies.get("whitelisted_addresses", []))
            st.metric(
                "Whitelisted",
                f"{whitelist_count} addresses"
            )
        except:
            st.metric("Whitelisted", "N/A")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Detailed Status
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("🔗 Blockchain Connection")
        try:
            bc_status = api.get_blockchain_status()
            
            if bc_status.get("connected"):
                st.success("✅ Connected to Sepolia Testnet")
                
                info_data = {
                    "Network": bc_status.get("network"),
                    "Chain ID": bc_status.get("chain_id"),
                    "RPC Provider": bc_status.get("rpc_provider"),
                    "Wallet": bc_status.get("wallet_address"),
                    "Balance": f"{bc_status.get('balance_eth')} ETH"
                }
                
                for key, value in info_data.items():
                    st.text(f"{key}: {value}")
            else:
                st.error("❌ Blockchain not connected")
                
        except Exception as e:
            st.error(f"Failed to fetch blockchain status: {str(e)}")
    
    with col_right:
        st.subheader("🛡️ Guardian Policies")
        try:
            policies = api.get_policies()
            
            limits = policies.get("transfer_limits", {})
            gas_limits = policies.get("gas_limits", {})
            
            st.markdown(f"""
            **Transfer Limits:**
            - Max Transfer: `{limits.get('max_transfer_limit')} ETH`
            - Max Contract: `{limits.get('max_contract_value')} ETH`
            
            **Gas Limits:**
            - Max Gas Price: `{gas_limits.get('max_gas_price_gwei')} Gwei`
            - Max Gas Limit: `{gas_limits.get('max_gas_limit')}`
            
            **Security:**
            - Whitelisted: `{len(policies.get('whitelisted_addresses', []))} addresses`
            - Blacklisted: `{len(policies.get('blacklisted_addresses', []))} addresses`
            - Approved Protocols: `{len(policies.get('approved_contracts', {}))} contracts`
            """)
            
        except Exception as e:
            st.error(f"Failed to fetch policies: {str(e)}")
    
    st.divider()
    
    # Features Overview
    st.subheader("✨ Active Features")
    try:
        status = api.get_status()
        features = status.get("features", [])
        
        cols = st.columns(3)
        for idx, feature in enumerate(features):
            with cols[idx % 3]:
                st.markdown(f"✅ {feature}")
    except:
        st.info("Unable to load features")

# ============================================================
# PAGE: AI AGENT
# ============================================================
elif page == "🤖 AI Agent":
    st.title("🤖 AI Transaction Agent")
    st.markdown("**Natural language transaction parsing with hallucination detection**")
    
    # Step 1: Intent Input
    st.subheader("Step 1: Transaction Intent")
    
    tab1, tab2 = st.tabs(["💬 Natural Language", "✏️ Manual Entry"])
    
    with tab1:
        st.markdown('<div class="info-box">Describe your transaction in plain English. The AI will extract address, amount, and detect protocols.</div>', unsafe_allow_html=True)
        
        # Example buttons
        st.markdown("**Quick Examples:**")
        col_ex1, col_ex2, col_ex3 = st.columns(3)
        
        with col_ex1:
            if st.button("💸 Wallet Transfer"):
                st.session_state['intent_input'] = "Send 0.01 ETH to 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
        
        with col_ex2:
            if st.button("🔄 Uniswap Swap"):
                st.session_state['intent_input'] = "Swap 0.02 ETH on Uniswap"
        
        with col_ex3:
            if st.button("⚠️ Hallucination Test"):
                st.session_state['intent_input'] = "Send money to Bob"
        
        user_intent = st.text_area(
            "Your Transaction Intent:",
            value=st.session_state.get('intent_input', "Send 0.01 ETH to 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"),
            height=100,
            placeholder="Example: Send 0.05 ETH to my friend at 0x..."
        )
        
        if st.button("🧠 Parse with AI", type="primary", use_container_width=True):
            if not user_intent or not user_intent.strip():
                st.error("❌ Please enter a transaction intent")
            else:
                with st.spinner("🤖 AI analyzing transaction intent..."):
                    parsed = api.parse_intent(user_intent)
                
                if "error" in parsed:
                    st.error(f"❌ Parsing failed: {parsed['error']}")
                else:
                    st.session_state['parsed_tx'] = parsed
                    st.success("✅ Intent parsed successfully!")
                    st.rerun()
    
    with tab2:
        st.markdown("**Manual transaction input (bypasses AI parsing)**")
        
        manual_address = st.text_input(
            "Recipient Address:",
            value="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            placeholder="0x..."
        )
        
        manual_amount = st.number_input(
            "Amount (ETH):",
            min_value=0.0001,
            max_value=10.0,
            value=0.01,
            step=0.001,
            format="%.4f"
        )
        
        if st.button("➡️ Use Manual Input", type="primary", use_container_width=True):
            st.session_state['parsed_tx'] = {
                "to_address": manual_address,
                "amount": manual_amount,
                "ai_confidence": 100,
                "reasoning": "Manual input provided",
                "parsed_from": "manual_input",
                "transaction_type": "wallet_transfer",
                "is_protocol_interaction": False
            }
            st.success("✅ Manual transaction prepared!")
            st.rerun()
    
    # Step 2: Parsed Result
    if 'parsed_tx' in st.session_state:
        st.divider()
        st.subheader("Step 2: Parsed Transaction")
        
        tx = st.session_state['parsed_tx']
        
        # Transaction Preview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Recipient",
                f"{tx.get('to_address', '')[:6]}...{tx.get('to_address', '')[-4:]}"
            )
        
        with col2:
            st.metric("Amount", f"{tx.get('amount', 0)} ETH")
        
        with col3:
            confidence = tx.get('ai_confidence', 100)
            st.metric(
                "AI Confidence",
                f"{confidence}%",
                delta="Good" if confidence >= 70 else "Low"
            )
        
        with col4:
            tx_type = tx.get('transaction_type', 'unknown')
            st.metric(
                "Type",
                "Protocol" if tx.get('is_protocol_interaction') else "Wallet"
            )
        
        # Protocol Info (if applicable)
        if tx.get('is_protocol_interaction'):
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown(f"""
            **🔗 Smart Contract Interaction Detected**
            - Protocol: `{tx.get('protocol_name', 'Unknown').capitalize()}`
            - Type: `{tx.get('protocol_type', 'Unknown')}`
            - Action: `{tx.get('action', 'N/A')}`
            """)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Hallucination Assessment
        hallucination = tx.get('hallucination_assessment', {})
        if hallucination:
            risk_score = hallucination.get('hallucination_risk_score', 0)
            is_hallucination = hallucination.get('is_likely_hallucination', False)
            
            if is_hallucination:
                st.markdown('<div class="warning-box">', unsafe_allow_html=True)
                st.markdown(f"""
                **⚠️ Hallucination Risk Detected**
                - Risk Score: `{risk_score}/100`
                - Factors: {', '.join(hallucination.get('risk_factors', []))}
                
                *The AI may have filled in missing information with defaults. Review carefully before proceeding.*
                """)
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Full Details Expander
        with st.expander("🔍 View Full Parsed Data"):
            st.json(tx)
        
        # Validate Button
        st.divider()
        if st.button("🛡️ Validate with Guardian", type="primary", use_container_width=True):
            with st.spinner("🔍 Guardian analyzing transaction..."):
                # Prepare validation payload
                proposal = {
                    "to_address": tx.get("to_address"),
                    "amount": tx.get("amount"),
                    "ai_confidence": tx.get("ai_confidence", 100),
                    "is_protocol_interaction": tx.get("is_protocol_interaction", False),
                    "protocol_name": tx.get("protocol_name")
                }
                
                validation = api.validate_transaction(proposal)
                
                if "error" in validation:
                    st.error(f"❌ Validation failed: {validation['error']}")
                else:
                    st.session_state['validation_result'] = validation
                    st.session_state['proposal'] = proposal
                    st.success("✅ Validation complete!")
                    st.rerun()
    
    # Step 3: Validation Results
    if 'validation_result' in st.session_state:
        st.divider()
        st.subheader("Step 3: Guardian Validation Results")
        
        val = st.session_state['validation_result']
        decision = val.get('final_decision', 'UNKNOWN')
        risk = val.get('risk_analysis', {})
        policy = val.get('policy_check', {})
        simulation = val.get('simulation', {})
        
        # Decision Banner
        if decision == "APPROVED":
            st.markdown('<div class="approved">', unsafe_allow_html=True)
            st.markdown(f"### ✅ TRANSACTION APPROVED")
            st.markdown(f"**{risk.get('recommendation', '')}**")
            st.markdown('</div>', unsafe_allow_html=True)
        elif decision == "REJECTED":
            st.markdown('<div class="rejected">', unsafe_allow_html=True)
            st.markdown(f"### ❌ TRANSACTION REJECTED")
            st.markdown(f"**{risk.get('recommendation', '')}**")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="review">', unsafe_allow_html=True)
            st.markdown(f"### ⚠️ REQUIRES REVIEW")
            st.markdown(f"**{risk.get('recommendation', '')}**")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Validation Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            risk_score = risk.get('risk_score', 0)
            st.metric(
                "Risk Score",
                f"{risk_score}/100",
                delta="High" if risk_score >= 70 else "Low"
            )
        
        with col2:
            st.metric(
                "Policy Check",
                "✅ Pass" if policy.get('passed') else "❌ Fail"
            )
        
        with col3:
            st.metric(
                "Simulation",
                "✅ Success" if simulation.get('success') else "❌ Fail"
            )
        
        with col4:
            if simulation.get('success'):
                st.metric(
                    "Gas Cost",
                    f"{simulation.get('gas_cost_eth', 0):.6f} ETH"
                )
            else:
                st.metric("Gas Cost", "N/A")
        
        # Risk Analysis Details
        if risk.get('reasons'):
            st.markdown("**🎯 Risk Factors:**")
            for reason in risk.get('reasons', []):
                st.markdown(f"- {reason}")
        
        # Policy Violations
        if not policy.get('passed'):
            st.markdown("**⛔ Policy Violations:**")
            for violation in policy.get('violations', []):
                st.markdown(f"- {violation}")
        
        # Warnings
        if policy.get('warnings'):
            st.markdown("**⚠️ Warnings:**")
            for warning in policy.get('warnings', []):
                st.markdown(f"- {warning}")
        
        # Full Validation Report
        with st.expander("📋 Full Validation Report"):
            st.json(val)
        
        # Execution Section
        st.divider()
        
        if decision == "APPROVED":
            st.markdown("### 🚀 Execute Transaction")
            st.warning("⚠️ This will broadcast a REAL transaction to Sepolia testnet!")
            
            col_exec1, col_exec2 = st.columns(2)
            
            with col_exec1:
                if st.button("✅ Execute on Blockchain", type="primary", use_container_width=True):
                    with st.spinner("📡 Broadcasting transaction..."):
                        time.sleep(1)  # UX delay
                        
                        exec_result = api.execute_transaction(st.session_state['proposal'])
                        
                        if exec_result.get('success'):
                            st.balloons()
                            st.success("🎉 Transaction Successful!")
                            
                            st.markdown(f"""
                            **Transaction Details:**
                            - TX Hash: `{exec_result.get('tx_hash')}`
                            - Block: `{exec_result.get('block_number')}`
                            - Gas Used: `{exec_result.get('gas_used')}`
                            - Status: `{exec_result.get('status_message')}`
                            """)
                            
                            st.markdown(f"[🔗 View on Etherscan]({exec_result.get('explorer_url')})")
                        else:
                            st.error(f"❌ Execution failed: {exec_result.get('error')}")
            
            with col_exec2:
                if st.button("❌ Cancel", use_container_width=True):
                    # Clear session state
                    if 'parsed_tx' in st.session_state:
                        del st.session_state['parsed_tx']
                    if 'validation_result' in st.session_state:
                        del st.session_state['validation_result']
                    if 'proposal' in st.session_state:
                        del st.session_state['proposal']
                    
                    st.info("Transaction cancelled")
                    st.rerun()
        else:
            st.error("🚫 Execution blocked by Guardian")
            
            if st.button("🔄 Start New Transaction"):
                # Clear session state
                if 'parsed_tx' in st.session_state:
                    del st.session_state['parsed_tx']
                if 'validation_result' in st.session_state:
                    del st.session_state['validation_result']
                if 'proposal' in st.session_state:
                    del st.session_state['proposal']
                
                st.rerun()

# ============================================================
# PAGE: GUARDIAN
# ============================================================
elif page == "🛡️ Guardian":
    st.title("🛡️ Guardian Policy Management")
    st.markdown("**Configure security policies and manage whitelists**")
    
    tab1, tab2, tab3 = st.tabs(["📋 Current Policies", "✅ Whitelist", "🔍 Contract Lookup"])
    
    with tab1:
        st.subheader("Current Guardian Policies")
        
        try:
            policies = api.get_policies()
            
            # Transfer Limits
            st.markdown("### 💸 Transfer Limits")
            limits = policies.get('transfer_limits', {})
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Max Wallet Transfer", f"{limits.get('max_transfer_limit')} ETH")
            with col2:
                st.metric("Max Contract Value", f"{limits.get('max_contract_value')} ETH")
            
            # Gas Limits
            st.divider()
            st.markdown("### ⛽ Gas Limits")
            gas_limits = policies.get('gas_limits', {})
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Max Gas Price", f"{gas_limits.get('max_gas_price_gwei')} Gwei")
            with col2:
                st.metric("Max Gas Limit", f"{gas_limits.get('max_gas_limit'):,}")
            
            # Security Lists
            st.divider()
            st.markdown("### 🔒 Security Lists")
            
            col1, col2 = st.columns(2)
            
            with col1:
                whitelist = policies.get('whitelisted_addresses', [])
                st.metric("Whitelisted Addresses", len(whitelist))
                
                if whitelist:
                    with st.expander("View Whitelist"):
                        for addr in whitelist:
                            st.code(addr)
            
            with col2:
                blacklist = policies.get('blacklisted_addresses', [])
                st.metric("Blacklisted Addresses", len(blacklist))
                
                if blacklist:
                    with st.expander("View Blacklist"):
                        for addr in blacklist:
                            st.code(addr)
            
            # Approved Contracts
            st.divider()
            st.markdown("### ✅ Approved DeFi Protocols")
            
            approved = policies.get('approved_contracts', {})
            if approved:
                for address, name in approved.items():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(f"📝 {name}")
                    with col2:
                        st.code(f"{address[:6]}...{address[-4:]}")
            else:
                st.info("No approved contracts")
            
        except Exception as e:
            st.error(f"Failed to load policies: {str(e)}")
    
    with tab2:
        st.subheader("Manage Whitelist")
        
        new_address = st.text_input(
            "Add Address to Whitelist:",
            placeholder="0x...",
            help="Enter an Ethereum address to whitelist"
        )
        
        if st.button("➕ Add to Whitelist", type="primary"):
            if new_address:
                if not new_address.startswith('0x') or len(new_address) != 42:
                    st.error("❌ Invalid Ethereum address format")
                else:
                    with st.spinner("Adding to whitelist..."):
                        result = api.whitelist_address(new_address)
                        
                        if result.get('success'):
                            st.success(f"✅ {result.get('message')}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ Failed: {result.get('error', 'Unknown error')}")
            else:
                st.warning("Please enter an address")
        
        st.divider()
        
        # Display current whitelist
        st.markdown("### Current Whitelist")
        try:
            policies = api.get_policies()
            whitelist = policies.get('whitelisted_addresses', [])
            
            if whitelist:
                df = pd.DataFrame(whitelist, columns=["Address"])
                df.index += 1
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Whitelist is empty")
        except:
            st.error("Failed to load whitelist")
    
    with tab3:
        st.subheader("Smart Contract Lookup")
        st.markdown("Check if an address is a smart contract")
        
        lookup_address = st.text_input(
            "Enter Address:",
            placeholder="0x...",
            key="lookup_input"
        )
        
        if st.button("🔍 Check Address", type="primary"):
            if lookup_address:
                with st.spinner("Looking up address..."):
                    info = api.get_contract_info(lookup_address)
                    
                    if "error" in info:
                        st.error(f"❌ Lookup failed: {info['error']}")
                    else:
                        is_contract = info.get('is_contract', False)
                        
                        if is_contract:
                            st.success("✅ This is a Smart Contract")
                            
                            st.markdown(f"""
                            **Contract Information:**
                            - Type: `{info.get('type')}`
                            - Code Size: `{info.get('code_size')} bytes`
                            - Code Hash: `{info.get('code_hash', 'N/A')[:16]}...`
                            """)
                        else:
                            st.info("ℹ️ This is an EOA (Externally Owned Account)")
                            st.markdown("Not a smart contract - regular wallet address")
            else:
                st.warning("Please enter an address")

# ============================================================
# PAGE: ANALYTICS
# ============================================================
elif page == "📊 Analytics":
    st.title("📊 Transaction Analytics")
    st.markdown("**Historical transaction data and risk analysis**")
    
    st.info("📌 Analytics feature coming soon! This will show:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Transaction History:**
        - Total transactions processed
        - Approved vs Rejected ratio
        - Average risk scores
        - Most common violation types
        """)
    
    with col2:
        st.markdown("""
        **AI Performance:**
        - Parsing accuracy rate
        - Hallucination detection rate
        - Protocol detection success
        - Average confidence scores
        """)
    
    # Placeholder charts
    st.divider()
    
    # Mock data for demonstration
    import random
    
    st.subheader("Risk Score Distribution (Demo)")
    chart_data = pd.DataFrame({
        'Risk Score': [random.randint(0, 100) for _ in range(50)]
    })
    st.bar_chart(chart_data)
    
    st.subheader("Transaction Status (Demo)")
    status_data = pd.DataFrame({
        'Status': ['Approved', 'Rejected', 'Review'],
        'Count': [42, 15, 8]
    })
    st.bar_chart(status_data.set_index('Status'))

# ============================================================
# PAGE: SETTINGS
# ============================================================
elif page == "⚙️ Settings":
    st.title("⚙️ Settings")
    st.markdown("**System configuration and preferences**")
    
    st.subheader("Backend Configuration")
    
    backend_url = st.text_input(
        "Backend URL:",
        value="http://localhost:8000",
        disabled=True
    )
    
    st.info("ℹ️ Backend URL is currently fixed. To change it, modify the APIClient initialization in the code.")
    
    st.divider()
    
    st.subheader("About AegisChain")
    
    st.markdown("""
    **AegisChain Guardian** is an AI-powered transaction security framework designed for autonomous on-chain agents.
    
    **Features:**
    - 🤖 Natural language transaction parsing
    - 🛡️ Multi-layer security validation
    - 🔍 Hallucination detection
    - 📊 Real-time risk scoring
    - ✅ Smart contract protocol support
    - ⛓️ Sepolia testnet integration
    
    **Technology Stack:**
    - Frontend: Streamlit
    - Backend: FastAPI (Python)
    - AI: Groq (Llama 3.3 70B)
    - Blockchain: Web3.py + Alchemy
    - Network: Ethereum Sepolia
    
    **Team:** Innofusion'26
    """)
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Version", "2.0.0")
    with col2:
        st.metric("Network", "Sepolia")
    with col3:
        st.metric("Status", "Active")
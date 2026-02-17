import streamlit as st
import pandas as pd
import requests
from api_client import APIClient

# Initialize API Client
# Assuming backend is running on localhost:8000
api = APIClient(base_url="http://localhost:8000")

st.set_page_config(
    page_title="AegisChain Guardian",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .status-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
        border: 1px solid #e0e0e0;
        margin-bottom: 10px;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.title("🛡️ AegisChain")
page = st.sidebar.radio("Navigation", ["Dashboard", "AI Transaction Agent", "Guardian Policies", "Settings"])

st.sidebar.markdown("---")
st.sidebar.markdown("### System Status")
try:
    health = requests.get("http://localhost:8000/health").json()
    st.sidebar.success(f"Backend: {health.get('status', 'Unknown')}")
except:
    st.sidebar.error("Backend: Offline")

# ------------------------------------------------------------
# PAGE: DASHBOARD
# ------------------------------------------------------------
if page == "Dashboard":
    st.title("🛡️ Guardian Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Blockchain Status")
        try:
            status = api.get_blockchain_status()
            if status.get("connected"):
                st.success(f"Network: {status.get('network')}")
                st.metric("Chain ID", status.get("chain_id"))
                st.metric("Wallet Balance", f"{status.get('balance_eth')} ETH")
                st.metric("Wallet Address", status.get("wallet_address"))
            else:
                st.error("Blockchain Disconnected")
        except Exception as e:
            st.error(f"Failed to fetch status: {e}")

    with col2:
        st.subheader("Guardian Constraints")
        try:
            policies = api.get_policies()
            limits = policies.get("transfer_limits", {})
            gas = policies.get("gas_limits", {})
            st.metric("Max Transfer Limit", f"{limits.get('max_transfer_limit')} ETH")
            st.metric("Max Gas Price", f"{gas.get('max_gas_price_gwei')} Gwei")
            st.write(f"Whitelisted Addresses: {len(policies.get('whitelisted_addresses', []))}")
            st.write(f"Blacklisted Addresses: {len(policies.get('blacklisted_addresses', []))}")
        except Exception as e:
            st.error(f"Failed to fetch policies: {e}")

# ------------------------------------------------------------
# PAGE: AI TRANSACTION AGENT
# ------------------------------------------------------------
elif page == "AI Transaction Agent":
    st.title("🤖 AI Transaction Agent")
    st.markdown("Describe your transaction in plain English, and the AI will parse it for you.")

    # Input Section
    st.subheader("1. Intent Parsing")
    col_input, col_manual = st.columns([2, 1])
    
    with col_input:
        user_intent = st.text_area("Enter your intent", 
                                   value="Send 0.01 ETH to 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                                   height=100)
        parse_btn = st.button("🔍 Parse Intent", type="primary")

    with col_manual:
        st.markdown("Or use manual input override (optional)")
        manual_to = st.text_input("To Address (Optional)")
        manual_amount = st.number_input("Amount (ETH) (Optional)", min_value=0.0, format="%.4f")

    if parse_btn:
        with st.spinner("AI Agent processing..."):
            parsed_result = api.parse_intent(user_intent, manual_to if manual_to else None, manual_amount if manual_amount > 0 else None)
            
            if "error" in parsed_result:
                st.error(f"Parsing Failed: {parsed_result['error']}")
            else:
                st.session_state['parsed_tx'] = parsed_result
                st.success("Intent Parsed Successfully!")

    # Display Parsed Result & Validation
    if 'parsed_tx' in st.session_state:
        st.divider()
        st.subheader("2. Parsed Transaction Proposal")
        
        tx = st.session_state['parsed_tx']
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Recipient", f"{tx.get('to_address')[:6]}...{tx.get('to_address')[-4:]}")
        c2.metric("Amount", f"{tx.get('amount')} ETH")
        c3.metric("AI Confidence", f"{tx.get('ai_confidence')}%")
        
        st.json(tx)
        
        # Validation Button
        if st.button("🛡️ Validate with Guardian"):
            with st.spinner("Guardian Engine simulating & validating..."):
                # Prepare payload for validation
                # The validation endpoint expects: TransactionProposal
                # We need to map our parsed result to that structure
                proposal = {
                    "to_address": tx.get("to_address"),
                    "amount": tx.get("amount"),
                    "ai_confidence": tx.get("ai_confidence", 100),
                    "is_protocol_interaction": tx.get("is_protocol_interaction", False),
                    "protocol_name": tx.get("protocol_name")
                }
                
                validation_result = api.validate_transaction(proposal)
                st.session_state['validation_result'] = validation_result
                st.session_state['proposal'] = proposal # Save for execution

    # Validated Result & Execution
    if 'validation_result' in st.session_state:
        st.divider()
        st.subheader("3. Guardian Validation Results")
        
        # Determine status color
        val_res = st.session_state['validation_result']
        decision = val_res.get("final_decision", "UNKNOWN")
        
        if decision == "APPROVED":
            st.success(f"✅ Status: {decision}")
        elif decision == "Requires Review":
            st.warning(f"⚠️ Status: {decision}")
        else:
            st.error(f"❌ Status: {decision}")

        # Display Validation Metrics
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Risk Score", val_res.get("risk_analysis", {}).get("risk_score"))
        r2.metric("Gas Cost", f"{val_res.get('simulation', {}).get('max_fee_gwei')} Gwei")
        r3.metric("Policy Check", "Pass" if val_res.get("policy_check", {}).get("passed") else "Fail")
        r4.metric("Simulation", "Success" if val_res.get("simulation", {}).get("success") else "Fail")

        with st.expander("Detailed Risk Report"):
            st.json(val_res)

        # Execution Button (Only if Approved)
        if decision == "APPROVED":
            if st.button("🚀 Execute Transaction", type="primary"):
                with st.spinner("Broadcasting to Blockchain..."):
                    exec_res = api.execute_transaction(st.session_state['proposal'])
                    if "hash" in exec_res:
                         st.balloons()
                         st.success(f"Transaction Broadcasted! Hash: {exec_res['hash']}")
                         st.info(f"Explorer URL: {exec_res.get('explorer_url', '#')}")
                    else:
                        st.error(f"Execution Failed: {exec_res}")
        else:
            st.error("Execution Blocked by Guardian Policy")

# ------------------------------------------------------------
# PAGE: GUARDIAN POLICIES
# ------------------------------------------------------------
elif page == "Guardian Policies":
    st.title("🛡️ Guardian Policy Management")
    
    tab1, tab2 = st.tabs(["Whitelist", "Risk Configuration"])
    
    with tab1:
        st.subheader("Manage Whitelist")
        new_address = st.text_input("Add Address to Whitelist")
        if st.button("Add to Whitelist"):
            if new_address:
                res = api.whitelist_address(new_address)
                if res.get("success"):
                    st.success(res.get("message"))
                else:
                    st.error(f"Failed: {res}")
            else:
                st.warning("Enter an address")

        # Display current whitelist
        try:
            policies = api.get_policies()
            whitelist = policies.get("whitelisted_addresses", [])
            st.write("### Current Whitelisted Addresses")
            if whitelist:
                # Convert to DataFrame for better display
                st.dataframe(pd.DataFrame(whitelist, columns=["Address"]), use_container_width=True)
            else:
                st.info("Whitelist is empty")
        except:
             st.error("Could not load policies")

    with tab2:
        st.subheader("Current Risk Parameters")
        try:
            policies = api.get_policies()
            st.json(policies)
        except:
             st.error("Could not load policies")

elif page == "Settings":
    st.title("⚙️ Settings")
    st.write("Connected to Backend: http://localhost:8000")
    st.text_input("Backend URL", value="http://localhost:8000", disabled=True)

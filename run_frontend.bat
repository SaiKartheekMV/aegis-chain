@echo off
echo Starting AegisChain Frontend...
cd frontend
pip install -r requirements.txt
streamlit run app.py
pause

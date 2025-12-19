import streamlit as st

def load_css():
    st.markdown("""
    <style>
        /* Import Inter font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* METRIC CARDS */
        .metric-card {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            transition: transform 0.2s;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            border-color: rgba(255, 255, 255, 0.2);
        }
        .metric-value {
            font-size: 2.2rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 5px;
        }
        .metric-label {
            font-size: 0.85rem;
            color: #a0a0a0;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* STATUS BADGES */
        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-block;
        }
        .status-compliant { background-color: rgba(46, 204, 113, 0.2); color: #2ecc71; }
        .status-partial { background-color: rgba(241, 196, 15, 0.2); color: #f1c40f; }
        .status-non-compliant { background-color: rgba(231, 76, 60, 0.2); color: #e74c3c; }
        .status-evidence { background-color: rgba(149, 165, 166, 0.2); color: #95a5a6; }

        /* HEADER STYLING */
        h1, h2, h3 { color: #ffffff !important; }
        p { color: #cccccc; }

        /* SIDEBAR POLISH */
        section[data-testid="stSidebar"] {
            background-color: #0e1117;
            border-right: 1px solid #262730;
        }
    </style>
    """, unsafe_allow_html=True)
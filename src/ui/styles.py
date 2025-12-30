import streamlit as st


def load_css() -> None:
    """Inject custom CSS styles into the Streamlit app."""
    st.markdown(
        """
        <style>
            @import url(
                'https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap'
            );

            html, body, [class*="css"] {
                font-family: 'Inter', sans-serif;
            }

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

            h1, h2, h3 {
                color: #ffffff !important;
            }

            p {
                color: #cccccc;
            }

            section[data-testid="stSidebar"] {
                background-color: #0e1117;
                border-right: 1px solid #262730;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

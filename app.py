import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdx
import time
import random
from datetime import datetime, timedelta
from PIL import Image, ImageFilter

# -----------------------------------------------------------------------------
# APP CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Streamlit Pro Showcase",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://docs.streamlit.io',
        'About': "Showcase App v1.0"
    }
)

# Custom CSS for a modern, polished look
st.markdown("""
<style>
    /* Gradient headers */
    h1, h2, h3 {
        background: -webkit-linear-gradient(45deg, #FF4B4B, #FF914D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    /* Card-like styling for metrics */
    div[data-testid="stMetric"] {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
    }
    /* Dark mode adjustments (optional, purely for CSS demo) */
    @media (prefers-color-scheme: dark) {
        div[data-testid="stMetric"] {
            background-color: #262730;
        }
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# UTILITIES & CACHING
# -----------------------------------------------------------------------------

@st.cache_data(ttl=600)
def generate_market_data(rows=100):
    """
    Simulates fetching complex financial data.
    Cached to demonstrate performance optimization.
    """
    dates = pd.date_range(end=datetime.now(), periods=rows, freq='D')
    df = pd.DataFrame({
        'Date': dates,
        'Revenue': np.random.randn(rows).cumsum() + 100,
        'Users': np.random.randint(50, 200, size=rows),
        'Satisfaction': np.random.uniform(3.5, 5.0, size=rows),
        'Category': np.random.choice(['SaaS', 'E-com', 'Enterprise'], size=rows)
    })
    return df

@st.cache_resource
def load_heavy_model_simulation():
    """
    Simulates loading a heavy ML model (e.g., PyTorch/TensorFlow).
    Uses cache_resource so it only loads once per session.
    """
    time.sleep(1) # Simulate load time
    return "DummyModel_v1.0"

# Initialize Session State Variables
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'process_status' not in st.session_state:
    st.session_state.process_status = "Ready"

# -----------------------------------------------------------------------------
# PAGE MODULES
# -----------------------------------------------------------------------------

def dashboard_page():
    st.header("📊 Interactive Analytics Dashboard")
    st.markdown("Demonstrates **editable dataframes**, **Plotly integration**, and **dynamic metrics**.")

    # 1. Top Level Metrics
    df = generate_market_data()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Revenue", f"${df['Revenue'].sum():,.0f}", "+12%")
    with col2:
        st.metric("Active Users", f"{df['Users'].mean():.0f}", "-2%")
    with col3:
        st.metric("Avg Satisfaction", f"{df['Satisfaction'].mean():.2f}/5.0")
    with col4:
        st.metric("Model Status", load_heavy_model_simulation(), delta="Online", delta_color="normal")

    st.divider()

    # 2. Interactive Layout
    col_config, col_chart = st.columns([1, 2])

    with col_config:
        st.subheader("Data Controller")
        with st.expander("Filter & Settings", expanded=True):
            category = st.multiselect("Filter Category", df['Category'].unique(), default=df['Category'].unique())
            date_range = st.slider("Date Range", 
                                   min_value=df['Date'].min().date(), 
                                   max_value=df['Date'].max().date(),
                                   value=(df['Date'].min().date(), df['Date'].max().date()))
            
        st.markdown("### Editable Data")
        st.caption("Try editing cells below – the chart updates instantly!")
        
        # Filter data based on input
        mask = (df['Category'].isin(category)) & (df['Date'].dt.date >= date_range[0]) & (df['Date'].dt.date <= date_range[1])
        filtered_df = df.loc[mask]

        # Data Editor (Write-back)
        edited_df = st.data_editor(
            filtered_df,
            column_config={
                "Satisfaction": st.column_config.ProgressColumn(
                    "Satisfaction Score", format="%.2f", min_value=0, max_value=5
                ),
                "Revenue": st.column_config.NumberColumn(format="$%.2f")
            },
            hide_index=True,
            width='stretch',
            num_rows="dynamic"
        )

    with col_chart:
        st.subheader("Real-time Visualization")
        
        # Tabs for different views
        tab1, tab2 = st.tabs(["📈 Trend Analysis", "🍩 Composition"])
        
        with tab1:
            # Advanced Plotly Chart
            fig = px.area(edited_df, x='Date', y='Revenue', color='Category', 
                          line_group='Category', template='plotly_white')
            fig.update_layout(hovermode="x unified", height=400)
            st.plotly_chart(fig, width='stretch')
        
        with tab2:
            fig_pie = px.pie(edited_df, values='Users', names='Category', hole=0.4)
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, width='stretch')

def geospatial_page():
    st.header("🌍 3D Geospatial Visualization")
    st.markdown("Demonstrates **PyDeck** integration for high-performance 3D mapping.")

    row1, row2 = st.columns([3, 1])

    with row2:
        st.info("Controls")
        elevation_scale = st.slider("Elevation Scale", 10, 100, 50)
        pitch = st.slider("Camera Pitch", 0, 60, 45)
        map_style = st.selectbox("Map Style", ["dark", "light", "road"])

    with row1:
        # Generate dummy hexagonal data
        df_map = pd.DataFrame(
            np.random.randn(1000, 2) / [50, 50] + [37.77, -122.4],
            columns=['lat', 'lon']
        )
        
        # PyDeck Layer
        layer = pdx.Layer(
            "HexagonLayer",
            df_map,
            get_position=["lon", "lat"],
            auto_highlight=True,
            elevation_scale=elevation_scale,
            pickable=True,
            elevation_range=[0, 3000],
            extruded=True,
            coverage=1
        )
        
        # View State
        view_state = pdx.ViewState(
            latitude=37.77,
            longitude=-122.4,
            zoom=11,
            pitch=pitch,
        )
        
        # Render Map
        st.pydeck_chart(pdx.Deck(
            map_style=f"mapbox://styles/mapbox/{map_style}-v9",
            initial_view_state=view_state,
            layers=[layer],
            tooltip={"html": "<b>Elevation Value:</b> {elevationValue}", "style": {"color": "white"}}
        ))

def chat_ai_page():
    st.header("💬 Streaming Chat Interface")
    st.markdown("Demonstrates **session state**, **chat widgets**, and **streaming response simulation**.")

    # Container for chat history
    chat_container = st.container()

    # Helper to simulate streaming
    def stream_response(text):
        for word in text.split():
            yield word + " "
            time.sleep(0.05)

    with chat_container:
        if len(st.session_state.chat_history) == 0:
            st.info("Start a conversation! (This is a simulation)")

        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("What would you like to build?"):
        # User message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # AI Response (Simulated)
        with st.chat_message("assistant"):
            response_text = f"I received your request: '{prompt}'. As a simulated AI, I can tell you that Streamlit makes building LLM apps incredibly easy using `st.chat_message` and `st.write_stream`."
            response = st.write_stream(stream_response(response_text))
        
        st.session_state.chat_history.append({"role": "assistant", "content": response_text})

def media_lab_page():
    st.header("🎨 Media & Image Processing")
    st.markdown("Demonstrates **file uploaders**, **image manipulation (PIL)**, and **multimedia rendering**.")

    tab_img, tab_av = st.tabs(["Image Filter", "Audio/Video"])

    with tab_img:
        col_controls, col_display = st.columns([1, 2])
        
        with col_controls:
            uploaded_file = st.file_uploader("Upload an image (or leave empty)", type=['png', 'jpg'])
            filter_type = st.radio("Apply Filter", ["Original", "Blur", "Contour", "Emboss"])
            
        with col_display:
            if uploaded_file:
                image = Image.open(uploaded_file)
            else:
                # Create a generated gradient image if no upload
                array = np.linspace(0, 1, 256*256).reshape(256, 256)
                image = Image.fromarray(np.uint8(array * 255)).convert("RGB")
                st.caption("Using generated placeholder image")

            # Apply processing
            if filter_type == "Blur":
                image = image.filter(ImageFilter.BLUR)
            elif filter_type == "Contour":
                image = image.filter(ImageFilter.CONTOUR)
            elif filter_type == "Emboss":
                image = image.filter(ImageFilter.EMBOSS)
            
            st.image(image, caption=f"Result: {filter_type}", width='stretch')

    with tab_av:
        st.warning("Demo placeholders (requires actual media files for playback)")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("### Audio Waveform")
            # Create dummy audio data
            audio_data = np.random.uniform(-1, 1, 44100)
            st.line_chart(audio_data[:100], height=100)
            st.audio(np.zeros(10), sample_rate=44100) # Dummy player
        with col_b:
            st.markdown("### Video Embed")
            st.video("https://www.youtube.com/watch?v=B2iAodr0fOo") # Streamlit demo video

def status_page():
    st.header("⚡ Real-time Status & Execution")
    st.markdown("Demonstrates **st.status**, **progress bars**, and **fragments** (partial reruns).")

    st.markdown("### Long Running Process Simulation")
    
    if st.button("Start Complex Job"):
        with st.status("Initializing Systems...", expanded=True) as status:
            st.write("🔌 Connecting to database...")
            time.sleep(1)
            st.write("💾 Downloading assets...")
            time.sleep(1)
            st.write("🧠 Running inference...")
            time.sleep(1)
            status.update(label="Job Complete!", state="complete", expanded=False)
        st.success("Process finished successfully!")

    st.divider()

    st.markdown("### Partial Reruns (@st.fragment)")
    st.info("Interact with the counter below. Notice the timestamp above DOES NOT update, proving only the fragment reruns.")

    st.write(f"**Full Page Load Time:** {datetime.now().strftime('%H:%M:%S')}")

    # New feature: Fragment
    @st.fragment
    def counter_fragment():
        st.caption(f"Fragment Update Time: {datetime.now().strftime('%H:%M:%S')}")
        c1, c2 = st.columns(2)
        if c1.button("Increment +"):
            st.session_state.count = st.session_state.get('count', 0) + 1
        if c2.button("Decrement -"):
            st.session_state.count = st.session_state.get('count', 0) - 1
        
        st.metric("Fragment Counter", st.session_state.get('count', 0))

    counter_fragment()

# -----------------------------------------------------------------------------
# MAIN DISPATCHER
# -----------------------------------------------------------------------------

def main():
    # Sidebar Navigation
    with st.sidebar:
        st.title("Streamlit Pro")
        st.write("Advanced Showcase")
        
        page = st.radio("Navigate", [
            "Analytics Dashboard", 
            "Geospatial 3D", 
            "AI Chat Interface", 
            "Media Lab",
            "Real-time & Status"
        ])
        
        st.markdown("---")
        st.markdown("### Settings")
        st.toggle("Dark Mode Simulation", value=True)
        st.slider("Data Sensitivity", 0, 100, 75)
        
        st.markdown("---")
        st.caption(f"Python {platform_version()}")

    # Routing
    if page == "Analytics Dashboard":
        dashboard_page()
    elif page == "Geospatial 3D":
        geospatial_page()
    elif page == "AI Chat Interface":
        chat_ai_page()
    elif page == "Media Lab":
        media_lab_page()
    elif page == "Real-time & Status":
        status_page()

def platform_version():
    import sys
    return sys.version.split()[0]

if __name__ == "__main__":
    main()
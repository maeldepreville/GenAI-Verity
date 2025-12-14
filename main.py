import streamlit as st
import streamlit_shadcn_ui as ui
from streamlit_elements import elements, mui, html, dashboard, media, editor, nivo
from types import SimpleNamespace
import json

# -----------------------------------------------------------------------------
# 1. PAGE CONFIG & CUSTOM CSS (The "Clean Slate")
# -----------------------------------------------------------------------------
st.set_page_config(layout="wide", page_title="NextGen Dashboard", page_icon="⚡")

# Remove default Streamlit chrome to make it look like a native Web App
st.markdown("""
<style>
    /* Hide the default Streamlit Hamburger menu and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Remove the huge white padding at the top */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }

    /* Custom scrollbar for a sleeker look */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f1f1; 
    }
    ::-webkit-scrollbar-thumb {
        background: #888; 
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #555; 
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. STATE MANAGEMENT (The SPA Engine)
# -----------------------------------------------------------------------------
# We use a simple session state variable to track the "active view"
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Dashboard"

# Initialize layout for the draggable dashboard if not present
if "layout" not in st.session_state:
    st.session_state.layout = [
        # Parameters: element_identifier, x_pos, y_pos, width, height
        dashboard.Item("stats", 0, 0, 6, 2),
        dashboard.Item("editor", 6, 0, 6, 5),
        dashboard.Item("media", 0, 2, 6, 3),
    ]

# -----------------------------------------------------------------------------
# 3. COMPONENT: DRAGGABLE DASHBOARD (Streamlit Elements)
# -----------------------------------------------------------------------------
def render_draggable_dashboard():
    """
    Renders a grid where users can drag and resize widgets.
    Uses Material UI (MUI) inside Streamlit.
    """
    st.markdown("### 🖱️ Interactive Grid")
    st.caption("Try dragging the cards below or resizing them from the bottom-right corner.")

    with elements("dashboard"):
        # 1. Initialize the dashboard grid
        with dashboard.Grid(st.session_state.layout) as grid:
            
            # --- WIDGET 1: Statistics Card (MUI) ---
            with mui.Card(key="stats", sx={"display": "flex", "flexDirection": "column"}):
                mui.CardHeader(title="Real-time Metrics", subheader="Live Data Feed")
                with mui.CardContent(sx={"flex": 1, "minHeight": 0}):
                    with mui.Typography(variant="h2", component="div"):
                        mui.icon.TrendingUp()
                        html.span(" +42%", style={"color": "green", "fontSize": "0.5em"})
                    mui.Typography("Active Sessions: 1,204")
                    mui.LinearProgress(variant="determinate", value=75, sx={"marginTop": 2})

            # --- WIDGET 2: Code Editor (Monaco) ---
            with mui.Card(key="editor", sx={"display": "flex", "flexDirection": "column"}):
                mui.CardHeader(title="Live Scripting", subheader="Python 3.10 Runtime")
                with mui.CardContent(sx={"flex": 1, "minHeight": 0}):
                    editor.Monaco(
                        height="100%",
                        defaultValue="def hello():\n    print('Hello Streamlit!')",
                        language="python",
                        theme="vs-dark"
                    )

            # --- WIDGET 3: Media Player ---
            with mui.Card(key="media", sx={"display": "flex", "flexDirection": "column"}):
                mui.CardHeader(title="Media Stream", subheader="HLS / MP4 Support")
                with mui.CardContent(sx={"flex": 1, "minHeight": 0, "padding": 0}):
                   media.Player(url="https://www.youtube.com/watch?v=B2iAodr0fOo", controls=True, width="100%", height="100%")

# -----------------------------------------------------------------------------
# 4. COMPONENT: MODERN SETTINGS FORM (Streamlit Shadcn UI)
# -----------------------------------------------------------------------------
def render_modern_settings():
    """
    Renders a clean, aesthetic settings page using Shadcn components.
    """
    st.markdown("### ⚙️ User Preferences")
    
    # Grid Layout for Cards
    col1, col2 = st.columns(2)

    with col1:
        # Shadcn Card
        with ui.card(key="profile_card"):
            ui.element("span", children=["Profile Settings"], className="text-gray-500 text-sm font-medium")
            ui.element("h3", children=["Personal Information"], className="text-xl font-bold text-gray-900")
            
            st.markdown("---")
            ui.input(default_value="jdoe@example.com", placeholder="Email Address", key="email_input")
            ui.select(options=["Admin", "Editor", "Viewer"], default_value="Admin", key="role_select")
            
            # Shadcn Button
            if ui.button("Save Changes", key="save_btn", className="bg-black text-white hover:bg-gray-800"):
                ui.badges(badge_list=[("Success", "default")], key="saved_badge")

    with col2:
        with ui.card(key="security_card"):
            ui.element("span", children=["Security"], className="text-red-500 text-sm font-medium")
            ui.element("h3", children=["2FA & Session"], className="text-xl font-bold text-gray-900")
            
            st.markdown("---")
            ui.switch(default_checked=True, label="Enable 2-Factor Auth", key="2fa_switch")
            ui.switch(default_checked=False, label="Allow API Access", key="api_switch")
            
            st.caption("Last active: 2 minutes ago")

# -----------------------------------------------------------------------------
# 5. MAIN ROUTER & NAVIGATION (The "App" wrapper)
# -----------------------------------------------------------------------------
def main():
    # --- Top Navigation Bar (Shadcn Tabs) ---
    # This acts as our Router. It sits at the top like a native app header.
    
    # We use columns to create a header layout: [Logo | Navigation | Avatar]
    head1, head2, head3 = st.columns([1, 2, 1])
    
    with head1:
        st.markdown("### ⚡ **PRO**DASH")
    
    with head2:
        # The Shadcn Tab component acting as a menu
        # Note: We bind this to a local var, handling state change manually if needed, 
        # or relying on the rerun behavior.
        chosen_tab = ui.tabs(options=['Mission Control', 'Settings'], default_value='Mission Control', key="nav_tabs")
    
    with head3:
        # A fake avatar using Shadcn Avatar (simulated via metric or badge for now)
        st.markdown("<div style='text-align: right;'>👤 Admin User</div>", unsafe_allow_html=True)

    st.markdown("---")

    # --- Router Logic ---
    if chosen_tab == "Mission Control":
        render_draggable_dashboard()
    elif chosen_tab == "Settings":
        render_modern_settings()

if __name__ == "__main__":
    main()
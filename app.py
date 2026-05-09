# app.py
import streamlit as st
import os

# ── MUST be the very first Streamlit call ──
st.set_page_config(
    page_title="LifeLine Blood Bank",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Initialize session state BEFORE any render calls ──
if "user_score" not in st.session_state:
    st.session_state.user_score = 0
if "donations" not in st.session_state:
    st.session_state.donations = []
if "requests" not in st.session_state:
    st.session_state.requests = []
if "last_donation_date" not in st.session_state:
    st.session_state.last_donation_date = None
if "subscribed" not in st.session_state:
    st.session_state.subscribed = False
if "subscription_locations" not in st.session_state:
    st.session_state.subscription_locations = []
if "patients_saved" not in st.session_state:
    st.session_state.patients_saved = 142
if "page" not in st.session_state:
    st.session_state.page = "home"
if "selected_blood_group_req" not in st.session_state:
    st.session_state.selected_blood_group_req = None
if "selected_blood_group_don" not in st.session_state:
    st.session_state.selected_blood_group_don = None
if "show_subscription" not in st.session_state:
    st.session_state.show_subscription = False
if "saved_records" not in st.session_state:
    st.session_state.saved_records = []
if "notifications" not in st.session_state:
    st.session_state.notifications = []

# ── Load global CSS ──
css_path = os.path.join(os.path.dirname(__file__), "styles", "global.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Fix page scroll ──
st.markdown("""
    <style>
        section.main {
            overflow: hidden !important;
            height: 100vh !important;
        }
        section.main > div.block-container {
            height: 100vh !important;
            overflow-y: auto !important;
            padding-top: 2rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# ── Sidebar ──
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <span class="drop">🩸</span>
        <div>
            <div class="brand">LifeLine</div>
            <div class="tagline">Every Drop Counts</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Compute unsent notification count for badge
    n_unsent = sum(
        1 for n in st.session_state.notifications
        if not n.get("email_sent")
    )

    nav_items = {
        "home":          ("🏠", "Home"),
        "requestors":    ("🏥", "Requestors"),
        "donators":      ("💉", "Donators"),
        "blood_tracker": ("🗺️", "Blood GPS Tracker"),
        "user_details":  ("📂", f"User Details{'  🔴' if n_unsent else ''}"),
    }

    for key, (icon, label) in nav_items.items():
        if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
            st.session_state.page = key
            st.session_state.selected_blood_group_req = None
            st.session_state.selected_blood_group_don = None
            st.rerun()

    st.markdown("---")
    st.markdown(f"""
    <div class="score-sidebar">
        <div class="score-label">Your Score</div>
        <div class="score-value">{st.session_state.user_score} pts</div>
        <div class="score-tier">{'🥇 Gold Donor' if st.session_state.user_score >= 300 else '🥈 Silver Donor' if st.session_state.user_score >= 150 else '🩸 New Donor'}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Notification summary strip ──
    if st.session_state.notifications:
        total_n  = len(st.session_state.notifications)
        n_pending = sum(1 for n in st.session_state.notifications if n["status"] == "pending")
        st.markdown("---")
        st.markdown(f"""
        <div style="padding: 10px 12px; background: rgba(230,126,34,0.1);
                    border-radius: 8px; border-left: 3px solid #E67E22;">
            <div style="font-size:0.78rem; color:#E67E22; font-weight:700; margin-bottom:4px;">
                📧 NOTIFICATIONS
            </div>
            <div style="font-size:0.82rem; color:#D0B0B0;">
                {total_n} match(es) · {n_pending} pending
            </div>
            {'<div style="font-size:0.75rem; color:#E67E22; margin-top:4px;">⚠ ' + str(n_unsent) + ' email(s) unsent</div>' if n_unsent else ''}
        </div>
        """, unsafe_allow_html=True)

# ── Route pages ──
if st.session_state.page == "home":
    from views.home import render
    render()
elif st.session_state.page == "requestors":
    from views.requestors import render
    render()
elif st.session_state.page == "donators":
    from views.donators import render
    render()
elif st.session_state.page == "blood_tracker":
    from views.blood_tracker import render
    render()
elif st.session_state.page == "user_details":
    from views.user_details import render
    render()
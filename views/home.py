#home.py
import streamlit as st


def render():
    # ── Hero ──
    st.markdown("""
    <div class="page-hero">
        <h1>LifeLine Blood Bank</h1>
        <p>Serving Bengaluru's communities — one drop at a time.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── KPIs ──
    st.markdown('<div class="section-title">Live Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Real-time vitals of our blood bank network</div>', unsafe_allow_html=True)

    score = st.session_state.user_score
    patients = st.session_state.patients_saved + len(st.session_state.donations) * 3

    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-icon">📍</div>
            <div class="kpi-value">12</div>
            <div class="kpi-label">Localities Covered</div>
            <div class="kpi-sub">Bengaluru Urban & Rural</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">❤️</div>
            <div class="kpi-value">{patients:,}</div>
            <div class="kpi-label">Patients Saved</div>
            <div class="kpi-sub">Since January 2022</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">🚨</div>
            <div class="kpi-value">3</div>
            <div class="kpi-label">Emergency Contacts</div>
            <div class="kpi-sub">+91 98450-00001 · 1910</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">⭐</div>
            <div class="kpi-value">{score}</div>
            <div class="kpi-label">Your Score</div>
            <div class="kpi-sub">{'🥇 Gold Donor' if score >= 300 else '🥈 Silver' if score >= 150 else '🩸 New Donor'}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Feature Preview ──
    st.markdown("---")
    st.markdown('<div class="section-title">How LifeLine Works</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Two simple flows — for those who need and those who give</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-flex">
        <div class="feature-card">
            <h3>🏥 For Requestors</h3>
            <p>If you or a loved one urgently needs blood, navigate to the Requestors page. 
            Choose a blood group, fill in your hospital details, and submit. 
            Our team mobilises within the hour.</p>
            <span class="pill">A+</span>
            <span class="pill">B-</span>
            <span class="pill">O+</span>
            <span class="pill">AB+</span>
            <span class="pill">All 8 Groups</span>
            <br><br>
            <span class="pill">📋 Name & Address</span>
            <span class="pill">🏥 Hospital</span>
            <span class="pill">💉 Quantity (ml)</span>
        </div>
        <div class="feature-card">
            <h3>💉 For Donators</h3>
            <p>Heroes live here. Pick a blood group, appoint yourself at a nearby location, 
            and schedule your donation. Earn points, unlock tiers, and get real discounts 
            at partner hospitals.</p>
            <span class="pill">📅 Schedule a Date</span>
            <span class="pill">📍 Pick Location</span>
            <span class="pill">⭐ Earn Points</span>
            <br><br>
            <span class="pill">🥇 Gold: 300pts</span>
            <span class="pill">🥈 Silver: 150pts</span>
            <span class="pill">🩸 New: 0pts</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Gamification explainer ──
    st.markdown("---")
    st.markdown('<div class="section-title">🎮 The Donor Rewards Programme</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Every donation earns you points redeemable at partner healthcare stores</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="kpi-card" style="text-align:center">
            <div class="kpi-icon">🩸</div>
            <div class="kpi-value" style="font-size:1.4rem">New Donor</div>
            <div class="kpi-label">0 – 149 pts</div>
            <div class="kpi-sub">5% off medical supplies</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="kpi-card" style="text-align:center">
            <div class="kpi-icon">🥈</div>
            <div class="kpi-value" style="font-size:1.4rem">Silver Donor</div>
            <div class="kpi-label">150 – 299 pts</div>
            <div class="kpi-sub">12% off diagnostics & labs</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="kpi-card" style="text-align:center">
            <div class="kpi-icon">🥇</div>
            <div class="kpi-value" style="font-size:1.4rem">Gold Donor</div>
            <div class="kpi-label">300+ pts</div>
            <div class="kpi-sub">20% off + priority care</div>
        </div>
        """, unsafe_allow_html=True)

    # ── About ──
    st.markdown("---")
    st.markdown("""
    <div class="about-section">
        <h2>About LifeLine</h2>
        <p>
            LifeLine is Bengaluru's community-driven blood bank, founded on the belief that no life 
            should be lost due to a shortage of blood. We connect voluntary donors with patients across 
            12 localities — from Indiranagar to Yelahanka — operating 24 × 7 with a dedicated emergency 
            response team. Every donor is a hero & every drop is a promise kept.
        </p>
        <p style="margin-top:12px">
            We are partnered with 40+ hospitals and clinics across the city, and our gamified rewards 
            programme ensures donors are recognised and rewarded for their lifesaving generosity. 
            Join 8,000+ registered donors on LifeLine today.
        </p>
        <div class="about-stats">
            <div class="about-stat">
                <div class="about-stat-val">8,000+</div>
                <div class="about-stat-lbl">Registered Donors</div>
            </div>
            <div class="about-stat">
                <div class="about-stat-val">40+</div>
                <div class="about-stat-lbl">Partner Hospitals</div>
            </div>
            <div class="about-stat">
                <div class="about-stat-val">24 × 7</div>
                <div class="about-stat-lbl">Emergency Response</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

import streamlit as st
from datetime import date, timedelta
import csv, io, re

# ── Email alert utility ──
from utils.email_alert import send_blood_alert_email

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

# ── Donor Compatibility: blood_group → list of recipient blood groups ──────────
DONOR_COMPATIBILITY = {
    "O+":  ["O+", "A+", "B+", "AB+"],
    "O-":  ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"],  # universal donor
    "A+":  ["A+", "AB+"],
    "A-":  ["A+", "A-", "AB+", "AB-"],
    "B+":  ["B+", "AB+"],
    "B-":  ["B+", "B-", "AB+", "AB-"],
    "AB+": ["AB+"],
    "AB-": ["AB+", "AB-"],
}

LOCATIONS = [
    "Indiranagar Community Centre",
    "Koramangala Blood Camp",
    "Whitefield Health Hub",
    "Jayanagar District Hospital",
    "Rajajinagar Civic Centre",
    "Malleshwaram Park Grounds",
    "Yelahanka New Town",
    "HSR Layout Blood Drive",
    "BTM Layout Camp",
    "Hebbal Sports Complex",
]

POINT_VALUE = 100  # points per donation


def _days_since_last_donation() -> int | None:
    if st.session_state.last_donation_date is None:
        return None
    return (date.today() - st.session_state.last_donation_date).days


def _is_valid_contact(contact: str) -> bool:
    digits = contact.replace("+", "").replace(" ", "").replace("-", "")
    return digits.isdigit() and 10 <= len(digits) <= 15


def _is_valid_name(name: str) -> bool:
    return bool(re.match(r"^[A-Za-z\s]+$", name.strip()))


def _is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email.strip()))


def _make_csv_bytes(record: dict) -> bytes:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=record.keys())
    writer.writeheader()
    writer.writerow(record)
    return output.getvalue().encode("utf-8")


def _safe_filename(name: str, contact: str) -> str:
    safe_name = re.sub(r"[^\w\s-]", "", name).strip().replace(" ", "_")
    digits = contact.replace("+", "").replace(" ", "").replace("-", "")
    return f"{safe_name}_{digits}.csv"


# ── Notification helpers ──────────────────────────────────────────────────────

def _find_matching_requests(blood_group: str):
    """
    Return all open requests whose blood group is compatible with this donor.
    Uses DONOR_COMPATIBILITY rules — not just exact blood group match.
    """
    compatible_recipients = DONOR_COMPATIBILITY.get(blood_group, [blood_group])
    return [
        r for r in st.session_state.get("saved_records", [])
        if r["record"].get("type") == "Request"
        and r["record"].get("blood_group") in compatible_recipients
        and not r.get("matched")
    ]


def _build_email_preview(requestor: dict, donor: dict) -> str:
    """Build a short text preview of the email that will be sent."""
    return (
        f"Dear {requestor['name']}, a {donor['blood_group']} donor has been matched "
        f"to your {requestor.get('blood_group', '')} blood request. "
        f"{donor['name']} is scheduled to donate at {donor['location']} "
        f"on {donor['date']} at {donor['time_slot']}. "
        f"Donor contact: {donor['contact']}. — LifeLine Blood Bank"
    )


def _dispatch_notifications(donation_record: dict):
    """
    Match the new donation against open compatible requests,
    create notifications, and send email alerts to ALL matched requestors.
    """
    if "notifications" not in st.session_state:
        st.session_state.notifications = []

    if "email_alert_results" not in st.session_state:
        st.session_state.email_alert_results = []

    matches = _find_matching_requests(donation_record["blood_group"])

    for saved in matches:
        req = saved["record"]
        email_preview = _build_email_preview(req, donation_record)

        notification = {
            "id": f"notif_{len(st.session_state.notifications)}",
            "type": "match",
            "status": "pending",
            "blood_group": donation_record["blood_group"],
            # Requestor info
            "requestor_name":     req["name"],
            "requestor_contact":  req["contact"],
            "requestor_email":    req.get("email", ""),
            "requestor_hospital": req.get("hospital", "—"),
            "requestor_urgency":  req.get("urgency", "—"),
            # Donor info
            "donor_name":     donation_record["name"],
            "donor_contact":  donation_record["contact"],
            "donor_email":    donation_record["email"],
            "donor_location": donation_record["location"],
            "donor_date":     donation_record["date"],
            "donor_time":     donation_record["time_slot"],
            # Email payload (replaces old SMS fields)
            "email_to":      req.get("email", ""),
            "email_preview": email_preview,
            "email_sent":    False,
            "created_at": str(date.today()),
            # Auto-email tracking
            "email_alert_sent":   False,
            "email_alert_status": None,
        }

        # ── Auto-fire email alert for ALL matches ─────────────────────────────
        requestor_email = req.get("email", "")
        urgency         = req.get("urgency", "Standard")

        if requestor_email:
            success, msg = send_blood_alert_email(
                requestor_name  = req["name"],
                requestor_email = requestor_email,
                blood_group     = donation_record["blood_group"],
                hospital        = req.get("hospital", "—"),
                quantity_ml     = req.get("quantity_ml", 0),
                urgency         = urgency,
                donor_name      = donation_record["name"],
                donor_phone     = donation_record["contact"],
                donor_email     = donation_record["email"],
                donor_location  = donation_record["location"],
                donor_date      = donation_record["date"],
                donor_time      = donation_record["time_slot"],
            )
            notification["email_alert_sent"]   = success
            notification["email_alert_status"] = msg
            if success:
                notification["email_sent"] = True   # mark as sent on auto-fire

            # Store result for post-submission UI feedback
            st.session_state.email_alert_results.append({
                "requestor": req["name"],
                "email":     requestor_email,
                "urgency":   urgency,
                "success":   success,
                "message":   msg,
            })

        st.session_state.notifications.append(notification)

        # Mark the request record as matched
        saved["matched"]       = True
        saved["matched_donor"] = donation_record["name"]


# ─────────────────────────────────────────────────────────────────────────────

def render():
    if st.session_state.get("show_subscription"):
        _render_subscription()
    elif st.session_state.selected_blood_group_don:
        _render_donation_form(st.session_state.selected_blood_group_don)
    else:
        _render_blood_grid()


def _render_blood_grid():
    st.markdown("""
    <div class="page-hero">
        <h1>Become a Donor</h1>
        <p>Choose a blood group to schedule your donation appointment today.</p>
    </div>
    """, unsafe_allow_html=True)

    days_since = _days_since_last_donation()

    if days_since is not None and days_since < 56:
        remaining = 56 - days_since
        st.markdown(f"""
        <div class="warning-banner">
            <h3>⏳ Cooldown Active — {remaining} days remaining</h3>
            <p>You donated {days_since} days ago. For your safety, you can donate again after 56 days.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Choose Blood Group to Donate</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">All blood types are valuable — even rare ones save lives</div>', unsafe_allow_html=True)

    row1, row2 = BLOOD_GROUPS[:4], BLOOD_GROUPS[4:]
    for row in [row1, row2]:
        cols = st.columns(4)
        for i, bg in enumerate(row):
            compatible_with = DONOR_COMPATIBILITY.get(bg, [bg])
            with cols[i]:
                st.markdown(f"""
                <div class="blood-card">
                    <div class="blood-type">{bg}</div>
                    <div class="blood-label">Blood Group</div>
                    <div class="blood-availability avail-mid">💉 Accepting Donors</div>
                    <div style="font-size:0.65rem;color:#9A7070;margin-top:6px;">
                        Can donate to: {', '.join(compatible_with)}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                disabled = days_since is not None and days_since < 56
                btn_label = f"Donate {bg}" if not disabled else f"⏳ {56 - days_since}d left"
                if st.button(btn_label, key=f"don_{bg}", use_container_width=True, disabled=disabled):
                    st.session_state.selected_blood_group_don = bg
                    st.rerun()

    st.markdown("---")
    _render_score_card()


def _render_donation_form(bg: str):
    col_back, _ = st.columns([1, 5])
    with col_back:
        if st.button("← Back"):
            st.session_state.selected_blood_group_don = None
            st.rerun()

    compatible_with = DONOR_COMPATIBILITY.get(bg, [bg])
    st.markdown(f"""
    <div class="page-hero">
        <h1>Donation Appointment</h1>
        <p>Scheduling your <strong>{bg}</strong> blood donation — thank you for saving a life.</p>
        <p style="font-size:0.85rem;opacity:0.8;">
            Your <strong>{bg}</strong> blood can be donated to: <strong>{', '.join(compatible_with)}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="instruction-box">
        <h4>📋 Before You Donate — Important Instructions</h4>
        <ul>
            <li><strong>Hydrate:</strong> Drink at least 500 ml of water in the 2 hours before donating.</li>
            <li><strong>Eat a meal:</strong> Have a light meal at least 3–4 hours before. Avoid fatty foods.</li>
            <li><strong>Sleep:</strong> Get at least 7 hours the night before.</li>
            <li><strong>No alcohol:</strong> Avoid for 24 hours before and after donating.</li>
            <li><strong>No blood-thinning medications:</strong> Consult your doctor if you take aspirin or ibuprofen.</li>
            <li><strong>Weight &amp; Age:</strong> At least 18 years old and weigh at least 50 kg.</li>
            <li><strong>Not eligible if:</strong> Tattoo/piercing in past 6 months, recent surgery, or active infection.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f'<span class="blood-badge">{bg}</span>', unsafe_allow_html=True)

    with st.form("donation_form", clear_on_submit=False):
        st.markdown('<div class="form-title" style="color:white;">Your Appointment Details</div>', unsafe_allow_html=True)
        st.markdown('<div class="form-sub">Fill in the details below to confirm your slot.</div>', unsafe_allow_html=True)

        name = st.text_input("👤 Full Name", placeholder="e.g. Priya Krishnan", key="don_name")

        col1, col2 = st.columns(2)
        with col1:
            gender = st.selectbox("⚧ Gender", ["Male", "Female", "Non-binary", "Prefer not to say"], key="don_gender")
        with col2:
            age = st.number_input("🎂 Age", min_value=18, max_value=65, value=25, step=1, key="don_age")

        donation_date = st.date_input(
            "📅 Preferred Donation Date",
            min_value=date.today() + timedelta(days=1),
            max_value=date.today() + timedelta(days=60),
            key="don_date"
        )

        location = st.selectbox("📍 Preferred Donation Location", LOCATIONS, key="don_location")

        col3, col4 = st.columns(2)
        with col3:
            time_slot = st.selectbox("⏰ Time Slot",
                ["9:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "2:00 PM", "3:00 PM", "4:00 PM"],
                key="don_time")
        with col4:
            contact = st.text_input("📞 Contact Number", placeholder="+91 XXXXX XXXXX", key="don_contact")

        email = st.text_input("📧 Email Address",
            placeholder="e.g. priya.krishnan@gmail.com", key="don_email")

        confirmed = st.checkbox(
            " I have read and will follow all pre-donation instructions", key="don_confirmed")
        eligible = st.checkbox(
            " I confirm I am eligible to donate blood (age 18–65, weight ≥ 50 kg, no recent surgery or illness)",
            key="don_eligible")

        submitted = st.form_submit_button("💉 Confirm Appointment", use_container_width=True)

    if submitted:
        # Clear previous email alert results
        st.session_state.email_alert_results = []

        errors = []
        if not name.strip():
            errors.append("Full name is required.")
        elif not _is_valid_name(name):
            errors.append("Name must contain letters only — no numbers or special characters.")
        if not contact.strip():
            errors.append("Contact number is required.")
        elif not _is_valid_contact(contact):
            errors.append("Contact number must contain only digits (10–15 digits). No letters or special characters.")
        if not email.strip():
            errors.append("Email address is required.")
        elif not _is_valid_email(email):
            errors.append("Please enter a valid email address.")
        if not confirmed:
            errors.append("Please confirm you have read the pre-donation instructions.")
        if not eligible:
            errors.append("Please confirm you are eligible to donate.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            record = {
                "type":       "Donation",
                "blood_group": bg,
                "name":       name.strip(),
                "gender":     gender,
                "age":        age,
                "contact":    contact.strip(),
                "email":      email.strip(),
                "location":   location,
                "date":       str(donation_date),
                "time_slot":  time_slot,
            }

            st.session_state.last_donation_date = date.today()
            st.session_state.user_score += POINT_VALUE
            st.session_state.donations.append(record)

            csv_bytes = _make_csv_bytes(record)
            filename  = _safe_filename(name.strip(), contact.strip())
            st.session_state.saved_records.append({
                "filename":     filename,
                "csv_bytes":    csv_bytes,
                "record":       record,
                "submitted_at": str(date.today()),
            })

            # ── Match against open compatible requests & fire email alerts ──
            _dispatch_notifications(record)

            n_matches = len([
                n for n in st.session_state.get("notifications", [])
                if n.get("donor_name") == name.strip()
                and n.get("donor_date") == str(donation_date)
            ])

            st.markdown(f"""
            <div class="success-banner">
                <h3>🎉 Appointment Confirmed!</h3>
                <p>You're scheduled to donate <strong>{bg}</strong> blood at <strong>{location}</strong>
                on <strong>{donation_date}</strong> at <strong>{time_slot}</strong>.
                You earned <strong>+{POINT_VALUE} points</strong>!
                New score: <strong>{st.session_state.user_score} pts</strong></p>
            </div>
            """, unsafe_allow_html=True)

            if n_matches > 0:
                st.markdown(f"""
                <div class="instruction-box" style="border-left: 4px solid #27AE60; background: rgba(39,174,96,0.08);">
                    <h4>📧 {n_matches} Requestor(s) Notified!</h4>
                    <p>We found <strong>{n_matches}</strong> pending blood request(s) compatible with your <strong>{bg}</strong> donation.
                    Email alerts have been sent to matched requestors with your donation location details.
                    You can view notification details in the <strong>User Details → Notifications</strong> tab.</p>
                </div>
                """, unsafe_allow_html=True)

            # ── Show email alert results ──────────────────────────────────
            for result in st.session_state.get("email_alert_results", []):
                if result["success"]:
                    st.markdown(f"""
                    <div style="padding:12px 16px; background:rgba(39,174,96,0.10);
                                border-left:4px solid #27AE60; border-radius:8px; margin-top:10px;">
                        <strong>📧 Email Alert Sent</strong><br/>
                        <span style="font-size:0.88rem; color:#555;">
                            An alert email was sent to
                            <strong>{result['requestor']}</strong> ({result['email']})
                            with your donation location and contact details.
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning(
                        f"⚠️ Email alert for {result['requestor']} could not be sent: {result['message']}"
                    )

            st.balloons()

            st.download_button(
                label="⬇️ Download Your Appointment Details (CSV)",
                data=csv_bytes,
                file_name=filename,
                mime="text/csv",
                key="don_download"
            )

            st.session_state.show_subscription = True
            st.session_state.selected_blood_group_don = None


def _render_subscription():
    st.markdown("""
    <div class="page-hero">
        <h1>🔔 Stay in the Loop</h1>
        <p>Subscribe to get notified when blood is urgently needed in your area.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="instruction-box">
        <h4>💡 Why Subscribe?</h4>
        <ul>
            <li>Receive email alerts when there's a shortage in your preferred locations.</li>
            <li>Be the first hero on the scene — scheduled reminders every 56 days.</li>
            <li>Earn <strong>bonus 25 points</strong> for every donation made as a response to an alert.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    with st.form("subscription_form", clear_on_submit=False):
        st.markdown("### Choose Your Preferred Locations")
        selected = st.multiselect("📍 Locations to watch", LOCATIONS, default=LOCATIONS[:2], key="sub_locations")
        email = st.text_input("📧 Email Address", placeholder="you@example.com", key="sub_email")
        phone = st.text_input("📱 Phone Number (optional)", placeholder="+91 XXXXX XXXXX", key="sub_phone")
        frequency = st.selectbox("🔔 Alert Frequency",
            ["Urgent only", "Weekly digest", "Every shortage"], key="sub_freq")
        sub_submitted = st.form_submit_button("✅ Subscribe Now", use_container_width=True)

    if st.button("Skip for now →", key="skip_sub"):
        st.session_state.show_subscription = False
        st.rerun()

    if sub_submitted:
        errors = []
        if not email.strip():
            errors.append("Email address is required.")
        elif not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email.strip()):
            errors.append("Please enter a valid email address.")
        if not selected:
            errors.append("Please select at least one location.")
        if phone.strip() and not _is_valid_contact(phone):
            errors.append("Phone number must contain only digits (10–15 digits).")

        if errors:
            for e in errors:
                st.error(e)
        else:
            st.session_state.subscribed = True
            st.session_state.subscription_locations = selected
            st.success("🎉 You're Subscribed! We'll alert you whenever blood is needed in your chosen locations.")
            if st.button("Go to My Score Card →", key="goto_score"):
                st.session_state.show_subscription = False
                st.rerun()


def _render_score_card():
    score = st.session_state.user_score
    tier = "🥇 Gold Donor" if score >= 300 else "🥈 Silver Donor" if score >= 150 else "🩸 New Donor"
    discount = "20%" if score >= 300 else "12%" if score >= 150 else "5%"
    donations_count = len(st.session_state.donations)

    st.markdown('<div class="section-title">🎮 Your Donor Score Card</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Show this card at partner hospitals to claim your discount</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(f"""
        <div class="score-card-display">
            <div class="score-card-name">LifeLine Donor Card</div>
            <div class="score-card-pts">{score}</div>
            <div style="font-size:0.85rem; color:#9A7070; margin-top:4px;">POINTS</div>
            <div class="score-card-tier">{tier}</div>
            <div style="margin-top:16px; padding:12px; background:rgba(255,255,255,0.05); border-radius:10px;">
                <div style="color:#D4A017; font-weight:700; font-size:1.1rem">{discount} Healthcare Discount</div>
                <div style="color:#9A7070; font-size:0.78rem; margin-top:4px">Valid at 40+ partner hospitals</div>
            </div>
            <div style="display:flex; justify-content:center; gap:24px; margin-top:16px;">
                <div style="text-align:center">
                    <div style="color:#FF6B6B; font-size:1.3rem; font-weight:700">{donations_count}</div>
                    <div style="color:#9A7070; font-size:0.72rem">Donations</div>
                </div>
                <div style="text-align:center">
                    <div style="color:#FF6B6B; font-size:1.3rem; font-weight:700">{donations_count * 3}</div>
                    <div style="color:#9A7070; font-size:0.72rem">Lives Touched</div>
                </div>
            </div>
            <div class="score-card-hint">Present this screen at the hospital reception</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("#### 🏆 How to Climb the Ranks")
        if score < 150:
            progress = f"**{150 - score} more points** to reach 🥈 Silver Donor"
        elif score < 300:
            progress = f"**{300 - score} more points** to reach 🥇 Gold Donor"
        else:
            progress = "🎉 You are at the **highest tier**! You're a LifeLine legend."

        st.markdown(f"""
        - Each donation earns **{POINT_VALUE} points**
        - Responding to an alert earns **+25 bonus points**
        - {progress}
        """)

        st.markdown("#### 🏥 Partner Discount Locations")
        st.markdown("""
        - Manipal Hospital Network
        - Apollo Pharmacy & Clinics
        - MedPlus Health Stores
        - Narayana Health Group
        - Fortis Diagnostic Centres
        """)

        if st.session_state.subscribed:
            st.success(f"🔔 Subscribed to alerts for {len(st.session_state.subscription_locations)} location(s)")
        else:
            st.info("💡 Subscribe to donation alerts to earn bonus points!")
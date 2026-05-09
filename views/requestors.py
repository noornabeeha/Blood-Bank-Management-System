import streamlit as st
import csv, io, re
from datetime import date

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
AVAILABILITY = {
    "A+":  ("High",   "avail-high", "✅"),
    "A-":  ("Low",    "avail-low",  "⚠️"),
    "B+":  ("High",   "avail-high", "✅"),
    "B-":  ("Low",    "avail-low",  "⚠️"),
    "AB+": ("Medium", "avail-mid",  "🟡"),
    "AB-": ("Low",    "avail-low",  "⚠️"),
    "O+":  ("High",   "avail-high", "✅"),
    "O-":  ("Medium", "avail-mid",  "🟡"),
}

HOSPITALS = [
    "Manipal Hospital, Old Airport Road",
    "St. John's Medical College Hospital",
    "Narayana Health City",
    "Fortis Hospital, Bannerghatta Road",
    "Apollo Hospital, Bannerghatta",
    "Sakra World Hospital",
    "Columbia Asia Hospital",
    "Victoria Hospital",
    "Bowring and Lady Curzon Hospital",
    "Other",
]


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


def render():
    if st.session_state.selected_blood_group_req:
        _render_request_form(st.session_state.selected_blood_group_req)
    else:
        _render_blood_grid()


def _render_blood_grid():
    st.markdown("""
    <div class="page-hero" style="background: linear-gradient(135deg, #1A0A0A, #3D0A0A);">
        <h1>Request Blood</h1>
        <p>Select a blood group below. We'll connect you with a donor as fast as possible.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Choose Blood Group</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Click on the required blood group to fill your request form</div>', unsafe_allow_html=True)

    row1, row2 = BLOOD_GROUPS[:4], BLOOD_GROUPS[4:]
    for row in [row1, row2]:
        cols = st.columns(4)
        for i, bg in enumerate(row):
            level, cls, icon = AVAILABILITY[bg]
            with cols[i]:
                st.markdown(f"""
                <div class="blood-card">
                    <div class="blood-type">{bg}</div>
                    <div class="blood-label">Blood Group</div>
                    <div class="blood-availability {cls}">{icon} {level} Supply</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Request {bg}", key=f"req_{bg}", use_container_width=True):
                    st.session_state.selected_blood_group_req = bg
                    st.rerun()

    st.markdown("---")
    st.markdown("""
    <div class="instruction-box">
        <h4>ℹ️ How Blood Requests Work</h4>
        <ul>
            <li>Submit your request with hospital and quantity details.</li>
            <li>Our coordination team will call you within <strong>30 minutes</strong> to confirm availability.</li>
            <li>For life-threatening emergencies, call <strong>+91 98450-00001</strong> directly.</li>
            <li>Requests are fulfilled in order of medical urgency, not submission time.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


def _render_request_form(bg: str):
    col_back, _ = st.columns([1, 5])
    with col_back:
        if st.button("← Back"):
            st.session_state.selected_blood_group_req = None
            st.rerun()

    st.markdown(f"""
    <div class="page-hero" style="background: linear-gradient(135deg, #1A0A0A, #3D0A0A);">
        <h1>Blood Request Form</h1>
        <p>Filling request for blood group <strong>{bg}</strong></p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f'<span class="blood-badge">{bg}</span>', unsafe_allow_html=True)

    # ── clear_on_submit=False keeps values visible after hitting submit ──
    with st.form("request_form", clear_on_submit=False):
        st.markdown('<div class="form-title" style="color:white;">Patient &amp; Request Details</div>', unsafe_allow_html=True)
        st.markdown('<div class="form-sub">All fields are required. Our team will verify details before dispatch.</div>', unsafe_allow_html=True)

        name = st.text_input("👤 Patient / Guardian Name",
            placeholder="e.g. Rahul Sharma", key="req_name")
        address = st.text_area("📍 Patient Address",
            placeholder="Full address including landmark, pincode", key="req_address")

        hospital_choice = st.selectbox("🏥 Hospital / Medical Centre", HOSPITALS, key="req_hospital")
        other_hospital = ""
        if hospital_choice == "Other":
            other_hospital = st.text_input("Enter Hospital Name", key="req_other_hospital")

        col1, col2 = st.columns(2)
        with col1:
            quantity = st.number_input("💉 Quantity Needed (ml)",
                min_value=100, max_value=5000, step=50, value=450, key="req_quantity")
        with col2:
            urgency = st.selectbox("🚨 Urgency Level",
                ["Standard (within 24h)", "Urgent (within 6h)", "Emergency (within 1h)"],
                key="req_urgency")

        contact = st.text_input("📞 Contact Number",
            placeholder="+91 XXXXX XXXXX", key="req_contact")

        email = st.text_input("📧 Email Address",
            placeholder="e.g. rahul.sharma@gmail.com", key="req_email")

        notes = st.text_area("📝 Additional Notes (optional)",
            placeholder="Any medical context or special requirements", key="req_notes")

        submitted = st.form_submit_button("🩸 Submit Request", use_container_width=True)

    # ── All validation OUTSIDE the form block ──
    if submitted:
        hospital = other_hospital.strip() if hospital_choice == "Other" else hospital_choice

        errors = []
        if not name.strip():
            errors.append("Patient / Guardian name is required.")
        elif not _is_valid_name(name):
            errors.append("Name must contain letters only — no numbers or special characters.")
        if not address.strip():
            errors.append("Patient address is required.")
        if hospital_choice == "Other" and not hospital:
            errors.append("Please enter the hospital name.")
        if not contact.strip():
            errors.append("Contact number is required.")
        elif not _is_valid_contact(contact):
            errors.append("Contact number must contain only digits (10–15 digits). No letters or special characters.")
        if not email.strip():
            errors.append("Email address is required.")
        elif not _is_valid_email(email):
            errors.append("Please enter a valid email address.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            record = {
                "type": "Request",
                "blood_group": bg,
                "name": name.strip(),
                "address": address.strip(),
                "hospital": hospital,
                "quantity_ml": quantity,
                "urgency": urgency,
                "contact": contact.strip(),
                "email": email.strip(),
                "notes": notes.strip(),
                "submitted_on": str(date.today()),
            }

            st.session_state.requests.append(record)
            st.session_state.patients_saved += 1

            # Save CSV for User Details page
            csv_bytes = _make_csv_bytes(record)
            filename = _safe_filename(name.strip(), contact.strip())
            st.session_state.saved_records.append({
                "filename": filename,
                "csv_bytes": csv_bytes,
                "record": record,
                "submitted_at": str(date.today()),
            })

            st.markdown("""
            <div class="success-banner">
                <h3>✅ Request Submitted Successfully!</h3>
                <p>Our coordination team will contact you within 30 minutes.
                Stay reachable on your provided number.</p>
            </div>
            """, unsafe_allow_html=True)
            st.balloons()

            # Immediate download
            st.download_button(
                label="⬇️ Download Your Request Details (CSV)",
                data=csv_bytes,
                file_name=filename,
                mime="text/csv",
                key="req_download"
            )

            if st.button("Make another request", key="req_another"):
                st.session_state.selected_blood_group_req = None
                st.rerun()
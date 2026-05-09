import streamlit as st
import csv, io
from datetime import date

# ── Email alert utility (replaces Twilio SMS) ─────────────────────────────────
from utils.email_alert import send_blood_alert_email


def _mark_donated(notification: dict):
    """Upgrade a 'pending' notification to 'donated' and rebuild the email preview."""
    notification["status"] = "donated"
    req_name = notification["requestor_name"]
    donor = {
        "name":       notification["donor_name"],
        "blood_group": notification["blood_group"],
        "location":   notification["donor_location"],
        "date":       notification["donor_date"],
        "time_slot":  notification["donor_time"],
        "contact":    notification["donor_contact"],
    }
    notification["email_preview"] = (
        f"Dear {req_name}, "
        f"{donor['name']} has donated {donor['blood_group']} blood "
        f"at {donor['location']} on {donor['date']} at {donor['time_slot']}. "
        f"Please coordinate with your hospital. Donor contact: {donor['contact']}. "
        f"— LifeLine Blood Bank"
    )
    notification["email_sent"] = False   # allow re-send with updated text


# ─────────────────────────────────────────────────────────────────────────────

def render():
    st.markdown("""
    <div class="page-hero">
        <h1>📂 User Details</h1>
        <p>All submitted donation and blood request records — download any entry as CSV.</p>
    </div>
    """, unsafe_allow_html=True)

    records       = st.session_state.get("saved_records", [])
    notifications = st.session_state.get("notifications", [])

    # ── Tab bar ──────────────────────────────────────────────────────────────
    n_unsent = sum(1 for n in notifications if not n.get("email_sent"))
    notif_label = f"📧 Notifications  🔴 {n_unsent}" if n_unsent else "📧 Notifications"
    tab_records, tab_notif = st.tabs(["📋 Records", notif_label])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — Records
    # ══════════════════════════════════════════════════════════════════════════
    with tab_records:
        if not records:
            st.markdown("""
            <div class="instruction-box" style="text-align:center; padding: 48px 24px;">
                <div style="font-size: 3rem; margin-bottom: 12px;">📭</div>
                <h3 style="margin: 0 0 8px 0;">No records yet</h3>
                <p style="color: #9A7070; margin: 0;">
                    Records will appear here once you submit a donation appointment or blood request.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            total     = len(records)
            donations = sum(1 for r in records if r["record"].get("type") == "Donation")
            requests  = sum(1 for r in records if r["record"].get("type") == "Request")

            st.markdown(f"""
            <div class="kpi-grid" style="grid-template-columns: repeat(3, 1fr); margin-bottom: 24px;">
                <div class="kpi-card">
                    <div class="kpi-icon">📋</div>
                    <div class="kpi-value">{total}</div>
                    <div class="kpi-label">Total Records</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-icon">💉</div>
                    <div class="kpi-value">{donations}</div>
                    <div class="kpi-label">Donations</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-icon">🏥</div>
                    <div class="kpi-value">{requests}</div>
                    <div class="kpi-label">Requests</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")

            st.markdown("""
            <style>
                .inbox-row {
                    display: flex; align-items: center; gap: 16px;
                    padding: 14px 18px;
                    border-bottom: 1px solid rgba(255,255,255,0.06);
                    border-radius: 8px; margin-bottom: 4px;
                    background: rgba(255,255,255,0.02);
                    transition: background 0.15s ease;
                }
                .inbox-row:hover { background: rgba(255,107,107,0.07); }
                .inbox-avatar {
                    width: 40px; height: 40px; border-radius: 50%;
                    display: flex; align-items: center; justify-content: center;
                    font-size: 1.1rem; font-weight: 700; flex-shrink: 0;
                    background: linear-gradient(135deg, #FF6B6B, #C0392B); color: white;
                }
                .inbox-avatar.req-avatar { background: linear-gradient(135deg, #E67E22, #C0392B); }
                .inbox-meta { flex: 1; min-width: 0; }
                .inbox-name {
                    font-weight: 600; font-size: 0.95rem; color: #F0E0E0;
                    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
                }
                .inbox-subject {
                    font-size: 0.78rem; color: #9A7070; margin-top: 2px;
                    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
                }
                .inbox-date { font-size: 0.75rem; color: #9A7070; flex-shrink: 0; text-align: right; }
                .inbox-badge { font-size: 0.7rem; padding: 2px 8px; border-radius: 12px; font-weight: 600; flex-shrink: 0; }
                .badge-donation { background: rgba(255,107,107,0.2); color: #FF6B6B; }
                .badge-request  { background: rgba(230,126,34,0.2);  color: #E67E22; }
            </style>
            """, unsafe_allow_html=True)

            for idx, entry in enumerate(reversed(records)):
                rec          = entry["record"]
                rtype        = rec.get("type", "Record")
                name         = rec.get("name", "Unknown")
                contact      = rec.get("contact", "")
                submitted_at = entry.get("submitted_at", "—")
                filename     = entry["filename"]
                csv_bytes    = entry["csv_bytes"]

                if rtype == "Donation":
                    bg        = rec.get("blood_group", "")
                    location  = rec.get("location", "")
                    subject   = f"{bg} donation · {location} · {rec.get('date', '')}"
                    badge_cls = "badge-donation"
                    avatar_cls = ""
                    avatar_letter = "💉"
                else:
                    bg        = rec.get("blood_group", "")
                    hospital  = rec.get("hospital", "")
                    subject   = f"{bg} request · {hospital} · {rec.get('urgency', '')}"
                    badge_cls = "badge-request"
                    avatar_cls = "req-avatar"
                    avatar_letter = "🏥"

                col_row, col_dl = st.columns([10, 1])
                with col_row:
                    st.markdown(f"""
                    <div class="inbox-row">
                        <div class="inbox-avatar {avatar_cls}">{avatar_letter}</div>
                        <div class="inbox-meta">
                            <div class="inbox-name">{name} &nbsp;<span style="color:#9A7070; font-weight:400; font-size:0.8rem">{contact}</span></div>
                            <div class="inbox-subject">{subject}</div>
                            <div style="margin-top:4px;">
                                <span class="inbox-badge {badge_cls}">{rtype}</span>
                            </div>
                        </div>
                        <div class="inbox-date">{submitted_at}<br><span style="font-size:0.7rem; color:#6A5050">{filename}</span></div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_dl:
                    st.download_button(
                        label="⬇️",
                        data=csv_bytes,
                        file_name=filename,
                        mime="text/csv",
                        key=f"dl_{idx}_{filename}",
                        help=f"Download {filename}",
                        use_container_width=True,
                    )

            st.markdown("---")
            st.caption(f"Showing {total} record(s) · stored in session · data resets on page refresh")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — Notifications
    # ══════════════════════════════════════════════════════════════════════════
    with tab_notif:
        st.markdown("""
        <style>
            .notif-card {
                border-radius: 12px;
                padding: 20px 22px;
                margin-bottom: 18px;
                border: 1px solid rgba(255,255,255,0.08);
                background: rgba(255,255,255,0.03);
            }
            .notif-card.pending  { border-left: 4px solid #E67E22; }
            .notif-card.donated  { border-left: 4px solid #27AE60; }
            .notif-card.sent     { border-left: 4px solid #2980B9; }

            .notif-header {
                display: flex; align-items: center; gap: 12px; margin-bottom: 14px;
            }
            .notif-badge {
                font-size: 0.72rem; padding: 3px 10px; border-radius: 12px;
                font-weight: 700; letter-spacing: 0.03em;
            }
            .nb-pending { background: rgba(230,126,34,0.2);  color: #E67E22; }
            .nb-donated { background: rgba(39,174,96,0.2);   color: #27AE60; }
            .nb-sent    { background: rgba(41,128,185,0.2);  color: #2980B9; }

            .notif-title { font-size: 1rem; font-weight: 700; color: #F0E0E0; }
            .notif-sub   { font-size: 0.8rem; color: #9A7070; margin-top: 2px; }

            .match-grid {
                display: grid; grid-template-columns: 1fr 1fr;
                gap: 14px; margin-bottom: 14px;
            }
            .match-box {
                background: rgba(255,255,255,0.04);
                border-radius: 8px; padding: 12px 14px;
            }
            .match-box-title { font-size: 0.72rem; color: #9A7070; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; }
            .match-row { font-size: 0.85rem; color: #D0B0B0; margin-bottom: 3px; }
            .match-row b { color: #F0E0E0; }

            .email-preview {
                background: rgba(0,0,0,0.3); border-radius: 8px;
                padding: 12px 16px; font-size: 0.82rem; color: #C0A0A0;
                font-family: monospace; line-height: 1.5;
                border: 1px dashed rgba(255,255,255,0.1);
                margin-bottom: 12px; word-break: break-word;
            }
        </style>
        """, unsafe_allow_html=True)

        if not notifications:
            st.markdown("""
            <div class="instruction-box" style="text-align:center; padding: 48px 24px;">
                <div style="font-size: 3rem; margin-bottom: 12px;">🔕</div>
                <h3 style="margin: 0 0 8px 0;">No notifications yet</h3>
                <p style="color: #9A7070; margin: 0;">
                    Notifications appear here when a donor's blood group matches a pending request.
                    Try submitting a blood <em>request</em> first, then a matching <em>donation</em>.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Summary strip
            total_n   = len(notifications)
            pending   = sum(1 for n in notifications if n["status"] == "pending")
            donated   = sum(1 for n in notifications if n["status"] == "donated")
            email_sent_count = sum(1 for n in notifications if n.get("email_sent"))

            st.markdown(f"""
            <div class="kpi-grid" style="grid-template-columns: repeat(4, 1fr); margin-bottom: 24px;">
                <div class="kpi-card">
                    <div class="kpi-icon">🔔</div>
                    <div class="kpi-value">{total_n}</div>
                    <div class="kpi-label">Total Matches</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-icon">⏳</div>
                    <div class="kpi-value">{pending}</div>
                    <div class="kpi-label">Pending Donations</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-icon">✅</div>
                    <div class="kpi-value">{donated}</div>
                    <div class="kpi-label">Donations Done</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-icon">📧</div>
                    <div class="kpi-value">{email_sent_count}</div>
                    <div class="kpi-label">Emails Sent</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")

            for i, notif in enumerate(reversed(notifications)):
                real_idx = len(notifications) - 1 - i

                status     = notif["status"]
                email_sent = notif.get("email_sent", False)

                card_cls  = "sent" if email_sent else status
                badge_cls = "nb-sent" if email_sent else f"nb-{status}"
                badge_txt = "📧 Email Sent" if email_sent else ("⏳ Pending" if status == "pending" else "✅ Donated")

                # Show compatibility note
                compat_note = (
                    f"(compatible: donor {notif['blood_group']} → requestor {notif.get('requestor_hospital','—')})"
                    if notif.get("blood_group") else ""
                )

                st.markdown(f"""
                <div class="notif-card {card_cls}">
                    <div class="notif-header">
                        <span class="notif-badge {badge_cls}">{badge_txt}</span>
                        <div>
                            <div class="notif-title">
                                {notif['blood_group']} Donor Match — {notif['requestor_name']} ← {notif['donor_name']}
                            </div>
                            <div class="notif-sub">Created {notif['created_at']}</div>
                        </div>
                    </div>

                    <div class="match-grid">
                        <div class="match-box">
                            <div class="match-box-title">🏥 Requestor</div>
                            <div class="match-row"><b>Name:</b> {notif['requestor_name']}</div>
                            <div class="match-row"><b>Contact:</b> {notif['requestor_contact']}</div>
                            <div class="match-row"><b>Email:</b> {notif.get('requestor_email', '—')}</div>
                            <div class="match-row"><b>Hospital:</b> {notif['requestor_hospital']}</div>
                            <div class="match-row"><b>Urgency:</b> {notif['requestor_urgency']}</div>
                        </div>
                        <div class="match-box">
                            <div class="match-box-title">💉 Donor</div>
                            <div class="match-row"><b>Name:</b> {notif['donor_name']}</div>
                            <div class="match-row"><b>Contact:</b> {notif['donor_contact']}</div>
                            <div class="match-row"><b>Location:</b> {notif['donor_location']}</div>
                            <div class="match-row"><b>Date / Time:</b> {notif['donor_date']} @ {notif['donor_time']}</div>
                        </div>
                    </div>

                    <div style="font-size:0.75rem; color:#9A7070; margin-bottom:6px;">
                        📩 Email preview — to be sent to <b style="color:#D0B0B0">{notif.get('email_to', '—')}</b>
                    </div>
                    <div class="email-preview">{notif.get('email_preview', '—')}</div>
                </div>
                """, unsafe_allow_html=True)

                # Action buttons row
                btn_cols = st.columns([2, 2, 3])

                with btn_cols[0]:
                    btn_label = "📧 Re-send Email" if email_sent else "📧 Send Email to Requestor"
                    if st.button(btn_label, key=f"send_email_{real_idx}", use_container_width=True):
                        r_email = notif.get("email_to", "")
                        if r_email:
                            ok, msg = send_blood_alert_email(
                                requestor_name  = notif["requestor_name"],
                                requestor_email = r_email,
                                blood_group     = notif["blood_group"],
                                hospital        = notif.get("requestor_hospital", "—"),
                                quantity_ml     = 0,
                                urgency         = notif.get("requestor_urgency", "Standard"),
                                donor_name      = notif["donor_name"],
                                donor_phone     = notif.get("donor_contact", "—"),
                                donor_email     = notif.get("donor_email", "—"),
                                donor_location  = notif["donor_location"],
                                donor_date      = notif["donor_date"],
                                donor_time      = notif["donor_time"],
                            )
                            if ok:
                                st.session_state.notifications[real_idx]["email_sent"] = True
                                st.success(f"✅ Email sent to {r_email}")
                                st.rerun()
                            else:
                                st.error(f"Email failed: {msg}")
                        else:
                            st.warning("No email address on file for this requestor.")

                with btn_cols[1]:
                    if status == "pending":
                        if st.button("✅ Mark as Donated", key=f"mark_donated_{real_idx}", use_container_width=True):
                            _mark_donated(st.session_state.notifications[real_idx])
                            st.success("Status updated to Donated. Email preview refreshed.")
                            st.rerun()

                with btn_cols[2]:
                    if email_sent:
                        st.markdown(
                            f"<div style='font-size:0.78rem; color:#2980B9; padding-top:6px;'>"
                            f"📧 Last sent to {notif.get('email_to', '—')}</div>",
                            unsafe_allow_html=True
                        )

                st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 4px 0 18px 0;'>",
                            unsafe_allow_html=True)

            st.caption(
                "💡 Tip: Email alerts are auto-sent when a match is found. "
                "Use the 'Send Email' button above to manually send or re-send an alert."
            )
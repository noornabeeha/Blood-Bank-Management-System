"""
views/blood_tracker.py
-----------------------
GPS map showing where blood donations are stored/scheduled across Bengaluru.
Requestors can filter by their blood group to see compatible locations.
"""

import streamlit as st
import folium
from streamlit_folium import st_folium

# ── GPS coordinates for all donation locations ────────────────────────────────
LOCATION_COORDS = {
    "Indiranagar Community Centre":  (12.9784, 77.6408),
    "Koramangala Blood Camp":        (12.9352, 77.6245),
    "Whitefield Health Hub":         (12.9698, 77.7499),
    "Jayanagar District Hospital":   (12.9250, 77.5938),
    "Rajajinagar Civic Centre":      (12.9887, 77.5546),
    "Malleshwaram Park Grounds":     (13.0035, 77.5710),
    "Yelahanka New Town":            (13.1007, 77.5963),
    "HSR Layout Blood Drive":        (12.9116, 77.6389),
    "BTM Layout Camp":               (12.9166, 77.6101),
    "Hebbal Sports Complex":         (13.0358, 77.5970),
}

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

# Donor compatibility: donor blood group → list of recipient blood groups
DONOR_COMPATIBILITY = {
    "O+":  ["O+", "A+", "B+", "AB+"],
    "O-":  ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"],
    "A+":  ["A+", "AB+"],
    "A-":  ["A+", "A-", "AB+", "AB-"],
    "B+":  ["B+", "AB+"],
    "B-":  ["B+", "B-", "AB+", "AB-"],
    "AB+": ["AB+"],
    "AB-": ["AB+", "AB-"],
}

# Which blood groups can donate TO a given recipient?
def _compatible_donors_for(recipient_bg: str) -> list[str]:
    """Return list of donor blood groups that can donate to recipient_bg."""
    return [donor for donor, recipients in DONOR_COMPATIBILITY.items()
            if recipient_bg in recipients]


def _get_donations_by_location() -> dict:
    """Group scheduled/confirmed donations by location name."""
    by_loc: dict[str, list] = {}
    for entry in st.session_state.get("saved_records", []):
        rec = entry.get("record", {})
        if rec.get("type") == "Donation":
            loc = rec.get("location", "")
            if loc and loc in LOCATION_COORDS:
                by_loc.setdefault(loc, []).append(rec)
    return by_loc


def _popup_html(location: str, donations: list) -> str:
    rows = "".join(
        f"<tr>"
        f"<td style='padding:5px 8px;'>"
        f"  <span style='background:#C0392B;color:#fff;padding:2px 7px;"
        f"  border-radius:10px;font-size:11px;font-weight:700;'>{d.get('blood_group','')}</span>"
        f"</td>"
        f"<td style='padding:5px 8px;color:#eee;font-size:12px;'>{d.get('name','')}</td>"
        f"<td style='padding:5px 8px;color:#bbb;font-size:11px;'>{d.get('date','')}</td>"
        f"<td style='padding:5px 8px;color:#bbb;font-size:11px;'>{d.get('time_slot','')}</td>"
        f"</tr>"
        for d in donations
    )
    return f"""
    <div style="background:#1C0A0A;border-radius:10px;padding:14px;
                min-width:300px;font-family:Arial,sans-serif;">
        <div style="color:#FF6B6B;font-weight:700;font-size:14px;margin-bottom:6px;">
            🩸 {location}
        </div>
        <div style="color:#E0A0A0;font-size:11px;margin-bottom:10px;">
            {len(donations)} donation unit(s) scheduled / stored at this location
        </div>
        <table style="width:100%;border-collapse:collapse;background:rgba(255,255,255,0.04);
                      border-radius:6px;overflow:hidden;">
            <thead>
                <tr style="background:rgba(192,57,43,0.3);">
                    <th style="padding:5px 8px;color:#FF6B6B;font-size:10px;text-align:left;">Type</th>
                    <th style="padding:5px 8px;color:#FF6B6B;font-size:10px;text-align:left;">Donor</th>
                    <th style="padding:5px 8px;color:#FF6B6B;font-size:10px;text-align:left;">Date</th>
                    <th style="padding:5px 8px;color:#FF6B6B;font-size:10px;text-align:left;">Slot</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    """


def _empty_popup_html(location: str) -> str:
    return f"""
    <div style="background:#1C0A0A;border-radius:10px;padding:14px;
                min-width:200px;font-family:Arial,sans-serif;">
        <div style="color:#FF6B6B;font-weight:700;font-size:14px;margin-bottom:6px;">
            📍 {location}
        </div>
        <div style="color:#9A7070;font-size:12px;">
            No donations scheduled at this location yet.
        </div>
    </div>
    """


def render():
    st.markdown("""
    <div class="page-hero" style="background: linear-gradient(135deg, #0A1A0A, #0A3D2E);">
        <h1>🗺️ Blood GPS Tracker</h1>
        <p>Live map of blood donation locations across Bengaluru.
           Filter by your blood group to find compatible supply near you.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Filter controls ───────────────────────────────────────────────────────
    col_f1, col_f2 = st.columns([3, 2])
    with col_f1:
        filter_bg = st.selectbox(
            "🔍 I need blood group (filter compatible locations):",
            ["Show All Locations"] + BLOOD_GROUPS,
            key="tracker_filter_bg",
        )
    with col_f2:
        show_empty = st.checkbox(
            "Show empty locations on map", value=False, key="tracker_show_empty"
        )

    # ── Build data ────────────────────────────────────────────────────────────
    all_by_loc = _get_donations_by_location()

    if filter_bg != "Show All Locations":
        compatible_donors = _compatible_donors_for(filter_bg)
        filtered_by_loc = {
            loc: [d for d in units if d.get("blood_group") in compatible_donors]
            for loc, units in all_by_loc.items()
        }
        filtered_by_loc = {k: v for k, v in filtered_by_loc.items() if v}
    else:
        compatible_donors = BLOOD_GROUPS
        filtered_by_loc = all_by_loc

    total_units    = sum(len(v) for v in all_by_loc.values())
    active_locs    = len(all_by_loc)
    matching_locs  = len(filtered_by_loc)
    matching_units = sum(len(v) for v in filtered_by_loc.values())

    # ── KPI strip ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="kpi-grid" style="grid-template-columns: repeat(4, 1fr); margin: 16px 0 20px 0;">
        <div class="kpi-card">
            <div class="kpi-icon">📍</div>
            <div class="kpi-value">{len(LOCATION_COORDS)}</div>
            <div class="kpi-label">Tracked Locations</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">🏥</div>
            <div class="kpi-value">{active_locs}</div>
            <div class="kpi-label">Active Locations</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">💉</div>
            <div class="kpi-value">{total_units}</div>
            <div class="kpi-label">Total Units Stored</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-icon">🔴</div>
            <div class="kpi-value">{matching_locs}</div>
            <div class="kpi-label">{'Compatible Locations' if filter_bg != 'Show All Locations' else 'Stocked Locations'}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Folium map ────────────────────────────────────────────────────────────
    m = folium.Map(
        location=[12.9716, 77.5946],   # Bengaluru centre
        zoom_start=12,
        tiles="CartoDB dark_matter",
    )

    for loc_name, coords in LOCATION_COORDS.items():
        compatible_here = filtered_by_loc.get(loc_name, [])
        all_here        = all_by_loc.get(loc_name, [])

        if not all_here and not show_empty:
            continue

        if compatible_here:
            # ✅ Has compatible blood for requested type
            blood_types = sorted(set(d.get("blood_group", "") for d in compatible_here))
            marker_color = "red"
            icon_name    = "tint"
            tooltip_txt  = f"🩸 {loc_name} — {len(compatible_here)} compatible unit(s): {', '.join(blood_types)}"
            popup_content = _popup_html(loc_name, compatible_here)

        elif all_here:
            # Has blood but not compatible with filter
            blood_types = sorted(set(d.get("blood_group", "") for d in all_here))
            marker_color = "gray"
            icon_name    = "tint"
            tooltip_txt  = f"⬜ {loc_name} — {len(all_here)} unit(s) (not compatible with {filter_bg})"
            popup_content = _popup_html(loc_name, all_here)

        else:
            # Empty location
            marker_color = "lightblue"
            icon_name    = "map-marker"
            tooltip_txt  = f"📍 {loc_name} — no donations yet"
            popup_content = _empty_popup_html(loc_name)

        folium.Marker(
            location=coords,
            popup=folium.Popup(popup_content, max_width=340),
            tooltip=tooltip_txt,
            icon=folium.Icon(
                color=marker_color,
                icon_color="white",
                icon=icon_name,
                prefix="fa",
            ),
        ).add_to(m)

    # Render map (full width)
    st_folium(m, width="100%", height=500, returned_objects=[])

    # ── Compatibility legend ───────────────────────────────────────────────────
    if filter_bg != "Show All Locations":
        compat_str = ", ".join(compatible_donors)
        st.markdown(f"""
        <div style="margin-top:16px; padding:14px 20px;
                    background:rgba(255,107,107,0.08);
                    border-left:4px solid #FF6B6B; border-radius:8px;">
            <div style="font-size:0.88rem; font-weight:700; color:#FF6B6B; margin-bottom:6px;">
                🔴 Showing locations compatible with blood group <strong>{filter_bg}</strong>
            </div>
            <div style="font-size:0.82rem; color:#C0A0A0; margin-bottom:4px;">
                These donor blood types can donate to <strong>{filter_bg}</strong>:
                <strong>{compat_str}</strong>
            </div>
            <div style="font-size:0.78rem; color:#9A7070;">
                🔴 Red markers = compatible blood available &nbsp;|&nbsp;
                ⬜ Grey markers = other blood types stored &nbsp;|&nbsp;
                🔵 Light blue = no donations yet
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="margin-top:12px; padding:10px 16px;
                    background:rgba(255,255,255,0.03);
                    border-left:4px solid #9A7070; border-radius:8px;
                    font-size:0.8rem; color:#9A7070;">
            🔴 Red = blood stored &nbsp;|&nbsp; 🔵 Light blue = empty location
            &nbsp;|&nbsp; Click any marker to see donor details
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Location detail list ───────────────────────────────────────────────────
    st.markdown('<div class="section-title">📋 Location Directory</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">All tracked donation locations with GPS coordinates and current blood stock</div>',
        unsafe_allow_html=True
    )

    # Use filtered data if a blood group is selected, otherwise all
    display_data = filtered_by_loc if filter_bg != "Show All Locations" else all_by_loc

    if not display_data:
        st.markdown("""
        <div class="instruction-box" style="text-align:center; padding:40px;">
            <div style="font-size:3rem; margin-bottom:12px;">🩸</div>
            <h4 style="margin:0 0 8px 0;">No donations registered yet</h4>
            <p style="color:#9A7070; margin:0;">
                Once donors submit appointments, their locations will appear on
                the map above and in this directory.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for loc_name, donations in display_data.items():
            if not donations:
                continue
            coords      = LOCATION_COORDS.get(loc_name, (0.0, 0.0))
            blood_types = sorted(set(d.get("blood_group", "") for d in donations))
            badges      = " ".join(
                f'<span style="background:#C0392B;color:#fff;padding:3px 9px;'
                f'border-radius:12px;font-size:0.75rem;font-weight:700;'
                f'margin-right:4px;">{bt}</span>'
                for bt in blood_types
            )
            donor_rows = "".join(
                f'<div style="font-size:0.8rem;color:#C0A0A0;margin-top:6px;padding:6px 10px;'
                f'background:rgba(255,255,255,0.03);border-radius:6px;">'
                f'💉 <b style="color:#F0E0E0;">{d.get("name","—")}</b> &nbsp;·&nbsp; '
                f'{d.get("blood_group","")} &nbsp;·&nbsp; {d.get("date","—")} @ {d.get("time_slot","—")}'
                f'</div>'
                for d in donations
            )

            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.03);
                        border:1px solid rgba(255,255,255,0.07);
                        border-left:4px solid #C0392B;
                        border-radius:10px;padding:18px 22px;margin-bottom:14px;">
                <div style="display:flex;justify-content:space-between;
                            align-items:flex-start;gap:16px;flex-wrap:wrap;">
                    <div style="flex:1;min-width:200px;">
                        <div style="font-weight:700;color:#F0E0E0;font-size:1rem;margin-bottom:4px;">
                            📍 {loc_name}
                        </div>
                        <div style="color:#9A7070;font-size:0.75rem;margin-bottom:10px;">
                            🌐 GPS: {coords[0]:.4f}°N, {coords[1]:.4f}°E
                        </div>
                        <div style="margin-bottom:10px;">{badges}</div>
                        {donor_rows}
                    </div>
                    <div style="text-align:right;flex-shrink:0;">
                        <div style="color:#FF6B6B;font-size:2rem;font-weight:700;
                                    line-height:1;">{len(donations)}</div>
                        <div style="color:#9A7070;font-size:0.75rem;">unit(s)</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Show all tracked locations with coordinates even if empty
    with st.expander("📡 View all 10 GPS-tracked locations"):
        for loc_name, coords in LOCATION_COORDS.items():
            count = len(all_by_loc.get(loc_name, []))
            status_icon = "🟢" if count > 0 else "⚪"
            st.markdown(
                f"{status_icon} **{loc_name}** &nbsp; "
                f"`{coords[0]:.4f}°N, {coords[1]:.4f}°E` &nbsp; "
                f"— {count} unit(s)"
            )

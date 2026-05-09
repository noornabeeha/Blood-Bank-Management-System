# 🩸 LifeLine Blood Bank Management System

A Python-based blood bank management platform built with Streamlit that connects blood donors and requestors across Bengaluru. It supports donation scheduling, blood request submissions, GPS-based location tracking of donation camps, a gamified donor rewards programme, and automated email alerting when urgent matches are found.

---

## 📁 Project Structure

```
Blood-Bank-Management-System/
│
├── app.py                    # Main Streamlit app — entry point
├── .env                      # Gmail credentials (not committed)
├── requirements.txt          # Python dependencies
├── LIFE_LINE_PPT.pdf         # Project presentation deck
│
├── styles/
│   └── global.css            # Custom CSS for the entire app (dark theme, KPI cards, sidebar)
│
├── utils/
│   └── email_alert.py        # Gmail SMTP utility — sends HTML alert emails on urgent matches
│
└── views/
    ├── home.py               # Home page — KPI dashboard, feature overview, rewards explainer
    ├── donators.py           # Donor registration & appointment scheduling
    ├── requestors.py         # Blood request submission with urgency level
    ├── blood_tracker.py      # Interactive Folium GPS map of donation locations
    └── user_details.py       # Records management, notification centre, CSV download
```

---

## 📦 Libraries Used

| Library | Purpose |
|---|---|
| `streamlit` | Interactive web dashboard UI and multi-page routing |
| `folium` | Rendering the interactive GPS map of Bengaluru donation locations |
| `streamlit-folium` | Embedding Folium maps inside Streamlit pages |
| `python-dotenv` | Loading Gmail credentials securely from the `.env` file |
| `smtplib` (stdlib) | Sending HTML alert emails via Gmail SMTP |
| `email.mime` (stdlib) | Composing multipart HTML email messages |
| `csv` / `io` (stdlib) | Generating downloadable CSV records for donors and requestors |
| `re` (stdlib) | Input validation (name, email, phone number patterns) |
| `datetime` (stdlib) | Date calculations — e.g. enforcing 56-day donation cooldown |
| `os` (stdlib) | Loading CSS and `.env` file paths relative to the project root |

---

## 🗂️ File Descriptions

### `app.py`
The main entry point. Run with `streamlit run app.py`. Responsibilities:

- Configures the page (`LifeLine Blood Bank`, wide layout, blood-drop icon)
- Initialises all `st.session_state` variables (donations, requests, score, notifications)
- Loads `styles/global.css` for the dark-red theme
- Renders the persistent sidebar with navigation, donor score badge, and notification summary strip
- Routes between pages: `home`, `requestors`, `donators`, `blood_tracker`, `user_details`

### `views/home.py`
The landing page. Displays:

- A live KPI grid (localities covered, patients saved, emergency contacts, user score)
- Feature cards explaining the Requestor and Donator flows
- The three-tier Donor Rewards Programme (New → Silver → Gold) with discount perks
- An About section with network statistics (8,000+ donors, 40+ partner hospitals, 24×7 response)

### `views/donators.py`
Handles the end-to-end donor journey:

- Blood group selection (all 8 groups) with compatibility reference
- Personal detail form with real-time validation (name, email, phone, date of birth)
- Donation location picker (10 Bengaluru localities) and time-slot selector
- Enforces a 56-day cooldown between donations
- Awards 100 points per confirmed donation, updating the sidebar score and tier
- Matches donors against pending blood requests and fires email alerts for urgent/emergency cases
- Exports the donation record as a downloadable CSV

### `views/requestors.py`
Handles blood request submissions:

- Blood group selection with a live availability indicator (High / Medium / Low) per group
- Urgency levels: Routine, Urgent, Emergency
- Hospital picker (10 Bengaluru hospitals) and quantity input (ml)
- Validates all inputs and saves requests to `st.session_state.requests`
- Triggers notification generation when a compatible donor is already on record
- Exports the request record as a downloadable CSV

### `views/blood_tracker.py`
An interactive Folium map centred on Bengaluru:

- Plots GPS markers for all 10 donation locations
- Colour-codes markers: red = has donations, grey = no donations scheduled
- Requestors can filter by blood group to see only compatible donor locations
- Popups show donor name, blood group, scheduled date, and time slot
- Sidebar lists compatible donor blood groups for the selected recipient group

### `views/user_details.py`
A two-tab records and notifications centre:

- **Records tab** — lists all submitted donations and requests with blood group, date, status; each entry has a CSV download button
- **Notifications tab** — shows matched donor–requestor pairs; allows the admin to mark donations as completed and send/resend the HTML alert email to the requestor

### `utils/email_alert.py`
Gmail SMTP utility:

- Reads `GMAIL_SENDER` and `GMAIL_PASSWORD` from `.env` via `python-dotenv`
- Builds a styled HTML email with requestor details, matched donor details, and urgency colour coding (red for Emergency, orange for Urgent)
- `send_blood_alert_email()` is called from both `donators.py` and `user_details.py`

### `styles/global.css`
Full custom CSS for the dark blood-bank theme:

- CSS variables for the colour palette (deep reds, dark backgrounds)
- Styled components: `.kpi-card`, `.feature-card`, `.sidebar-logo`, `.score-sidebar`, `.pill`, `.about-section`
- Responsive layout rules for the Streamlit container and sidebar

---

## ⚙️ Setup & Run Instructions

### Prerequisites

- Python 3.10 or higher
- A Gmail account with a [Google App Password](https://support.google.com/accounts/answer/185833) (required for email alerts)
- `pip` available on your system PATH

### 1. Clone the Repository

```bash
git clone https://github.com/noornabeeha/Blood-Bank-Management-System.git
cd Blood-Bank-Management-System
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

`requirements.txt` includes:

```
streamlit>=1.35.0
python-dotenv>=1.0.0
folium>=0.15.0
streamlit-folium>=0.18.0
```

### 3. Configure the `.env` File

Create a `.env` file in the project root (a template already exists):

```env
GMAIL_SENDER = "your@gmail.com"
GMAIL_PASSWORD = "your_app_password_here"
```

> ⚠️ **Never commit your `.env` file.** It contains sensitive credentials.

| Variable | Description |
|---|---|
| `GMAIL_SENDER` | Gmail address used to send blood alert emails |
| `GMAIL_PASSWORD` | Gmail App Password (16-character, not your regular password) |

### 4. Run the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

---

## 🚀 How to Use the App

1. **Launch** the app with `streamlit run app.py`
2. **Home page** — view live KPI stats and learn about the Requestor and Donator flows
3. **Requestors page** — select a blood group, fill in hospital and urgency details, and submit a request; download your record as CSV
4. **Donators page** — pick your blood group, enter personal details and a preferred location and time slot, then confirm your appointment; earn points and unlock donor tiers
5. **Blood GPS Tracker** — select a blood group to see a live Folium map of compatible donation locations across Bengaluru
6. **User Details** — review all records, manage notifications, mark donations as completed, and send email alerts to matched requestors

> 💡 **Tip:** Email alerts are only sent for **Urgent** or **Emergency** requests. Routine requests are logged but do not trigger notifications.

---

## 🗺️ Donation Locations Covered

| Location | Area |
|---|---|
| Indiranagar Community Centre | East Bengaluru |
| Koramangala Blood Camp | South-East |
| Whitefield Health Hub | East |
| Jayanagar District Hospital | South |
| Rajajinagar Civic Centre | West |
| Malleshwaram Park Grounds | North-West |
| Yelahanka New Town | North |
| HSR Layout Blood Drive | South-East |
| BTM Layout Camp | South |
| Hebbal Sports Complex | North |

---

## 🎮 Donor Rewards Programme

| Tier | Points Required | Benefit |
|---|---|---|
| 🩸 New Donor | 0 – 149 pts | 5% off medical supplies |
| 🥈 Silver Donor | 150 – 299 pts | 12% off diagnostics & labs |
| 🥇 Gold Donor | 300+ pts | 20% off + priority care |

Each confirmed donation awards **100 points**. Points accumulate across sessions via `st.session_state`.

---

## 👥 Team Members

| Name | GitHub |
|---|---|
| Noor Nabeeha | [@noornabeeha](https://github.com/noornabeeha) |
| Riteesha Banavannavar | [@rit2006](https://github.com/rit2006) |
| Priya Hira | [@priyahirag](https://github.com/priyahirag) |
| Prakruth D | [@prak123d](https://github.com/prak123d) |

Repository: [https://github.com/noornabeeha/Blood-Bank-Management-System](https://github.com/noornabeeha/Blood-Bank-Management-System)

---

## 🤖 AI Tools Declaration

The following AI tools were used during the development of this project:

| Tool | Usage |
|---|---|
| Claude (Anthropic) | Generating Streamlit layout boilerplate (sidebar routing, session state initialisation, column structures) · Suggesting Folium marker and popup configurations for the GPS tracker · Drafting the HTML email template structure for blood alert notifications · Reviewing and improving input validation logic (email, phone, name regex patterns) · Assisting with CSS variable structure and dark-theme component styling |

This declaration is made in the interest of academic integrity and transparency. All AI-assisted content was reviewed, verified, and adapted by the team.

---

*Last updated: May 2026*

from __future__ import annotations

import json
import os
from datetime import datetime
from urllib import error, request

import streamlit as st

st.set_page_config(page_title="Dialed Training", page_icon="🏋️", layout="wide")

THEME = {
    "bg": "#0A0D14",
    "surface": "#121826",
    "surface_alt": "#1A2233",
    "surface_elevated": "#202B3D",
    "sidebar": "#0E1420",
    "primary": "#7F56FF",
    "primary_soft": "rgba(127, 86, 255, 0.18)",
    "success": "#16A34A",
    "text": "#F3F4F6",
    "text_muted": "#98A6BF",
    "border": "#263247",
}

WORKOUT_TEMPLATES = [
    {
        "tier": "Foundation",
        "title": "Full Body Primer",
        "category": "Full",
        "exercises": [
            "Goblet Squat 3x10",
            "DB Bench Press 3x10",
            "Lat Pulldown 3x10",
            "RDL 3x8",
            "Farmer Carry 3x40m",
        ],
    },
    {
        "tier": "Foundation",
        "title": "Upper Build Base",
        "category": "Upper",
        "exercises": [
            "Incline DB Press 4x8",
            "Chest-Supported Row 4x10",
            "DB Shoulder Press 3x10",
            "Cable Face Pull 3x15",
            "Plank 3x45s",
        ],
    },
    {
        "tier": "Build",
        "title": "Push Strength",
        "category": "Push",
        "exercises": [
            "Barbell Bench 5x5",
            "Overhead Press 4x6",
            "Weighted Dips 3x8",
            "Lateral Raise 3x15",
            "Triceps Pressdown 3x12",
        ],
    },
    {
        "tier": "Build",
        "title": "Pull Power",
        "category": "Pull",
        "exercises": [
            "Deadlift 5x3",
            "Weighted Pull-up 5x5",
            "Barbell Row 4x8",
            "Rear Delt Fly 3x15",
            "EZ Curl 3x12",
        ],
    },
    {
        "tier": "Peak",
        "title": "Performance Peak",
        "category": "Athletic",
        "exercises": [
            "Power Clean 6x2",
            "Front Squat 4x4",
            "Bench Press 4x4",
            "Sled Sprint 8x20m",
            "Core Circuit 3 rounds",
        ],
    },
]

RECOVERY_PROTOCOLS = [
    "10-minute easy bike + nasal breathing",
    "Soft tissue calves/quads/glutes 8 minutes",
    "Hip mobility flow 6 minutes",
    "Thoracic opener 3 minutes",
    "Walk 20-30 minutes",
]

PT_PROTOCOLS = {
    "Patellar tendon": ["Spanish squat hold 5x45s", "Step-down 3x10", "Slow split squat 3x8"],
    "Shoulder irritation": ["Band external rotation 3x15", "Scap push-up 3x12", "Landmine press 3x8"],
    "Shin splints": ["Tib raises 3x20", "Calf eccentric 3x12", "Foot intrinsic drill 5 min"],
    "Low back strain": ["McGill curl-up 3x8", "Bird-dog 3x8", "Side plank 3x30s"],
}

MILITARY_ROUTES = {
    "Ranger School": ["Ruck progression", "Pull-up density", "Land-nav endurance"],
    "Sapper": ["Grip/carry work", "Hill intervals", "Heavy step-up endurance"],
    "Airborne": ["Landing prep mobility", "Sprint repeats", "Core stiffness"],
    "Selection": ["Long-zone cardio", "Sandbag strength", "Sleep discipline"],
}


st.markdown(
    f"""
<style>
.stApp {{
  background:
    radial-gradient(1200px 550px at 0% -20%, rgba(127,86,255,0.22), transparent 60%),
    radial-gradient(900px 450px at 100% 0%, rgba(22,163,74,0.16), transparent 52%),
    {THEME['bg']};
}}
[data-testid="stSidebar"] {{
  background: {THEME['sidebar']};
  border-right: 1px solid rgba(255,255,255,0.06);
}}
.block-container {{
  padding-top: 1.3rem;
  padding-bottom: 2rem;
}}
.dial-shell {{
  border: 1px solid {THEME['border']};
  border-radius: 18px;
  background: linear-gradient(130deg, {THEME['surface']}, {THEME['surface_alt']});
  padding: 18px 20px;
  box-shadow: 0 16px 36px rgba(0,0,0,0.32);
}}
.dial-kicker {{
  font-size: 12px;
  color: #9CB4FF;
  text-transform: uppercase;
  font-weight: 700;
  letter-spacing: .08em;
  margin-bottom: 4px;
}}
.dial-muted {{
  color: {THEME['text_muted']};
}}
</style>
""",
    unsafe_allow_html=True,
)


def get_setting(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name)  # type: ignore[union-attr]
        if value is not None:
            return str(value)
    except Exception:
        pass
    return str(os.getenv(name, default))


def init_state() -> None:
    if "foundation_profile" not in st.session_state:
        st.session_state["foundation_profile"] = {
            "goal": "General Fitness",
            "trainingDays": 3,
            "equipment": "Full Gym",
            "experience": "Brand New",
        }
    if "workout_history" not in st.session_state:
        st.session_state["workout_history"] = []
    if "coach_history" not in st.session_state:
        st.session_state["coach_history"] = []
    if "active_workout" not in st.session_state:
        st.session_state["active_workout"] = None


def is_authenticated() -> bool:
    username = get_setting("APP_USERNAME", "").strip()
    password = get_setting("APP_PASSWORD", "").strip()
    auth_enabled = bool(username and password)

    if not auth_enabled:
        return True
    if st.session_state.get("authenticated"):
        return True

    st.markdown('<div class="dial-shell">', unsafe_allow_html=True)
    st.markdown('<p class="dial-kicker">Protected App</p>', unsafe_allow_html=True)
    st.title("Dialed Sign In")
    with st.form("login_form", clear_on_submit=False):
        user_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")
        if submitted:
            if user_input == username and password_input == password:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Invalid credentials.")
    st.markdown("</div>", unsafe_allow_html=True)
    return False


def backend_coach_reply(prompt: str, mode: str) -> tuple[dict | None, str | None]:
    backend_url = get_setting("BACKEND_URL", "").strip().rstrip("/")
    if not backend_url:
        return None, "No BACKEND_URL configured."

    payload = {
        "athleteId": "streamlit-user",
        "mode": mode,
        "prompt": prompt,
        "contextSummary": "Streamlit deployment",
        "recentWorkouts": st.session_state.get("workout_history", []),
        "conversationHistory": st.session_state.get("coach_history", [])[-12:],
    }

    req = request.Request(
        f"{backend_url}/api/coach/respond",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=15) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw), None
    except error.HTTPError as exc:
        return None, f"Backend HTTP error: {exc.code}"
    except error.URLError as exc:
        return None, f"Backend unavailable: {exc.reason}"
    except Exception as exc:
        return None, f"Backend error: {exc}"


def local_coach_reply(prompt: str, mode: str) -> dict:
    lower = prompt.lower()
    if "deadlift" in lower:
        summary = "Keep bar over mid-foot, brace hard before pulling, and keep lats tight to lock in neutral spine."
    elif "recover" in lower or "sore" in lower:
        summary = "Run a low-intensity recovery day, focus on sleep, then return to volume once soreness drops."
    elif "knee" in lower or "pain" in lower:
        summary = "Use pain-free ROM, lower load, and progress slowly with controlled tempo work for 7-10 days."
    else:
        summary = "Prioritize execution quality, progress load gradually, and keep recovery standards consistent."

    return {
        "mode": mode,
        "summary": summary,
        "nextActions": [
            "Log the next workout with RPE.",
            "Track sleep and soreness for 3 days.",
            "Adjust weekly volume by readiness.",
        ],
        "source": "local-fallback",
    }


def save_workout_result(workout_title: str, tier: str, notes: str) -> None:
    record = {
        "id": datetime.utcnow().strftime("%Y%m%d%H%M%S%f"),
        "date": datetime.utcnow().isoformat(),
        "title": workout_title,
        "tier": tier,
        "notes": notes,
    }
    st.session_state["workout_history"] = [record] + st.session_state["workout_history"]


def workout_catalog(selected_tier: str) -> list[dict]:
    pool = [w for w in WORKOUT_TEMPLATES if selected_tier == "All" or w["tier"] == selected_tier]
    profile = st.session_state.get("foundation_profile", {})
    goal = str(profile.get("goal", ""))
    if goal == "Strength":
        pool = sorted(pool, key=lambda x: 0 if x["category"] in {"Push", "Pull", "Athletic"} else 1)
    elif goal == "Fat Loss":
        pool = sorted(pool, key=lambda x: 0 if x["category"] in {"Full", "Athletic"} else 1)
    return pool


def render_welcome() -> None:
    st.markdown('<div class="dial-shell">', unsafe_allow_html=True)
    st.markdown('<p class="dial-kicker">Mission Control</p>', unsafe_allow_html=True)
    st.subheader("Welcome")
    profile = st.session_state["foundation_profile"]
    st.caption(
        f"Goal: {profile['goal']} | {profile['trainingDays']} days/week | {profile['equipment']} | {profile['experience']}"
    )
    col1, col2, col3 = st.columns(3)
    col1.metric("Workouts Logged", len(st.session_state["workout_history"]))
    col2.metric("Coach Messages", len(st.session_state["coach_history"]))
    col3.metric("Program Tier", "Foundation")
    st.markdown("</div>", unsafe_allow_html=True)


def render_foundation_setup() -> None:
    st.markdown('<div class="dial-shell">', unsafe_allow_html=True)
    st.markdown('<p class="dial-kicker">Foundation Setup</p>', unsafe_allow_html=True)
    profile = st.session_state["foundation_profile"]
    with st.form("foundation_form"):
        goal = st.selectbox("Goal", ["General Fitness", "Strength", "Muscle", "Fat Loss"], index=["General Fitness", "Strength", "Muscle", "Fat Loss"].index(profile["goal"]))
        training_days = st.slider("Training days / week", min_value=2, max_value=6, value=int(profile["trainingDays"]))
        equipment = st.selectbox("Equipment", ["Bodyweight", "Basic Gym", "Full Gym"], index=["Bodyweight", "Basic Gym", "Full Gym"].index(profile["equipment"]) if profile["equipment"] in ["Bodyweight", "Basic Gym", "Full Gym"] else 2)
        experience = st.selectbox("Experience", ["Brand New", "Some Experience", "Advanced"], index=["Brand New", "Some Experience", "Advanced"].index(profile["experience"]) if profile["experience"] in ["Brand New", "Some Experience", "Advanced"] else 0)
        saved = st.form_submit_button("Save Profile")
        if saved:
            st.session_state["foundation_profile"] = {
                "goal": goal,
                "trainingDays": training_days,
                "equipment": equipment,
                "experience": experience,
            }
            st.success("Foundation profile saved.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_workout() -> None:
    st.markdown('<div class="dial-shell">', unsafe_allow_html=True)
    st.markdown('<p class="dial-kicker">Programmed Workouts</p>', unsafe_allow_html=True)
    tier = st.selectbox("Tier", ["All", "Foundation", "Build", "Peak"], index=1)
    templates = workout_catalog(tier)

    if not templates:
        st.info("No workouts found for this filter.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    for template in templates:
        with st.expander(f"{template['title']}  |  {template['tier']}  |  {template['category']}"):
            for ex in template["exercises"]:
                st.write(f"- {ex}")
            start = st.button(f"Start {template['title']}", key=f"start_{template['title']}")
            if start:
                st.session_state["active_workout"] = template
                st.success(f"Active workout: {template['title']}")

    active = st.session_state.get("active_workout")
    if active:
        st.divider()
        st.write(f"Active Workout: **{active['title']}**")
        notes = st.text_area("Session notes", key="session_notes")
        complete = st.button("Complete Workout")
        if complete:
            save_workout_result(active["title"], active["tier"], notes)
            st.session_state["active_workout"] = None
            st.success("Workout logged to Results.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_results() -> None:
    st.markdown('<div class="dial-shell">', unsafe_allow_html=True)
    st.markdown('<p class="dial-kicker">Results</p>', unsafe_allow_html=True)
    history = st.session_state["workout_history"]
    if not history:
        st.info("No workouts logged yet.")
    else:
        for record in history[:25]:
            with st.expander(f"{record['title']} | {record['tier']} | {record['date'][:10]}"):
                st.write(record.get("notes") or "No notes")
    st.markdown("</div>", unsafe_allow_html=True)


def render_recovery() -> None:
    st.markdown('<div class="dial-shell">', unsafe_allow_html=True)
    st.markdown('<p class="dial-kicker">Recovery</p>', unsafe_allow_html=True)
    readiness = st.slider("How recovered do you feel?", 1, 10, 6)
    st.write("Today protocol:")
    for step in RECOVERY_PROTOCOLS:
        st.write(f"- {step}")
    if readiness <= 4:
        st.warning("Keep intensity low today. Recovery focus is recommended.")
    elif readiness >= 8:
        st.success("Green light for a harder session.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_pt() -> None:
    st.markdown('<div class="dial-shell">', unsafe_allow_html=True)
    st.markdown('<p class="dial-kicker">PT Support</p>', unsafe_allow_html=True)
    condition = st.selectbox("Condition", list(PT_PROTOCOLS.keys()))
    st.write("Plan:")
    for step in PT_PROTOCOLS[condition]:
        st.write(f"- {step}")
    st.caption("This is supportive training guidance, not medical diagnosis.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_military_prep() -> None:
    st.markdown('<div class="dial-shell">', unsafe_allow_html=True)
    st.markdown('<p class="dial-kicker">Military Prep</p>', unsafe_allow_html=True)
    school = st.selectbox("Target School", list(MILITARY_ROUTES.keys()))
    week = st.slider("Current week", 1, 16, 1)
    st.write(f"Week {week} priorities:")
    for step in MILITARY_ROUTES[school]:
        st.write(f"- {step}")
    st.markdown("</div>", unsafe_allow_html=True)


def render_coach() -> None:
    st.markdown('<div class="dial-shell">', unsafe_allow_html=True)
    st.markdown('<p class="dial-kicker">Coach</p>', unsafe_allow_html=True)
    prompt = st.text_area("Ask coach", "How do I set up my deadlift?")
    mode = st.selectbox("Mode", ["Foundation", "Build", "Peak", "Recovery", "PT", "Military"])

    if st.button("Generate coach response"):
        backend_reply, backend_error = backend_coach_reply(prompt, mode)
        if backend_reply:
            backend_reply["source"] = "backend"
            st.session_state["coach_history"].append({"role": "user", "content": prompt})
            st.session_state["coach_history"].append(
                {"role": "assistant", "content": json.dumps(backend_reply)}
            )
            st.json(backend_reply)
        else:
            if backend_error:
                st.warning(f"{backend_error} Falling back to local coach logic.")
            reply = local_coach_reply(prompt, mode)
            st.session_state["coach_history"].append({"role": "user", "content": prompt})
            st.session_state["coach_history"].append(
                {"role": "assistant", "content": json.dumps(reply)}
            )
            st.json(reply)

    if st.session_state["coach_history"]:
        st.divider()
        st.caption("Recent coach conversation")
        for item in st.session_state["coach_history"][-8:]:
            who = "You" if item["role"] == "user" else "Coach"
            st.write(f"**{who}:** {item['content']}")
    st.markdown("</div>", unsafe_allow_html=True)


def render_admin() -> None:
    st.markdown('<div class="dial-shell">', unsafe_allow_html=True)
    st.markdown('<p class="dial-kicker">Admin</p>', unsafe_allow_html=True)
    allow_registration = st.toggle("Allow registration", value=True)
    announcement = st.text_input("Announcement", "Welcome to Dialed")
    st.code(
        json.dumps(
            {
                "allowRegistration": allow_registration,
                "announcement": announcement,
            },
            indent=2,
        ),
        language="json",
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_team_admin() -> None:
    st.markdown('<div class="dial-shell">', unsafe_allow_html=True)
    st.markdown('<p class="dial-kicker">Team Admin</p>', unsafe_allow_html=True)
    team_name = st.text_input("Team name", "Dialed Tactical")
    athlete_email = st.text_input("Add athlete by email")
    if st.button("Add Athlete") and athlete_email:
        st.success(f"Added {athlete_email} to {team_name} (mock flow).")
    st.markdown("</div>", unsafe_allow_html=True)


def render_account() -> None:
    st.markdown('<div class="dial-shell">', unsafe_allow_html=True)
    st.markdown('<p class="dial-kicker">Account</p>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    col1.text_input("Name", "Dialed Athlete")
    col2.text_input("Email", "athlete@dialed.app")
    st.selectbox("Plan", ["Foundation", "Performance", "Team"], index=1)
    st.button("Save Account")
    st.markdown("</div>", unsafe_allow_html=True)


def render_placeholder(screen: str) -> None:
    st.markdown('<div class="dial-shell">', unsafe_allow_html=True)
    st.markdown(f'<p class="dial-kicker">{screen}</p>', unsafe_allow_html=True)
    st.info("This screen is scaffolded with production styling and ready for deeper parity wiring.")
    st.markdown("</div>", unsafe_allow_html=True)


init_state()
if not is_authenticated():
    st.stop()

if st.session_state.get("authenticated"):
    with st.sidebar:
        if st.button("Log out"):
            st.session_state["authenticated"] = False
            st.rerun()

screens = [
    "Welcome",
    "Foundation Setup",
    "Workout",
    "Results",
    "Recovery",
    "PT",
    "Military Prep",
    "Coach",
    "Admin",
    "Team Admin",
    "Account",
]

selected = st.sidebar.radio("Screen", screens, key="screen")
st.subheader(selected)

if selected == "Welcome":
    render_welcome()
elif selected == "Foundation Setup":
    render_foundation_setup()
elif selected == "Workout":
    render_workout()
elif selected == "Results":
    render_results()
elif selected == "Recovery":
    render_recovery()
elif selected == "PT":
    render_pt()
elif selected == "Military Prep":
    render_military_prep()
elif selected == "Coach":
    render_coach()
elif selected == "Admin":
    render_admin()
elif selected == "Team Admin":
    render_team_admin()
elif selected == "Account":
    render_account()
else:
    render_placeholder(selected)

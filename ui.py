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
    "sidebar": "#0E1420",
    "border": "#263247",
    "text_muted": "#98A6BF",
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
  padding-top: 1.25rem;
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
[data-testid="stTextInputRootElement"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {{
  background: #111827 !important;
  color: #E5E7EB !important;
  border: 1px solid #334155 !important;
  border-radius: 10px !important;
}}
[data-testid="stTextInputRootElement"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {{
  color: #94A3B8 !important;
}}
[data-baseweb="select"] > div {{
  background: #111827 !important;
  color: #E5E7EB !important;
  border: 1px solid #334155 !important;
  border-radius: 10px !important;
}}
[data-baseweb="select"] svg {{
  fill: #9CB4FF !important;
}}
.stButton > button,
.stFormSubmitButton > button {{
  background: linear-gradient(160deg, #151E30, #121826) !important;
  color: #E5E7EB !important;
  border: 1px solid #334155 !important;
  border-radius: 10px !important;
}}
.stButton > button:hover,
.stFormSubmitButton > button:hover {{
  border-color: #9CB4FF !important;
  color: #FFFFFF !important;
}}
.stButton > button:disabled,
.stFormSubmitButton > button:disabled {{
  background: #111827 !important;
  color: #64748B !important;
  border-color: #1F2937 !important;
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
    if "admin_settings" not in st.session_state:
        st.session_state["admin_settings"] = {
            "allowRegistration": True,
            "announcementEnabled": False,
            "announcementMessage": "Welcome to Dialed.",
            "maintenanceMode": False,
            "maintenanceMessage": "",
        }
    if "members" not in st.session_state:
        st.session_state["members"] = []
    if "backend_auth" not in st.session_state:
        st.session_state["backend_auth"] = {"token": "", "member": None}


def app_gate_authenticated() -> bool:
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
    with st.form("app_login_form"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")
        if submitted:
            if u == username and p == password:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Invalid credentials")
    st.markdown("</div>", unsafe_allow_html=True)
    return False


def backend_request(
    path: str,
    method: str = "GET",
    payload: dict | None = None,
    auth_token: str | None = None,
) -> tuple[dict | list | None, str | None]:
    backend_url = get_setting("BACKEND_URL", "").strip().rstrip("/")
    if not backend_url:
        return None, "No BACKEND_URL configured."

    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = request.Request(f"{backend_url}{path}", data=body, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=15) as response:
            raw = response.read().decode("utf-8")
            if not raw:
                return {}, None
            return json.loads(raw), None
    except error.HTTPError as exc:
        try:
            raw = exc.read().decode("utf-8")
            parsed = json.loads(raw) if raw else {}
            return None, str(parsed.get("message") or parsed.get("detail") or f"HTTP {exc.code}")
        except Exception:
            return None, f"HTTP {exc.code}"
    except error.URLError as exc:
        return None, f"Network error: {exc.reason}"
    except Exception as exc:
        return None, str(exc)


def backend_coach_reply(prompt: str, mode: str) -> tuple[dict | None, str | None]:
    payload = {
        "athleteId": "streamlit-user",
        "mode": mode,
        "prompt": prompt,
        "contextSummary": "Streamlit deployment",
        "recentWorkouts": st.session_state.get("workout_history", []),
        "conversationHistory": st.session_state.get("coach_history", [])[-12:],
    }
    response, err = backend_request("/api/coach/respond", method="POST", payload=payload)
    if err:
        return None, err
    return response if isinstance(response, dict) else None, None


def local_coach_reply(prompt: str, mode: str) -> dict:
    text = prompt.lower()
    if "deadlift" in text:
        summary = "Keep bar over mid-foot, brace hard before pulling, and keep lats tight."
    elif "recover" in text or "sore" in text:
        summary = "Use a low-intensity recovery day and return to hard training when readiness improves."
    elif "knee" in text or "pain" in text:
        summary = "Use pain-free ROM, reduce load, and progress slowly for 7-10 days."
    else:
        summary = "Prioritize movement quality, controlled progression, and recovery standards."

    return {
        "mode": mode,
        "summary": summary,
        "nextActions": [
            "Log next session with RPE.",
            "Track sleep and soreness for 3 days.",
            "Adjust weekly volume by readiness.",
        ],
        "source": "local-fallback",
    }


def display_member_name(member: dict) -> str:
    email = str(member.get("email") or "").strip()
    name = str(member.get("name") or "").strip()
    return f"{name} ({email})" if name else email


def member_plan(member: dict) -> str:
    subscription = member.get("subscription")
    if isinstance(subscription, dict):
        return str(subscription.get("plan") or "Performance")
    return str(member.get("plan") or "Performance")


def member_status(member: dict) -> str:
    subscription = member.get("subscription")
    if isinstance(subscription, dict):
        return str(subscription.get("status") or "active")
    return str(member.get("status") or "active")


def backend_token() -> str:
    auth = st.session_state.get("backend_auth", {})
    return str(auth.get("token") or "")


def backend_member() -> dict:
    auth = st.session_state.get("backend_auth", {})
    member = auth.get("member")
    return member if isinstance(member, dict) else {}


def is_backend_admin() -> bool:
    return bool(backend_token() and backend_member().get("role") == "admin")


def render_backend_session() -> None:
    backend_url = get_setting("BACKEND_URL", "").strip()
    with st.sidebar:
        st.markdown("---")
        st.caption("Backend Session")

        if not backend_url:
            st.caption("Set BACKEND_URL in Secrets for live backend mode.")
            return

        auth = st.session_state["backend_auth"]
        token = auth.get("token", "")
        member = auth.get("member")

        if token and member:
            st.success(f"{member.get('email', '')} ({member.get('role', 'member')})")
            if st.button("Sign out backend", key="backend_signout"):
                st.session_state["backend_auth"] = {"token": "", "member": None}
                st.rerun()
            return

        with st.form("backend_signin"):
            email = st.text_input("Backend email")
            password = st.text_input("Backend password", type="password")
            submitted = st.form_submit_button("Sign in backend")
            if submitted:
                response, err = backend_request(
                    "/api/auth/login",
                    method="POST",
                    payload={"email": email.strip().lower(), "password": password},
                )
                if err:
                    st.error(err)
                elif isinstance(response, dict):
                    session = response.get("session") or {}
                    member_payload = response.get("member")
                    token_value = str(session.get("token") or "")
                    if token_value and member_payload:
                        st.session_state["backend_auth"] = {
                            "token": token_value,
                            "member": member_payload,
                        }
                        st.rerun()
                    else:
                        st.error("Unexpected login response")


def workout_catalog(selected_tier: str) -> list[dict]:
    pool = [w for w in WORKOUT_TEMPLATES if selected_tier == "All" or w["tier"] == selected_tier]
    goal = str(st.session_state["foundation_profile"].get("goal", ""))
    if goal == "Strength":
        pool = sorted(pool, key=lambda x: 0 if x["category"] in {"Push", "Pull", "Athletic"} else 1)
    elif goal == "Fat Loss":
        pool = sorted(pool, key=lambda x: 0 if x["category"] in {"Full", "Athletic"} else 1)
    return pool


def save_workout_result(workout: dict, notes: str) -> None:
    record = {
        "id": datetime.utcnow().strftime("%Y%m%d%H%M%S%f"),
        "date": datetime.utcnow().isoformat(),
        "title": workout["title"],
        "tier": workout["tier"],
        "category": workout.get("category", "General"),
        "exercises": workout.get("exercises", []),
        "completedCount": len(workout.get("exercises", [])),
        "notes": notes,
    }
    st.session_state["workout_history"] = [record] + st.session_state["workout_history"]


def performance_grade(total_logged: int, completed_count: int) -> str:
    if total_logged == 0 or completed_count == 0:
        return "Reset"
    if completed_count >= total_logged:
        return "Locked In"
    if completed_count / total_logged >= 0.65:
        return "Productive"
    return "Partial"


def infer_pattern(exercise: str) -> str:
    text = exercise.lower()
    if "squat" in text:
        return "Squat"
    if "deadlift" in text or "rdl" in text:
        return "Hinge"
    if any(x in text for x in ["press", "bench", "dip"]):
        return "Push"
    if any(x in text for x in ["row", "pull", "pulldown"]):
        return "Pull"
    if any(x in text for x in ["sled", "carry", "sprint", "bike", "erg"]):
        return "Conditioning"
    return "Accessory"


def render_welcome() -> None:
    backend_url = get_setting("BACKEND_URL", "").strip()
    if backend_url:
        settings_payload, settings_error = backend_request("/api/app/settings")
        if settings_error:
            st.caption(f"Live settings unavailable: {settings_error}")
        elif isinstance(settings_payload, dict):
            app_settings = settings_payload.get("settings") or {}
            if app_settings.get("announcementEnabled") and app_settings.get("announcementMessage"):
                st.info(str(app_settings.get("announcementMessage")))
            if app_settings.get("maintenanceMode"):
                st.warning(str(app_settings.get("maintenanceMessage") or "Maintenance mode is enabled."))

    st.markdown('<div class="dial-shell">', unsafe_allow_html=True)
    st.markdown('<p class="dial-kicker">Mission Control</p>', unsafe_allow_html=True)
    st.subheader("Welcome")
    p = st.session_state["foundation_profile"]
    st.caption(f"Goal: {p['goal']} | {p['trainingDays']} days/week | {p['equipment']} | {p['experience']}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Workouts Logged", len(st.session_state["workout_history"]))
    c2.metric("Coach Messages", len(st.session_state["coach_history"]))
    c3.metric("Program Tier", "Foundation")
    st.markdown("</div>", unsafe_allow_html=True)


def render_foundation_setup() -> None:
    st.markdown('<div class="dial-shell">', unsafe_allow_html=True)
    st.markdown('<p class="dial-kicker">Foundation Setup</p>', unsafe_allow_html=True)
    profile = st.session_state["foundation_profile"]
    with st.form("foundation_form"):
        goal = st.selectbox("Goal", ["General Fitness", "Strength", "Muscle", "Fat Loss"], index=["General Fitness", "Strength", "Muscle", "Fat Loss"].index(profile["goal"]))
        days = st.slider("Training days / week", 2, 6, int(profile["trainingDays"]))
        equipment = st.selectbox("Equipment", ["Bodyweight", "Basic Gym", "Full Gym"], index=["Bodyweight", "Basic Gym", "Full Gym"].index(profile["equipment"]) if profile["equipment"] in ["Bodyweight", "Basic Gym", "Full Gym"] else 2)
        exp = st.selectbox("Experience", ["Brand New", "Some Experience", "Advanced"], index=["Brand New", "Some Experience", "Advanced"].index(profile["experience"]) if profile["experience"] in ["Brand New", "Some Experience", "Advanced"] else 0)
        if st.form_submit_button("Save Profile"):
            st.session_state["foundation_profile"] = {
                "goal": goal,
                "trainingDays": days,
                "equipment": equipment,
                "experience": exp,
            }
            st.success("Profile saved.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_workout() -> None:
    st.markdown('<div class="dial-shell">', unsafe_allow_html=True)
    st.markdown('<p class="dial-kicker">Programmed Workouts</p>', unsafe_allow_html=True)
    preview_count = 6
    tier = st.selectbox("Tier", ["All", "Foundation", "Build", "Peak"], index=1)
    search = st.text_input("Search workouts, categories, or exercises...")
    query = search.strip().lower()

    templates = workout_catalog(tier)
    filtered = []
    for template in templates:
        matched = (
            not query
            or query in template["title"].lower()
            or query in template["category"].lower()
            or query in template["tier"].lower()
            or any(query in ex.lower() for ex in template["exercises"])
        )
        if matched:
            filtered.append(template)

    show_all = st.toggle(f"Show all workouts ({len(filtered)})", value=bool(query), key="show_all_workouts")
    visible = filtered if query or show_all else filtered[:preview_count]

    if not filtered:
        st.info("No workouts found for this filter.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if not query and not show_all and len(filtered) > len(visible):
        st.caption(f"Showing top {preview_count}. Search or open the full list for more options.")

    for template in visible:
        with st.expander(f"{template['title']} | {template['tier']} | {template['category']}"):
            for ex in template["exercises"]:
                st.write(f"- {ex}")
            if st.button(f"Start {template['title']}", key=f"start_{template['title']}"):
                st.session_state["active_workout"] = template
                st.success(f"Active workout: {template['title']}")

    active = st.session_state.get("active_workout")
    if active:
        st.divider()
        st.write(f"Active workout: **{active['title']}**")
        notes = st.text_area("Session notes", key="session_notes")
        if st.button("Complete Workout", key="complete_workout"):
            save_workout_result(active, notes)
            st.session_state["active_workout"] = None
            st.success("Workout logged to Results.")

    st.markdown("</div>", unsafe_allow_html=True)


def render_results() -> None:
    st.markdown('<div class="dial-shell">', unsafe_allow_html=True)
    st.markdown('<p class="dial-kicker">Results</p>', unsafe_allow_html=True)
    history = st.session_state["workout_history"]

    if not history:
        st.info("No workouts logged yet.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    selected = history[0]
    total_logged = len(selected.get("exercises", []))
    completed_count = int(selected.get("completedCount", total_logged))
    grade = performance_grade(total_logged, completed_count)
    top_exercise = selected.get("exercises", ["-"])[0] if selected.get("exercises") else "-"

    movement_split: dict[str, int] = {}
    for ex in selected.get("exercises", []):
        pattern = infer_pattern(ex)
        movement_split[pattern] = movement_split.get(pattern, 0) + 1

    trend_values = [len(item.get("exercises", [])) for item in history[:6]]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Performance", grade)
    m2.metric("Exercises", str(total_logged))
    m3.metric("Top Movement", top_exercise.split(" ")[0] if top_exercise != "-" else "-")
    m4.metric("Recent Sessions", str(len(history)))

    c1, c2 = st.columns(2)
    c1.write("Movement split")
    c1.code(json.dumps(movement_split or {"None": 0}, indent=2), language="json")
    c2.write("Recent trend (exercise count)")
    c2.line_chart(list(reversed(trend_values)))

    st.divider()
    for record in history[:25]:
        with st.expander(f"{record['title']} | {record['tier']} | {record['date'][:10]}"):
            exercises = record.get("exercises", [])
            if exercises:
                st.write("Exercises")
                for ex in exercises:
                    st.write(f"- {ex}")
            st.write(record.get("notes") or "No notes")

    st.markdown("</div>", unsafe_allow_html=True)


def render_recovery() -> None:
    st.markdown('<div class="dial-shell">', unsafe_allow_html=True)
    st.markdown('<p class="dial-kicker">Recovery</p>', unsafe_allow_html=True)
    readiness = st.slider("How recovered do you feel?", 1, 10, 6)
    for step in RECOVERY_PROTOCOLS:
        st.write(f"- {step}")
    if readiness <= 4:
        st.warning("Keep intensity low today.")
    elif readiness >= 8:
        st.success("Green light for a harder session.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_pt() -> None:
    st.markdown('<div class="dial-shell">', unsafe_allow_html=True)
    st.markdown('<p class="dial-kicker">PT Support</p>', unsafe_allow_html=True)
    condition = st.selectbox("Condition", list(PT_PROTOCOLS.keys()))
    for step in PT_PROTOCOLS[condition]:
        st.write(f"- {step}")
    st.caption("Supportive training guidance, not diagnosis.")
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

    if st.button("Generate coach response", key="coach_generate"):
        backend_reply, backend_error = backend_coach_reply(prompt, mode)
        if backend_reply:
            backend_reply["source"] = "backend"
            reply = backend_reply
        else:
            if backend_error:
                st.warning(f"{backend_error} Falling back to local coach logic.")
            reply = local_coach_reply(prompt, mode)

        st.session_state["coach_history"].append({"role": "user", "content": prompt})
        st.session_state["coach_history"].append({"role": "assistant", "content": json.dumps(reply)})
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

    token = backend_token()
    member = backend_member()
    backend_configured = bool(get_setting("BACKEND_URL", "").strip())
    backend_admin = bool(backend_configured and token and member.get("role") == "admin")

    if backend_configured and token and member.get("role") != "admin":
        st.warning("Backend connected, but this account is not admin.")

    if not backend_configured:
        st.info("Running local mode. Set BACKEND_URL and sign in as admin for live backend control.")

    if backend_admin:
        settings_response, settings_error = backend_request("/api/admin/settings", auth_token=token)
        members_response, members_error = backend_request("/api/admin/members", auth_token=token)
        if settings_error:
            st.error(f"Settings fetch failed: {settings_error}")
        if members_error:
            st.error(f"Members fetch failed: {members_error}")

        settings = settings_response.get("settings") if isinstance(settings_response, dict) else st.session_state["admin_settings"]
        members = members_response.get("members") if isinstance(members_response, dict) else st.session_state["members"]
        if isinstance(members, list):
            st.session_state["members"] = members
        if isinstance(settings, dict):
            st.session_state["admin_settings"] = settings
    else:
        settings = st.session_state["admin_settings"]
        members = st.session_state["members"]

    if not isinstance(members, list):
        members = []

    st.subheader("App Controls")
    c1, c2 = st.columns(2)
    with c1:
        settings["allowRegistration"] = st.toggle("Allow registration", value=bool(settings.get("allowRegistration", True)), key="adm_allow")
        settings["announcementEnabled"] = st.toggle("Announcement enabled", value=bool(settings.get("announcementEnabled", False)), key="adm_ann")
        settings["maintenanceMode"] = st.toggle("Maintenance mode", value=bool(settings.get("maintenanceMode", False)), key="adm_maint")
    with c2:
        settings["announcementMessage"] = st.text_input("Announcement message", value=str(settings.get("announcementMessage", "")), key="adm_ann_msg")
        settings["maintenanceMessage"] = st.text_input("Maintenance message", value=str(settings.get("maintenanceMessage", "")), key="adm_maint_msg")

    if st.button("Save Admin Settings", key="adm_save"):
        if backend_admin:
            _, save_error = backend_request("/api/admin/settings", method="PATCH", payload=settings, auth_token=token)
            if save_error:
                st.error(f"Could not save settings: {save_error}")
            else:
                st.success("Backend settings saved.")
                st.rerun()
        else:
            st.session_state["admin_settings"] = settings
            st.success("Local settings saved.")

    st.divider()
    st.subheader("Member Access")
    m1, m2 = st.columns(2)
    with m1:
        new_email = st.text_input("Member email", key="adm_new_email")
        new_name = st.text_input("Member name", key="adm_new_name")
    with m2:
        new_role = st.selectbox("Role", ["member", "admin"], key="adm_new_role")
        new_plan = st.selectbox("Plan", ["Foundation", "Performance", "Team"], index=1, key="adm_new_plan")

    if st.button("Add Member", key="adm_add_member") and new_email.strip():
        email_value = new_email.strip().lower()
        if backend_admin:
            register_response, add_error = backend_request(
                "/api/auth/register",
                method="POST",
                payload={
                    "name": new_name.strip() or "New Member",
                    "email": email_value,
                    "password": "TempPass123!",
                    "plan": new_plan,
                    "programType": "individual",
                },
            )
            if add_error:
                st.error(f"Backend add member failed: {add_error}")
            else:
                verification_link = None
                if isinstance(register_response, dict):
                    verification_link = register_response.get("verificationLink")

                if new_role == "admin":
                    _, grant_error = backend_request(
                        "/api/admin/admins/grant",
                        method="POST",
                        payload={"email": email_value},
                        auth_token=token,
                    )
                    if grant_error:
                        st.warning(f"Member created but admin grant failed: {grant_error}")
                    else:
                        st.success(f"Added {email_value} and granted admin.")
                else:
                    st.success(f"Added {email_value} in backend.")

                if verification_link:
                    st.caption(f"Verification link: {verification_link}")
                st.caption("Temporary password: TempPass123!")
                st.rerun()
        else:
            members.append(
                {
                    "id": datetime.utcnow().strftime("local-%Y%m%d%H%M%S"),
                    "name": new_name.strip() or "New Member",
                    "email": email_value,
                    "role": new_role,
                    "plan": new_plan,
                    "status": "active",
                }
            )
            st.session_state["members"] = members
            st.success(f"Added {email_value} in local mode.")

    if members:
        member_options = [display_member_name(m) for m in members]
        selected_label = st.selectbox("Select member", member_options, key="adm_sel_member")
        selected_member = members[member_options.index(selected_label)]
        selected_email = str(selected_member.get("email") or "")
        sel_role = st.selectbox(
            "Update role",
            ["member", "admin"],
            index=0 if selected_member.get("role", "member") == "member" else 1,
            key="adm_upd_role",
        )
        sel_status = st.selectbox(
            "Update status",
            ["trial", "active", "paused", "canceled", "past_due", "locked"],
            index=["trial", "active", "paused", "canceled", "past_due", "locked"].index(member_status(selected_member))
            if member_status(selected_member) in {"trial", "active", "paused", "canceled", "past_due", "locked"}
            else 1,
            key="adm_upd_status",
        )
        sel_plan = st.selectbox(
            "Update plan",
            ["Foundation", "Performance", "Team"],
            index=["Foundation", "Performance", "Team"].index(member_plan(selected_member))
            if member_plan(selected_member) in {"Foundation", "Performance", "Team"}
            else 1,
            key="adm_upd_plan",
        )
        if st.button("Update Member", key="adm_update"):
            if backend_admin and selected_member.get("id"):
                _, upd_error = backend_request(
                    f"/api/admin/members/{selected_member['id']}",
                    method="PATCH",
                    payload={
                        "role": sel_role,
                        "status": sel_status,
                        "plan": sel_plan,
                    },
                    auth_token=token,
                )
                if upd_error:
                    st.error(f"Backend update failed: {upd_error}")
                else:
                    st.success(f"Updated {selected_email} in backend.")
                    st.rerun()
            else:
                selected_member["role"] = sel_role
                selected_member["status"] = sel_status
                selected_member["plan"] = sel_plan
                st.session_state["members"] = members
                st.success(f"Updated {selected_email} in local mode.")

        if backend_admin and selected_member.get("id"):
            a1, a2, a3 = st.columns(3)
            if a1.button("Reset Password Link", key="adm_reset_password"):
                reset_response, reset_error = backend_request(
                    f"/api/admin/members/{selected_member['id']}/reset-password",
                    method="POST",
                    auth_token=token,
                )
                if reset_error:
                    st.error(f"Reset password failed: {reset_error}")
                else:
                    st.success("Password reset generated.")
                    if isinstance(reset_response, dict) and reset_response.get("resetLink"):
                        st.caption(f"Reset link: {reset_response['resetLink']}")
            if a2.button("Resend Verification", key="adm_resend_verify"):
                verify_response, verify_error = backend_request(
                    f"/api/admin/members/{selected_member['id']}/resend-verification",
                    method="POST",
                    auth_token=token,
                )
                if verify_error:
                    st.error(f"Verification resend failed: {verify_error}")
                else:
                    st.success("Verification flow triggered.")
                    if isinstance(verify_response, dict) and verify_response.get("verificationLink"):
                        st.caption(f"Verification link: {verify_response['verificationLink']}")
            if a3.button("Force Logout Member", key="adm_force_logout"):
                _, logout_error = backend_request(
                    f"/api/admin/members/{selected_member['id']}/force-logout",
                    method="POST",
                    auth_token=token,
                )
                if logout_error:
                    st.error(f"Force logout failed: {logout_error}")
                else:
                    st.success("Member sessions revoked.")

    st.divider()
    st.subheader("Current Members")
    role_filter = st.selectbox("Filter by role", ["all", "member", "admin"], key="adm_filter_role")
    status_filter = st.selectbox(
        "Filter by status",
        ["all", "trial", "active", "paused", "canceled", "past_due", "locked"],
        key="adm_filter_status",
    )

    filtered = []
    for m in members:
        role_ok = role_filter == "all" or m.get("role") == role_filter
        status_value = member_status(m)
        status_ok = status_filter == "all" or status_value == status_filter
        if role_ok and status_ok:
            filtered.append(m)

    if filtered:
        st.dataframe(
            [
                {
                    "name": m.get("name", ""),
                    "email": m.get("email", ""),
                    "role": m.get("role", "member"),
                    "plan": member_plan(m),
                    "status": member_status(m),
                    "emailVerified": bool(m.get("emailVerified", False)),
                    "programType": m.get("programType", "individual"),
                }
                for m in filtered
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No members match filters.")

    st.markdown("</div>", unsafe_allow_html=True)


def render_team_admin() -> None:
    st.markdown('<div class="dial-shell">', unsafe_allow_html=True)
    st.markdown('<p class="dial-kicker">Team Admin</p>', unsafe_allow_html=True)

    token = backend_token()
    member = backend_member()
    backend_configured = bool(get_setting("BACKEND_URL", "").strip())

    if not backend_configured:
        st.info("Local mode only. Configure BACKEND_URL for live teams.")
        team_name = st.text_input("Team name", "Dialed Tactical", key="team_name_local")
        athlete_email = st.text_input("Add athlete by email", key="team_add_email_local")
        if st.button("Add Athlete", key="team_add_local") and athlete_email:
            st.success(f"Added {athlete_email} to {team_name}.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if not token:
        st.warning("Sign in to backend from the sidebar to manage teams.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    teams_payload, teams_error = backend_request("/api/team/me", auth_token=token)
    if teams_error:
        st.error(f"Could not load teams: {teams_error}")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    teams = teams_payload.get("teams") if isinstance(teams_payload, dict) else []
    if not isinstance(teams, list):
        teams = []

    can_create_team = member.get("role") == "admin"
    if can_create_team:
        st.subheader("Create Team")
        c1, c2 = st.columns(2)
        with c1:
            team_name = st.text_input("Team name", key="team_create_name")
        with c2:
            org_name = st.text_input("Organization", key="team_create_org")
        if st.button("Create Team", key="team_create_btn") and team_name.strip():
            create_response, create_error = backend_request(
                "/api/admin/teams",
                method="POST",
                payload={"name": team_name.strip(), "organization": org_name.strip()},
                auth_token=token,
            )
            if create_error:
                st.error(f"Could not create team: {create_error}")
            else:
                created = create_response.get("team", {}) if isinstance(create_response, dict) else {}
                st.success(f"Created team: {created.get('name', team_name.strip())}")
                st.rerun()

    if not teams:
        st.info("No teams found for this account yet.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    team_labels = [f"{t.get('name', 'Team')} ({t.get('id', '')[:8]})" for t in teams]
    selected_label = st.selectbox("Select team", team_labels, key="team_select")
    team = teams[team_labels.index(selected_label)]
    team_id = str(team.get("id") or "")
    st.caption(f"Role: {team.get('myRole', 'athlete')}")

    dashboard_payload, dashboard_error = backend_request(f"/api/team/{team_id}/dashboard", auth_token=token)
    roster_payload, roster_error = backend_request(f"/api/team/{team_id}/roster", auth_token=token)
    templates_payload, templates_error = backend_request(f"/api/team/{team_id}/templates", auth_token=token)
    assignments_payload, assignments_error = backend_request(f"/api/team/{team_id}/assignments", auth_token=token)

    if dashboard_error:
        st.error(f"Dashboard error: {dashboard_error}")
    if roster_error:
        st.error(f"Roster error: {roster_error}")
    if templates_error:
        st.error(f"Templates error: {templates_error}")
    if assignments_error:
        st.error(f"Assignments error: {assignments_error}")

    dashboard = dashboard_payload.get("dashboard") if isinstance(dashboard_payload, dict) else {}
    roster = roster_payload.get("members") if isinstance(roster_payload, dict) else []
    templates = templates_payload.get("templates") if isinstance(templates_payload, dict) else []
    assignments = assignments_payload.get("assignments") if isinstance(assignments_payload, dict) else []

    if not isinstance(roster, list):
        roster = []
    if not isinstance(templates, list):
        templates = []
    if not isinstance(assignments, list):
        assignments = []

    d1, d2, d3 = st.columns(3)
    d1.metric("Roster", str(len(roster)))
    d2.metric("Templates", str(len(templates)))
    d3.metric("Assignments", str(len(assignments)))

    st.subheader("Add Team Member")
    a1, a2 = st.columns(2)
    with a1:
        add_email = st.text_input("Member email", key="team_add_email_live")
    with a2:
        add_role = st.selectbox("Team role", ["athlete", "coach", "team_admin"], key="team_add_role_live")
    if st.button("Add to Team", key="team_add_live") and add_email.strip():
        _, add_error = backend_request(
            f"/api/team/{team_id}/members",
            method="POST",
            payload={"email": add_email.strip().lower(), "role": add_role},
            auth_token=token,
        )
        if add_error:
            st.error(f"Could not add member: {add_error}")
        else:
            st.success(f"Added {add_email.strip().lower()} to team.")
            st.rerun()

    st.divider()
    st.subheader("Team Roster")
    if roster:
        st.dataframe(
            [
                {
                    "name": m.get("name", ""),
                    "email": m.get("email", ""),
                    "teamRole": m.get("teamRole", ""),
                    "globalRole": m.get("globalRole", ""),
                    "plan": m.get("subscription", {}).get("plan", ""),
                    "status": m.get("subscription", {}).get("status", ""),
                }
                for m in roster
            ],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("No members in this team yet.")

    if templates:
        st.subheader("Templates")
        st.dataframe(
            [
                {
                    "title": t.get("title", ""),
                    "tier": t.get("tier", ""),
                    "category": t.get("category", ""),
                    "exerciseCount": len(t.get("exercises", []) if isinstance(t.get("exercises"), list) else []),
                }
                for t in templates
            ],
            hide_index=True,
            use_container_width=True,
        )

    if assignments:
        st.subheader("Assignments")
        st.dataframe(
            [
                {
                    "template": a.get("templateTitle", ""),
                    "member": a.get("memberName", ""),
                    "status": a.get("status", ""),
                    "assignedAt": a.get("assignedAt", ""),
                }
                for a in assignments
            ],
            hide_index=True,
            use_container_width=True,
        )

    if isinstance(dashboard, dict) and dashboard:
        st.subheader("Team Dashboard")
        st.json(dashboard)

    st.markdown("</div>", unsafe_allow_html=True)


def render_account() -> None:
    st.markdown('<div class="dial-shell">', unsafe_allow_html=True)
    st.markdown('<p class="dial-kicker">Account</p>', unsafe_allow_html=True)

    token = backend_token()
    member = backend_member()

    if token and member:
        st.success("Connected to backend account")
        st.write(f"Name: {member.get('name', '-')}")
        st.write(f"Email: {member.get('email', '-')}")
        st.write(f"Role: {member.get('role', 'member')}")
        sub = member.get("subscription", {})
        if isinstance(sub, dict):
            st.write(f"Plan: {sub.get('plan', '-')}")
            st.write(f"Status: {sub.get('status', '-')}")

        if st.button("Refresh Account", key="acct_refresh"):
            me_response, me_error = backend_request("/api/auth/me", auth_token=token)
            if me_error:
                st.error(f"Refresh failed: {me_error}")
            elif isinstance(me_response, dict) and isinstance(me_response.get("member"), dict):
                st.session_state["backend_auth"] = {"token": token, "member": me_response["member"]}
                st.rerun()

        st.divider()
        st.subheader("Profile")
        p1, p2, p3 = st.columns(3)
        with p1:
            age = st.number_input("Age", min_value=0, max_value=100, value=int(member.get("age") or 0), step=1)
        with p2:
            height = st.number_input(
                "Height (in)",
                min_value=0,
                max_value=96,
                value=int(member.get("heightInches") or 0),
                step=1,
            )
        with p3:
            weight = st.number_input(
                "Weight (lb)",
                min_value=0,
                max_value=700,
                value=int(member.get("weightLbs") or 0),
                step=1,
            )
        activity = st.selectbox(
            "Activity level",
            ["", "low", "moderate", "high"],
            index=["", "low", "moderate", "high"].index(str(member.get("activityLevel") or ""))
            if str(member.get("activityLevel") or "") in {"", "low", "moderate", "high"}
            else 0,
        )
        program_type = st.selectbox(
            "Program type",
            ["individual", "team"],
            index=1 if member.get("programType") == "team" else 0,
        )
        team_name = st.text_input("Team name", value=str(member.get("teamName") or ""))
        if st.button("Save Profile", key="acct_save_profile"):
            payload = {
                "age": int(age) if age else None,
                "heightInches": int(height) if height else None,
                "weightLbs": int(weight) if weight else None,
                "activityLevel": activity or None,
                "programType": program_type,
                "teamName": team_name.strip() or None,
            }
            profile_response, profile_error = backend_request(
                "/api/auth/profile",
                method="PATCH",
                payload=payload,
                auth_token=token,
            )
            if profile_error:
                st.error(f"Profile update failed: {profile_error}")
            elif isinstance(profile_response, dict) and isinstance(profile_response.get("member"), dict):
                st.session_state["backend_auth"] = {"token": token, "member": profile_response["member"]}
                st.success("Profile updated.")
                st.rerun()

        st.divider()
        st.subheader("Subscription")
        current_plan = str(sub.get("plan") or "Performance") if isinstance(sub, dict) else "Performance"
        current_status = str(sub.get("status") or "active") if isinstance(sub, dict) else "active"
        upd_plan = st.selectbox(
            "Plan",
            ["Foundation", "Performance", "Team"],
            index=["Foundation", "Performance", "Team"].index(current_plan)
            if current_plan in {"Foundation", "Performance", "Team"}
            else 1,
        )
        upd_status = st.selectbox(
            "Status",
            ["trial", "active", "paused", "canceled", "past_due"],
            index=["trial", "active", "paused", "canceled", "past_due"].index(current_status)
            if current_status in {"trial", "active", "paused", "canceled", "past_due"}
            else 1,
        )
        if st.button("Save Subscription", key="acct_save_subscription"):
            sub_response, sub_error = backend_request(
                "/api/auth/subscription",
                method="PATCH",
                payload={"plan": upd_plan, "status": upd_status},
                auth_token=token,
            )
            if sub_error:
                st.error(f"Subscription update failed: {sub_error}")
            elif isinstance(sub_response, dict) and isinstance(sub_response.get("member"), dict):
                st.session_state["backend_auth"] = {"token": token, "member": sub_response["member"]}
                st.success("Subscription updated.")
                st.rerun()

        st.divider()
        st.subheader("Password")
        with st.form("acct_password_form"):
            current_password = st.text_input("Current password", type="password")
            next_password = st.text_input("New password", type="password")
            if st.form_submit_button("Change Password"):
                _, pwd_error = backend_request(
                    "/api/auth/password/change",
                    method="POST",
                    payload={"currentPassword": current_password, "nextPassword": next_password},
                    auth_token=token,
                )
                if pwd_error:
                    st.error(f"Password change failed: {pwd_error}")
                else:
                    st.success("Password updated.")
    else:
        st.info("Sign in to backend from the sidebar to load account data.")

    st.markdown("</div>", unsafe_allow_html=True)


def render_placeholder(screen: str) -> None:
    st.markdown('<div class="dial-shell">', unsafe_allow_html=True)
    st.markdown(f'<p class="dial-kicker">{screen}</p>', unsafe_allow_html=True)
    st.info("This screen is running in the Python build and ready for deeper parity wiring.")
    st.markdown("</div>", unsafe_allow_html=True)


init_state()
if not app_gate_authenticated():
    st.stop()

if st.session_state.get("authenticated"):
    with st.sidebar:
        if st.button("Log out app", key="app_signout"):
            st.session_state["authenticated"] = False
            st.rerun()

render_backend_session()

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

from __future__ import annotations

import json
import os
from urllib import error, request

import streamlit as st

st.set_page_config(page_title="Dialed Python UI", page_icon="🏋️", layout="wide")

st.markdown(
    """
<style>
.stApp {
  background: radial-gradient(1200px 500px at 20% -10%, rgba(0, 153, 255, 0.22), transparent),
              radial-gradient(900px 500px at 100% 0%, rgba(255, 72, 0, 0.16), transparent),
              #0A0E16;
}
[data-testid="stSidebar"] {
  background: rgba(18, 22, 34, 0.95);
}
.dial-shell {
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 20px;
  padding: 20px 24px;
  background: linear-gradient(130deg, rgba(17, 24, 39, 0.94), rgba(10, 14, 22, 0.96));
  box-shadow: 0 20px 40px rgba(0,0,0,0.35);
}
.dial-kicker {
  font-size: 12px;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: #8FB2FF;
  font-weight: 700;
}
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


def local_coach_reply(prompt: str, mode: str) -> dict:
    lower = prompt.lower()
    if "deadlift" in lower:
        summary = "Keep bar over mid-foot, brace before pulling, and maintain neutral spine."
    elif "recover" in lower or "sore" in lower:
        summary = "Use a low-intensity recovery day and re-test readiness tomorrow."
    elif "knee" in lower or "pain" in lower:
        summary = "Reduce painful patterns, keep pain-free ranges, and progress only after symptoms settle."
    else:
        summary = "Focus on progressive overload, movement quality, and recovery consistency."

    return {
        "mode": mode,
        "summary": summary,
        "nextActions": [
            "Log your session.",
            "Track soreness and sleep.",
            "Adjust next session by readiness.",
        ],
        "source": "local-fallback",
    }


def backend_coach_reply(prompt: str, mode: str) -> tuple[dict | None, str | None]:
    backend_url = get_setting("BACKEND_URL", "").strip().rstrip("/")
    if not backend_url:
        return None, "No BACKEND_URL configured."

    payload = {
        "athleteId": "streamlit-user",
        "mode": mode,
        "prompt": prompt,
        "contextSummary": "Streamlit deployment",
        "recentWorkouts": [],
        "conversationHistory": [],
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"{backend_url}/api/coach/respond",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=12) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw), None
    except error.HTTPError as exc:
        return None, f"Backend HTTP error: {exc.code}"
    except error.URLError as exc:
        return None, f"Backend unavailable: {exc.reason}"
    except Exception as exc:  # pragma: no cover
        return None, f"Backend error: {exc}"


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


if not is_authenticated():
    st.stop()

if st.session_state.get("authenticated"):
    with st.sidebar:
        if st.button("Log out"):
            st.session_state["authenticated"] = False
            st.rerun()

st.markdown('<div class="dial-shell">', unsafe_allow_html=True)
st.markdown('<p class="dial-kicker">Dial Training</p>', unsafe_allow_html=True)
st.title("Dialed Training")
st.caption("Python-native companion UI replacing the original TypeScript app shell.")
st.markdown("</div>", unsafe_allow_html=True)

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

selected = st.sidebar.radio("Screen", screens)

st.subheader(selected)

if selected == "Welcome":
    st.write("This is the Python production shell with deploy-safe settings.")
    backend_url = get_setting("BACKEND_URL", "").strip()
    st.code(
        json.dumps(
            {
                "backendConfigured": bool(backend_url),
                "backendUrl": backend_url or "not-set",
                "authEnabled": bool(
                    get_setting("APP_USERNAME", "").strip()
                    and get_setting("APP_PASSWORD", "").strip()
                ),
            },
            indent=2,
        ),
        language="json",
    )

if selected == "Coach":
    prompt = st.text_area("Ask coach", "How do I set up my deadlift?")
    mode = st.selectbox("Mode", ["Foundation", "Build", "Peak", "Recovery", "PT", "Military"])
    if st.button("Generate coach response"):
        backend_reply, backend_error = backend_coach_reply(prompt, mode)
        if backend_reply:
            backend_reply["source"] = "backend"
            st.json(backend_reply)
        else:
            if backend_error:
                st.warning(f"{backend_error} Falling back to local coach logic.")
            st.json(local_coach_reply(prompt, mode))

if selected in {"Workout", "Results", "Recovery", "PT", "Military Prep", "Admin", "Team Admin", "Account", "Foundation Setup"}:
    st.info("Production UI shell loaded. Connect this screen to backend routes as needed.")
    st.code(
        json.dumps(
            {
                "screen": selected,
                "status": "ready_for_integration",
                "api_base": get_setting("BACKEND_URL", "http://localhost:4000"),
            },
            indent=2,
        ),
        language="json",
    )

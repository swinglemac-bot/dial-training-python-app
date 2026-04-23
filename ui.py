from __future__ import annotations

import json

import streamlit as st

st.set_page_config(page_title="Dialed Python UI", page_icon="🏋️", layout="wide")

st.title("Dialed Training (Python Copy)")
st.caption("Python-native companion UI replacing the original TypeScript app shell.")

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
    st.write("This is the Python version of your app shell.")

if selected == "Coach":
    prompt = st.text_area("Ask coach", "How do I set up my deadlift?")
    mode = st.selectbox("Mode", ["Foundation", "Build", "Peak", "Recovery", "PT", "Military"])
    if st.button("Generate coach response"):
        lower = prompt.lower()
        if "deadlift" in lower:
            summary = "Keep bar over mid-foot, brace before pulling, and maintain neutral spine."
        elif "recover" in lower or "sore" in lower:
            summary = "Use a low-intensity recovery day and re-test readiness tomorrow."
        else:
            summary = "Focus on progressive overload, movement quality, and recovery consistency."

        st.json(
            {
                "mode": mode,
                "summary": summary,
                "nextActions": [
                    "Log your session.",
                    "Track soreness and sleep.",
                    "Adjust next session by readiness.",
                ],
            }
        )

if selected in {"Workout", "Results", "Recovery", "PT", "Military Prep", "Admin", "Team Admin", "Account", "Foundation Setup"}:
    st.info("Python UI scaffold created. Wire this to `app.main` API routes for live data.")
    st.code(
        json.dumps(
            {
                "screen": selected,
                "status": "ready_for_integration",
                "api_base": "http://localhost:4000",
            },
            indent=2,
        ),
        language="json",
    )

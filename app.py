# app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="MSD Risk Survey Demo", layout="wide")

# --------------------
# Utilities & Defaults
# --------------------
DEFAULT_THRESHOLDS = {
    "high": 70,
    "med_high": 50,
    "med": 35,
}

# columns order
COLUMNS = [
    "timestamp",
    "tool",              # NZMAC / NZRAPP / NZART
    "task_name",
    # Common fields
    "duration_min",
    "frequency_per_hr",
    "posture",
    # Lifting (NZMAC-like)
    "load_kg",
    "lift_height",       # floor / knee / waist / shoulder
    # Pushing/Pulling (NZRAPP-like)
    "push_pull_force_kg",
    "distance_m",
    "surface",           # smooth / rough
    # Repetitive (NZART-like)
    "reps_per_min",
    "cycle_time_sec",
    "neck_shoulder_awk", # none / mild / severe
    # Score & Tier
    "risk_score",
    "risk_tier",
]

POSTURES = ["neutral", "bending", "twisting", "reaching"]
LIFT_HEIGHTS = ["floor", "knee", "waist", "shoulder"]
SURFACES = ["smooth", "rough"]
NECK_SHOULDER = ["none", "mild", "severe"]

def init_state():
    if "df" not in st.session_state:
        # seed with tiny demo dataset
        demo = [
            [datetime.now().strftime("%Y-%m-%d %H:%M"), "NZMAC", "Lift cartons", 10, 30, "bending", 12, "knee", None, None, None, None, None, "mild", 58, "Med-High"],
            [datetime.now().strftime("%Y-%m-%d %H:%M"), "NZRAPP", "Push trolley", 8, 20, "neutral", None, None, 18, 25, "smooth", None, None, "none", 42, "Medium"],
            [datetime.now().strftime("%Y-%m-%d %H:%M"), "NZART", "Soldering", 15, 40, "reaching", None, None, None, None, None, 28, 12, "severe", 76, "High"],
        ]
        st.session_state.df = pd.DataFrame(demo, columns=COLUMNS)
    if "thresholds" not in st.session_state:
        st.session_state.thresholds = DEFAULT_THRESHOLDS.copy()

init_state()

# --------------------
# Risk Model (simple pragmatic rules)
# --------------------
def tier_from_score(score: float, thres: dict) -> str:
    if score >= thres["high"]:
        return "High"
    if score >= thres["med_high"]:
        return "Med-High"
    if score >= thres["med"]:
        return "Medium"
    return "Low"

def score_nzmac(load_kg, frequency_per_hr, posture, lift_height):
    """Very simplified surrogate of lifting assessment (0-100)."""
    # base by load
    load_points = np.interp(load_kg, [0, 5, 10, 20, 35], [5, 15, 30, 55, 75])
    # frequency multiplier
    freq_mult = np.interp(frequency_per_hr, [0, 10, 30, 60], [1.0, 1.1, 1.25, 1.4])
    # posture penalty
    posture_pen = {"neutral": 1.0, "bending": 1.15, "twisting": 1.2, "reaching": 1.1}.get(posture, 1.0)
    # height penalty
    height_pen = {"floor": 1.25, "knee": 1.15, "waist": 1.0, "shoulder": 1.2}.get(lift_height, 1.0)
    score = load_points * freq_mult * posture_pen * height_pen
    return float(np.clip(score, 5, 100))

def score_nzrapp(push_pull_force_kg, distance_m, surface, frequency_per_hr):
    """Simplified pushing/pulling scoring (0-100)."""
    force_points = np.interp(push_pull_force_kg, [0, 5, 10, 20, 35], [5, 15, 28, 48, 70])
    dist_mult = np.interp(distance_m, [0, 10, 30, 60], [1.0, 1.05, 1.15, 1.25])
    surface_pen = {"smooth": 1.0, "rough": 1.15}.get(surface, 1.0)
    freq_mult = np.interp(frequency_per_hr, [0, 10, 30, 60], [1.0, 1.1, 1.2, 1.3])
    score = force_points * dist_mult * surface_pen * freq_mult
    return float(np.clip(score, 5, 100))

def score_nzart(reps_per_min, cycle_time_sec, neck_shoulder_awk, posture):
    """Simplified repetitive upper limb scoring (0-100)."""
    rep_points = np.interp(reps_per_min, [0, 10, 20, 40, 60], [5, 15, 30, 55, 75])
    cycle_adj = np.interp(cycle_time_sec, [5, 20, 60], [1.25, 1.1, 1.0])  # shorter cycle → higher load
    neck_pen = {"none": 1.0, "mild": 1.15, "severe": 1.35}.get(neck_shoulder_awk, 1.0)
    posture_pen = {"neutral": 1.0, "bending": 1.1, "twisting": 1.15, "reaching": 1.2}.get(posture, 1.0)
    score = rep_points * cycle_adj * neck_pen * posture_pen
    return float(np.clip(score, 5, 100))

def recommendations(tier: str, tool: str):
    base = [
        "Rotate tasks to reduce exposure time.",
        "Provide micro-breaks and encourage neutral postures.",
        "Train staff on safe techniques and early symptom reporting.",
    ]
    if tier in ["Med-High", "High"]:
        base.insert(0, "Consider engineering controls (lifting aids, height-adjustable benches).")
        if tool == "NZMAC":
            base.append("Reduce load weight or split lifts into smaller units.")
        if tool == "NZRAPP":
            base.append("Reduce initial push/pull force and improve wheel/surface condition.")
        if tool == "NZART":
            base.append("Redesign tasks to lower repetition rate or awkward neck/shoulder posture.")
    return base[:4]

# --------------------
# Sidebar Navigation
# --------------------
st.sidebar.title("MSD Survey Demo")
page = st.sidebar.radio("Navigation", ["New Survey", "History & Trends", "Import/Export", "Admin (Thresholds)"])
st.sidebar.markdown("---")
st.sidebar.caption("Demo only. Scores are simplified surrogates of NZMAC/NZRAPP/NZART.")

# --------------------
# Page: New Survey
# --------------------
if page == "New Survey":
    st.title("📝 New Risk Survey")

    with st.form("survey"):
        colA, colB = st.columns([1.2, 1])
        with colA:
            tool = st.selectbox("Choose Tool", ["NZMAC (Lifting)", "NZRAPP (Pushing/Pulling)", "NZART (Repetitive Upper Limb)"])
            task_name = st.text_input("Task name", placeholder="e.g., Lift cartons / Push trolley / Assembly")
            duration_min = st.number_input("Duration per task (min)", 0, 300, 10, 1)
            frequency_per_hr = st.number_input("Frequency per hour", 0, 120, 20, 1)
            posture = st.selectbox("General posture", POSTURES, index=0)

            # tool-specific inputs
            if tool.startswith("NZMAC"):
                st.subheader("NZMAC – Lifting Inputs")
                load_kg = st.number_input("Load weight (kg)", 0.0, 80.0, 12.0, 0.5)
                lift_height = st.selectbox("Lift height", LIFT_HEIGHTS, index=1)
                push_pull_force_kg = distance_m = None
                surface = None
                reps_per_min = cycle_time_sec = None
                neck_shoulder_awk = "mild"  # for completeness
            elif tool.startswith("NZRAPP"):
                st.subheader("NZRAPP – Pushing/Pulling Inputs")
                push_pull_force_kg = st.number_input("Push/Pull initial force (kg)", 0.0, 60.0, 18.0, 0.5)
                distance_m = st.number_input("Travel distance (m)", 0.0, 200.0, 25.0, 1.0)
                surface = st.selectbox("Floor surface", SURFACES, index=0)
                load_kg = None
                lift_height = None
                reps_per_min = cycle_time_sec = None
                neck_shoulder_awk = "none"
            else:
                st.subheader("NZART – Repetitive Upper Limb Inputs")
                reps_per_min = st.number_input("Repetitions per minute", 0, 120, 28, 1)
                cycle_time_sec = st.number_input("Cycle time (sec)", 2, 120, 12, 1)
                neck_shoulder_awk = st.selectbox("Neck/Shoulder awkwardness", NECK_SHOULDER, index=1)
                load_kg = None
                lift_height = None
                push_pull_force_kg = distance_m = None
                surface = None

        with colB:
            st.info("🔎 Simple scoring model (0–100). Tiers use adjustable thresholds in **Admin**.")
            st.metric("High Risk ≥", st.session_state.thresholds["high"])
            st.metric("Med-High ≥", st.session_state.thresholds["med_high"])
            st.metric("Medium ≥", st.session_state.thresholds["med"])

        submitted = st.form_submit_button("Calculate risk & save")
    if submitted:
        # compute score
        if tool.startswith("NZMAC"):
            score = score_nzmac(load_kg, frequency_per_hr, posture, lift_height)
            tool_tag = "NZMAC"
        elif tool.startswith("NZRAPP"):
            score = score_nzrapp(push_pull_force_kg, distance_m, surface, frequency_per_hr)
            tool_tag = "NZRAPP"
        else:
            score = score_nzart(reps_per_min, cycle_time_sec, neck_shoulder_awk, posture)
            tool_tag = "NZART"

        tier = tier_from_score(score, st.session_state.thresholds)

        row = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "tool": tool_tag,
            "task_name": task_name or "(untitled task)",
            "duration_min": duration_min,
            "frequency_per_hr": frequency_per_hr,
            "posture": posture,
            "load_kg": load_kg,
            "lift_height": lift_height,
            "push_pull_force_kg": push_pull_force_kg,
            "distance_m": distance_m,
            "surface": surface,
            "reps_per_min": reps_per_min,
            "cycle_time_sec": cycle_time_sec,
            "neck_shoulder_awk": neck_shoulder_awk,
            "risk_score": round(score, 1),
            "risk_tier": tier,
        }
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([row])], ignore_index=True)

        st.success(f"✅ Saved! Risk score = **{round(score,1)}** → **{tier}**")
        st.subheader("Suggested Controls")
        for i, rec in enumerate(recommendations(tier, tool_tag), 1):
            st.write(f"{i}. {rec}")

        with st.expander("View saved record"):
            st.dataframe(pd.DataFrame([row]).T, use_container_width=True)

# --------------------
# Page: History & Trends
# --------------------
elif page == "History & Trends":
    st.title("📈 History & Trends")
    df = st.session_state.df.copy()

    col1, col2 = st.columns([1.2, 1])
    with col1:
        filt_tool = st.selectbox("Filter by tool", ["All", "NZMAC", "NZRAPP", "NZART"])
        if filt_tool != "All":
            df = df[df["tool"] == filt_tool]

        if df.empty:
            st.warning("No data for the current filter.")
        else:
            # line plot of average score by date
            df_plot = df.copy()
            df_plot["date"] = pd.to_datetime(df_plot["timestamp"]).dt.date
            avg = df_plot.groupby("date")["risk_score"].mean().reset_index()

            fig, ax = plt.subplots(figsize=(7, 4))
            ax.plot(avg["date"], avg["risk_score"], marker="o")
            ax.set_xlabel("Date")
            ax.set_ylabel("Average Risk Score")
            ax.set_title("Risk Trend")
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)

    with col2:
        st.caption("Download current data")
        st.download_button(
            "Download CSV",
            data=st.session_state.df.to_csv(index=False).encode("utf-8"),
            file_name="msd_survey_data.csv",
            mime="text/csv",
        )

    st.subheader("Recent Records")
    st.dataframe(st.session_state.df.tail(50), use_container_width=True)

# --------------------
# Page: Import/Export
# --------------------
elif page == "Import/Export":
    st.title("⬇️ Export / ⬆️ Import")
    st.write("Preview of current data:")
    st.dataframe(st.session_state.df.head(20), use_container_width=True)

    st.markdown("### Import CSV (replace all data)")
    up = st.file_uploader("Upload a CSV exported from this tool", type=["csv"])
    if up is not None:
        try:
            new_df = pd.read_csv(up)
            # align columns
            for c in COLUMNS:
                if c not in new_df.columns:
                    new_df[c] = None
            st.session_state.df = new_df[COLUMNS]
            st.success("✅ Data replaced.")
        except Exception as e:
            st.error(f"Import failed: {e}")

    st.download_button(
        "Download current CSV",
        data=st.session_state.df.to_csv(index=False).encode("utf-8"),
        file_name="msd_survey_data.csv",
        mime="text/csv",
    )

# --------------------
# Page: Admin
# --------------------
else:
    st.title("⚙️ Admin – Adjust Risk Thresholds")
    th = st.session_state.thresholds
    st.write("These thresholds define **risk tiers** from the 0–100 score.")

    c1, c2, c3 = st.columns(3)
    with c1:
        th["high"] = st.slider("High (≥)", 55, 95, th["high"], 1)
    with c2:
        th["med_high"] = st.slider("Med-High (≥)", 40, th["high"], th["med_high"], 1)
    with c3:
        th["med"] = st.slider("Medium (≥)", 20, th["med_high"], th["med"], 1)

    # Preview tier distribution
    df = st.session_state.df.copy()
    df["tier_preview"] = [tier_from_score(s, th) for s in df["risk_score"]]
    st.subheader("Preview of tier distribution with new thresholds")
    st.dataframe(df[["timestamp", "task_name", "tool", "risk_score", "tier_preview"]].tail(30), use_container_width=True)

    if st.button("Reset to defaults"):
        st.session_state.thresholds = DEFAULT_THRESHOLDS.copy()
        st.success("Reset done.")

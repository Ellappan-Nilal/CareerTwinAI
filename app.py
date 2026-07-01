"""
app.py
CareerTwin AI - main Streamlit application.
Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd

import database as db
import career_match
import skill_gap
import roadmap as roadmap_module
import interview as interview_module
import resume_review
import dashboard

st.set_page_config(page_title="CareerTwin AI", page_icon="🎯", layout="wide")

# ---------------- Init ----------------
db.init_db()

if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = ""
if "interview_qa_log" not in st.session_state:
    st.session_state.interview_qa_log = []  # current session's questions (avoid repeats)
if "current_question" not in st.session_state:
    st.session_state.current_question = None

# ---------------- Sidebar: login + API key ----------------
with st.sidebar:
    st.title("🎯 CareerTwin AI")
    st.caption("Your Personal Career Mentor")

    st.subheader("Setup")
    api_key_input = st.text_input("Gemini API Key", type="password", value=st.session_state.gemini_api_key)
    st.session_state.gemini_api_key = api_key_input

    st.divider()
    st.subheader("Your Profile")
    name = st.text_input("Name", key="input_name")
    email = st.text_input("Email", key="input_email")
    if st.button("Login / Continue", use_container_width=True):
        if name and email:
            st.session_state.user_id = db.create_or_get_user(name, email)
            st.success(f"Welcome, {name}!")
        else:
            st.warning("Enter both name and email.")

    st.divider()
    page = st.radio(
        "Navigate",
        [
            "1. Skill Analysis",
            "2. Career Match",
            "3. Skill Gap Analysis",
            "4. Learning Roadmap",
            "5. Project Recommendation",
            "6. Resume Review",
            "7. Mock Interview",
            "8. Progress Dashboard",
        ],
    )

# ---------------- Guard: require login ----------------
if not st.session_state.user_id:
    st.info("👈 Enter your name and email in the sidebar, then click **Login / Continue** to get started.")
    st.stop()

if not st.session_state.gemini_api_key:
    st.warning("👈 Add your Gemini API key in the sidebar to unlock AI features.")

user_id = st.session_state.user_id

# ==========================================================
# 1. SKILL ANALYSIS
# ==========================================================
if page.startswith("1"):
    st.header("🧩 Skill Analysis")
    st.write("Add your current skills so CareerTwin AI can understand your strengths.")

    col1, col2 = st.columns([3, 1])
    with col1:
        new_skill = st.text_input("Skill name (e.g. Python, SQL, Communication)")
    with col2:
        proficiency = st.selectbox("Proficiency", ["Beginner", "Intermediate", "Advanced"])

    if st.button("Add Skill"):
        if new_skill.strip():
            db.add_skill(user_id, new_skill.strip(), proficiency)
            st.success(f"Added: {new_skill} ({proficiency})")
            st.rerun()
        else:
            st.warning("Enter a skill name first.")

    skills = db.get_skills(user_id)
    if skills:
        st.subheader("Your Skills")
        df = pd.DataFrame(skills)[["skill_name", "proficiency", "added_at"]]
        df.columns = ["Skill", "Proficiency", "Added On"]
        st.dataframe(df, use_container_width=True, hide_index=True)

        if st.button("🗑️ Clear All Skills"):
            db.clear_skills(user_id)
            st.rerun()
    else:
        st.caption("No skills added yet.")

# ==========================================================
# 2. CAREER MATCH
# ==========================================================
elif page.startswith("2"):
    st.header("🎯 Career Match")
    skills = [s["skill_name"] for s in db.get_skills(user_id)]

    if not skills:
        st.warning("Add some skills first in the Skill Analysis tab.")
    else:
        interests = st.text_area("Interests / preferences (optional)",
                                  placeholder="e.g. I enjoy working with data, prefer remote roles...")
        if st.button("🔍 Find Matching Careers"):
            with st.spinner("Analyzing your profile..."):
                try:
                    matches = career_match.get_career_matches(skills, interests)
                    if matches:
                        db.save_career_matches(user_id, matches)
                        st.session_state["last_matches"] = matches
                except Exception as e:
                    st.error(f"Error: {e}")

        matches = st.session_state.get("last_matches") or [
            {"role_name": m["role_name"], "match_score": m["match_score"], "rationale": m["rationale"]}
            for m in db.get_career_matches(user_id)[:5]
        ]
        if matches:
            st.subheader("Recommended Roles")
            for m in matches:
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"**{m['role_name']}**")
                    c1.caption(m.get("rationale", ""))
                    c2.metric("Match", f"{m.get('match_score', 0)}%")

# ==========================================================
# 3. SKILL GAP ANALYSIS
# ==========================================================
elif page.startswith("3"):
    st.header("📊 Skill Gap Analysis")
    skills = [s["skill_name"] for s in db.get_skills(user_id)]
    target_role = st.text_input("Target role", placeholder="e.g. Data Analyst, AI Engineer")

    if not skills:
        st.warning("Add some skills first in the Skill Analysis tab.")
    elif st.button("🔍 Analyze Gap") and target_role:
        with st.spinner("Comparing your skills to the target role..."):
            try:
                gaps = skill_gap.get_skill_gaps(skills, target_role)
                if gaps:
                    db.save_skill_gaps(user_id, target_role, gaps)
                    st.session_state["last_gaps"] = gaps
            except Exception as e:
                st.error(f"Error: {e}")

    gaps = st.session_state.get("last_gaps")
    if gaps:
        st.subheader(f"Missing Skills for: {target_role}")
        priority_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
        for g in gaps:
            icon = priority_color.get(g.get("priority", "Medium"), "🟡")
            st.markdown(f"{icon} **{g['skill']}** — {g.get('reason', '')}")

# ==========================================================
# 4. LEARNING ROADMAP
# ==========================================================
elif page.startswith("4"):
    st.header("🗺️ Learning Roadmap")
    skills = [s["skill_name"] for s in db.get_skills(user_id)]
    target_role = st.text_input("Target role for roadmap", placeholder="e.g. Cloud Engineer")
    duration = st.select_slider("Duration (days)", options=[30, 60, 90], value=30)

    if st.button("🛠️ Generate Roadmap") and target_role:
        with st.spinner(f"Building your {duration}-day roadmap..."):
            try:
                tasks = roadmap_module.generate_roadmap(target_role, skills, duration)
                if tasks:
                    db.save_roadmap_tasks(user_id, target_role, tasks)
                    st.success("Roadmap generated and saved!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    if target_role:
        existing = db.get_roadmap_tasks(user_id, target_role)
        if existing:
            st.subheader(f"Roadmap: {target_role}")
            pct = db.get_roadmap_completion_pct(user_id, target_role)
            st.progress(pct / 100, text=f"{pct}% complete")

            for t in existing:
                checked = st.checkbox(
                    f"Day {t['day_number']}: {t['task_description']}",
                    value=bool(t["is_completed"]),
                    key=f"task_{t['id']}",
                )
                if checked != bool(t["is_completed"]):
                    db.mark_task_complete(t["id"], checked)
                    st.rerun()

# ==========================================================
# 5. PROJECT RECOMMENDATION
# ==========================================================
elif page.startswith("5"):
    st.header("💡 Project Recommendations")
    target_role = st.text_input("Target role for projects", placeholder="e.g. Python Developer")

    if st.button("✨ Suggest Projects") and target_role:
        with st.spinner("Finding relevant projects..."):
            try:
                projects = roadmap_module.get_project_recommendations(target_role)
                st.session_state["last_projects"] = projects
            except Exception as e:
                st.error(f"Error: {e}")

    projects = st.session_state.get("last_projects")
    if projects:
        tabs = st.tabs(["🟢 Beginner", "🟡 Intermediate", "🔴 Advanced"])
        for tab, level in zip(tabs, ["beginner", "intermediate", "advanced"]):
            with tab:
                for p in projects.get(level, []):
                    with st.container(border=True):
                        st.markdown(f"**{p['title']}**")
                        st.caption(p.get("description", ""))

# ==========================================================
# 6. RESUME REVIEW
# ==========================================================
elif page.startswith("6"):
    st.header("📄 Resume Review")

    # ---- Portfolio Projects Panel ----
    with st.expander("🗂️ Portfolio Projects (included in AI analysis)", expanded=True):
        st.caption("Add your projects so the AI can give feedback on how well they're presented in your resume.")

        col_t, col_d = st.columns([2, 3])
        with col_t:
            proj_title = st.text_input("Project Title", placeholder="e.g. CareerTwin AI", key="proj_title")
        with col_d:
            proj_desc = st.text_input("Short Description", placeholder="e.g. AI-powered career mentor web app built with Streamlit and OpenAI", key="proj_desc")

        col_ts, col_lnk = st.columns([2, 2])
        with col_ts:
            proj_tech = st.text_input("Tech Stack", placeholder="e.g. Python, Streamlit, OpenAI, SQLite", key="proj_tech")
        with col_lnk:
            proj_link = st.text_input("Link (optional)", placeholder="e.g. https://github.com/you/careertwinai", key="proj_link")

        if st.button("➕ Add Project", use_container_width=True):
            if proj_title.strip() and proj_desc.strip() and proj_tech.strip():
                db.add_project(user_id, proj_title.strip(), proj_desc.strip(), proj_tech.strip(), proj_link.strip())
                st.success(f"✅ Added project: {proj_title}")
                st.rerun()
            else:
                st.warning("Please fill in Title, Description, and Tech Stack.")

        saved_projects = db.get_projects(user_id)
        if saved_projects:
            st.markdown("**Your Projects:**")
            for proj in saved_projects:
                pcol1, pcol2 = st.columns([5, 1])
                with pcol1:
                    link_md = f" — [🔗 link]({proj['link']})" if proj.get("link") else ""
                    st.markdown(f"**{proj['title']}** | *{proj['tech_stack']}*{link_md}  \n{proj['description']}")
                with pcol2:
                    if st.button("🗑️", key=f"del_proj_{proj['id']}", help="Delete project"):
                        db.delete_project(proj["id"], user_id)
                        st.rerun()
        else:
            st.caption("No projects added yet.")

    st.divider()

    # ---- Resume Upload & Review ----
    target_role = st.text_input("Target role (optional, improves relevance)", key="rr_target_role")
    uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])

    if uploaded_file and st.button("🔍 Review Resume"):
        with st.spinner("Analyzing your resume + projects..."):
            try:
                projects_for_review = db.get_projects(user_id)
                result = resume_review.review_resume(uploaded_file, target_role, projects_for_review)
                db.save_resume_review(user_id, uploaded_file.name, str(result))
                st.session_state["last_resume_review"] = result
            except Exception as e:
                st.error(f"Error: {e}")

    result = st.session_state.get("last_resume_review")
    if result:
        st.metric("Overall Score", f"{result.get('overall_score', 0)}/100")

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("✅ Strengths")
            for s in result.get("strengths", []):
                st.markdown(f"- {s}")
        with c2:
            st.subheader("⚠️ Missing Sections")
            for m in result.get("missing_sections", []):
                st.markdown(f"- {m}")

        st.subheader("🔧 Improvements")
        for imp in result.get("improvements", []):
            st.markdown(f"**{imp.get('area', '')}:** {imp.get('suggestion', '')}")

        proj_feedback = result.get("project_feedback", [])
        if proj_feedback:
            st.subheader("💡 Project Presentation Feedback")
            for pf in proj_feedback:
                with st.container(border=True):
                    st.markdown(f"**{pf.get('project', '')}**")
                    st.caption(pf.get("feedback", ""))

# ==========================================================
# 7. MOCK INTERVIEW
# ==========================================================
elif page.startswith("7"):
    st.header("🎤 Mock Interview")
    target_role = st.text_input("Interview for role", placeholder="e.g. AI Engineer")
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])

    if st.button("▶️ Start / Next Question") and target_role:
        with st.spinner("Preparing question..."):
            try:
                q = interview_module.get_next_question(
                    target_role, difficulty, st.session_state.interview_qa_log
                )
                st.session_state.current_question = q
                st.session_state.interview_qa_log.append(q)
            except Exception as e:
                st.error(f"Error: {e}")

    if st.session_state.current_question:
        st.subheader("Question")
        st.info(st.session_state.current_question)

        answer = st.text_area("Your answer", key="interview_answer")
        if st.button("✅ Submit Answer") and answer.strip():
            with st.spinner("Evaluating your answer..."):
                try:
                    eval_result = interview_module.evaluate_answer(
                        st.session_state.current_question, answer, target_role
                    )
                    db.save_interview_result(
                        user_id, target_role,
                        st.session_state.current_question, answer,
                        eval_result.get("score", 0),
                        eval_result.get("feedback", ""),
                    )
                    st.success(f"Score: {eval_result.get('score', 0)}/10")
                    st.write(eval_result.get("feedback", ""))
                    st.subheader("Improvement Tips")
                    for tip in eval_result.get("improvement_tips", []):
                        st.markdown(f"- {tip}")
                    st.session_state.current_question = None
                except Exception as e:
                    st.error(f"Error: {e}")

    st.divider()
    history = db.get_interview_history(user_id)
    if history:
        st.subheader("Past Attempts")
        df = pd.DataFrame(history)[["target_role", "question", "score", "created_at"]]
        df.columns = ["Role", "Question", "Score", "Date"]
        st.dataframe(df, use_container_width=True, hide_index=True)

# ==========================================================
# 8. PROGRESS DASHBOARD
# ==========================================================
elif page.startswith("8"):
    st.header("📈 Progress Dashboard")

    skills = db.get_skills(user_id)
    history = db.get_interview_history(user_id)

    col1, col2, col3 = st.columns(3)
    col1.metric("Skills Logged", len(skills))
    col2.metric("Mock Interviews Taken", len(history))
    col3.metric("Avg Interview Score", f"{dashboard.average_interview_score(history)}/10")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        fig = dashboard.skills_breakdown_chart(skills)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("No skill data yet.")
    with c2:
        fig = dashboard.interview_score_history_chart(history)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("No interview data yet.")

    st.divider()
    st.subheader("Roadmap Completion")
    role_for_roadmap = st.text_input("Check roadmap progress for role")
    if role_for_roadmap:
        pct = db.get_roadmap_completion_pct(user_id, role_for_roadmap)
        fig = dashboard.roadmap_completion_gauge(pct, role_for_roadmap)
        st.plotly_chart(fig, use_container_width=True)

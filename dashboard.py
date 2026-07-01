"""
dashboard.py
Builds Plotly figures for the Progress Dashboard tab:
- Skills completed / added over time
- Interview score history
- Roadmap completion percentage
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def skills_breakdown_chart(skills: list):
    """Bar chart of skills by proficiency level."""
    if not skills:
        return None
    df = pd.DataFrame(skills)
    counts = df.groupby("proficiency").size().reset_index(name="count")
    fig = px.bar(
        counts, x="proficiency", y="count",
        title="Skills by Proficiency Level",
        color="proficiency",
        text="count",
    )
    fig.update_layout(showlegend=False, xaxis_title="Proficiency", yaxis_title="Number of Skills")
    return fig


def interview_score_history_chart(interview_history: list):
    """Line chart of mock interview scores over time."""
    if not interview_history:
        return None
    df = pd.DataFrame(interview_history)
    df["attempt"] = range(1, len(df) + 1)
    fig = px.line(
        df, x="attempt", y="score",
        title="Mock Interview Score History",
        markers=True,
        range_y=[0, 10],
    )
    fig.update_layout(xaxis_title="Attempt #", yaxis_title="Score (out of 10)")
    return fig


def roadmap_completion_gauge(completion_pct: float, target_role: str):
    """Gauge chart showing roadmap completion percentage."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=completion_pct,
        title={"text": f"Roadmap Completion: {target_role}"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#4C78A8"},
            "steps": [
                {"range": [0, 33], "color": "#f2dede"},
                {"range": [33, 66], "color": "#fcf8e3"},
                {"range": [66, 100], "color": "#dff0d8"},
            ],
        },
    ))
    fig.update_layout(height=300)
    return fig


def average_interview_score(interview_history: list) -> float:
    if not interview_history:
        return 0.0
    scores = [h.get("score", 0) for h in interview_history if h.get("score") is not None]
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 1)

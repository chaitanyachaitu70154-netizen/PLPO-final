"""
Interactive Data Visualization Components using Plotly.
Visualizes mastery states, confidence calibration, radar profiles, and historical trends.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List
from core.knowledge_state import KnowledgeState
from utils.config import CONFIG, get_mastery_color

def plot_topic_mastery_barchart(knowledge_state: KnowledgeState) -> go.Figure:
    """Horizontal bar chart showing topic mastery vs proficiency thresholds."""
    topics = list(knowledge_state.topics.keys())
    scores = [knowledge_state.topics[t].percentage for t in topics]
    confidences = [knowledge_state.topics[t].confidence_percentage for t in topics]
    colors = [get_mastery_color(s) for s in scores]

    df = pd.DataFrame({
        "Topic": topics,
        "Mastery": scores,
        "Confidence": confidences,
        "Color": colors
    }).sort_values("Mastery", ascending=True)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=df["Topic"],
        x=df["Mastery"],
        orientation="h",
        marker=dict(
            color=df["Color"],
            line=dict(color="#CBD5E1", width=1),
            cornerradius=4
        ),
        text=[f"{s:.0f}%" for s in df["Mastery"]],
        textposition="inside",
        textfont=dict(color="white", size=13, family="sans-serif"),
        hovertemplate="<b>%{y}</b><br>Mastery: %{x:.1f}%<br>Confidence: %{customdata:.1f}%<extra></extra>",
        customdata=df["Confidence"]
    ))

    # Add 80% threshold line (Mastered)
    fig.add_vline(
        x=80,
        line_dash="dash",
        line_color="#10B981",
        annotation_text="Mastery (80%)",
        annotation_position="top right",
        annotation_font=dict(size=10, color="#10B981")
    )

    # Add 60% threshold line (Proficient)
    fig.add_vline(
        x=60,
        line_dash="dot",
        line_color="#F59E0B",
        annotation_text="Proficiency (60%)",
        annotation_position="top left",
        annotation_font=dict(size=10, color="#F59E0B")
    )

    fig.update_layout(
        title=dict(
            text="<b>Topic Mastery Distribution</b>",
            font=dict(size=15, color="#0F172A")
        ),
        xaxis=dict(
            title="Assessed Mastery Score (%)",
            range=[0, 105],
            gridcolor="#F1F5F9",
            zerolinecolor="#E2E8F0"
        ),
        yaxis=dict(
            title="",
            tickfont=dict(size=13, color="#1E293B")
        ),
        margin=dict(l=20, r=20, t=40, b=30),
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=320,
        showlegend=False
    )

    return fig

def plot_competency_radar(knowledge_state: KnowledgeState) -> go.Figure:
    """Radar chart comparing current knowledge profile with mastery target."""
    topics = list(knowledge_state.topics.keys())
    # Close polygon
    radar_topics = topics + [topics[0]]
    current_scores = [knowledge_state.topics[t].percentage for t in topics]
    current_scores = current_scores + [current_scores[0]]
    target_scores = [85] * len(radar_topics)

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=target_scores,
        theta=radar_topics,
        fill=None,
        line=dict(color="#94A3B8", dash="dash", width=1.5),
        name="Target Baseline (85%)"
    ))

    fig.add_trace(go.Scatterpolar(
        r=current_scores,
        theta=radar_topics,
        fill='toself',
        fillcolor='rgba(37, 99, 235, 0.25)',
        line=dict(color="#2563EB", width=2.5),
        name="Demo Student"
    ))

    fig.update_layout(
        title=dict(
            text="<b>Curricular Competency Footprint</b>",
            font=dict(size=15, color="#0F172A")
        ),
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor="#E2E8F0",
                tickfont=dict(size=9, color="#64748B")
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color="#1E293B")
            )
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(l=30, r=30, t=40, b=40),
        paper_bgcolor="white",
        height=320
    )

    return fig

def plot_calibration_quadrant(knowledge_state: KnowledgeState) -> go.Figure:
    """Quadrant chart plotting confidence vs actual mastery to detect calibration & blind spots."""
    data = []
    for name, topic in knowledge_state.topics.items():
        data.append({
            "Topic": name,
            "Mastery": topic.percentage,
            "Confidence": topic.confidence_percentage,
            "Color": get_mastery_color(topic.percentage)
        })

    df = pd.DataFrame(data)

    fig = go.Figure()

    # Quadrant background colors / shading
    # Top-Left: Overconfident / High Risk (Low mastery, high confidence)
    fig.add_shape(type="rect", x0=0, y0=60, x1=60, y1=100,
                  fillcolor="rgba(239, 68, 68, 0.06)", line_width=0, layer="below")
    # Top-Right: Mastered & Calibrated (High mastery, high confidence)
    fig.add_shape(type="rect", x0=60, y0=60, x1=100, y1=100,
                  fillcolor="rgba(16, 185, 129, 0.06)", line_width=0, layer="below")
    # Bottom-Left: Emerging & Aware
    fig.add_shape(type="rect", x0=0, y0=0, x1=60, y1=60,
                  fillcolor="rgba(245, 158, 11, 0.06)", line_width=0, layer="below")
    # Bottom-Right: Impostor / Hesitant (High mastery, low confidence)
    fig.add_shape(type="rect", x0=60, y0=0, x1=100, y1=60,
                  fillcolor="rgba(59, 130, 246, 0.06)", line_width=0, layer="below")

    # Midpoint dividing lines
    fig.add_vline(x=60, line_dash="dash", line_color="#CBD5E1", line_width=1)
    fig.add_hline(y=60, line_dash="dash", line_color="#CBD5E1", line_width=1)

    # Plot topics
    for _, row in df.iterrows():
        fig.add_trace(go.Scatter(
            x=[row["Mastery"]],
            y=[row["Confidence"]],
            mode="markers+text",
            name=row["Topic"],
            text=[f"<b>{row['Topic']}</b>"],
            textposition="top center",
            textfont=dict(size=11, color="#1E293B"),
            marker=dict(
                size=16,
                color=row["Color"],
                line=dict(width=2, color="white")
            ),
            hovertemplate="<b>%{text}</b><br>Mastery: %{x:.0f}%<br>Confidence: %{y:.0f}%<extra></extra>"
        ))

    # Add quadrant labels
    fig.add_annotation(x=30, y=95, text="⚠️ Blind Spot / Overconfident", showarrow=False, font=dict(size=10, color="#EF4444"))
    fig.add_annotation(x=80, y=95, text="✅ Calibrated Mastery", showarrow=False, font=dict(size=10, color="#10B981"))
    fig.add_annotation(x=30, y=10, text="📖 Growth Area (Aware)", showarrow=False, font=dict(size=10, color="#F59E0B"))
    fig.add_annotation(x=80, y=10, text="💡 Hesitant / Underconfident", showarrow=False, font=dict(size=10, color="#2563EB"))

    fig.update_layout(
        title=dict(
            text="<b>Confidence vs. Mastery Calibration Matrix</b>",
            font=dict(size=15, color="#0F172A")
        ),
        xaxis=dict(title="Assessed Mastery (%)", range=[0, 100], gridcolor="#F1F5F9"),
        yaxis=dict(title="Self-Reported Confidence (%)", range=[0, 100], gridcolor="#F1F5F9"),
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=320,
        margin=dict(l=30, r=30, t=40, b=30)
    )

    return fig

def plot_historical_trajectory(history_records: List[Dict]) -> go.Figure:
    """Time-series chart showing weekly progression of topics and overall mastery."""
    df = pd.DataFrame(history_records)

    fig = go.Figure()

    topics = ["Variables", "Conditions", "Loops", "Functions", "Lists"]
    palette = {
        "Variables": "#10B981",
        "Conditions": "#3B82F6",
        "Loops": "#F59E0B",
        "Functions": "#EF4444",
        "Lists": "#8B5CF6"
    }

    for topic in topics:
        fig.add_trace(go.Scatter(
            x=df["week"],
            y=df[topic],
            mode="lines+markers",
            name=topic,
            line=dict(color=palette.get(topic, "#64748B"), width=2),
            marker=dict(size=6)
        ))

    # Overall line
    fig.add_trace(go.Scatter(
        x=df["week"],
        y=df["overall"],
        mode="lines+markers",
        name="Overall Mastery",
        line=dict(color="#0F172A", width=3, dash="dot"),
        marker=dict(size=8, symbol="diamond")
    ))

    fig.update_layout(
        title=dict(
            text="<b>Multi-Week Knowledge Trajectory</b>",
            font=dict(size=15, color="#0F172A")
        ),
        xaxis=dict(title="Timeline", gridcolor="#F1F5F9"),
        yaxis=dict(title="Mastery (%)", range=[0, 100], gridcolor="#F1F5F9"),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.28, xanchor="center", x=0.5),
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=320,
        margin=dict(l=30, r=30, t=40, b=40)
    )

    return fig

import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import numpy as np
from datetime import datetime, timedelta
import time

# Page config
st.set_page_config(
    page_title="Street Light Predictive Maintenance",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Global styles */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 1200px;
    }
    
    /* Main header */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1rem;
    }
    
    /* Compact metrics */
    .metric-container {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 1px solid #f1f5f9;
        height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    /* Alert cards */
    .alert-card {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border: none;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ef4444;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(239, 68, 68, 0.1);
    }
    
    .success-card {
        background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
        border: none;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #22c55e;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(34, 197, 94, 0.1);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    }
    
    /* Chart container */
    .chart-container {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        margin: 1rem 0;
    }
    
    /* Compact sections */
    .compact-section {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #f1f5f9;
    }
    
    /* Modern buttons */
    .stButton > button {
        border-radius: 8px;
        border: none;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Compact selectbox */
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
    
    /* Hide streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 1.5rem;
        }
        .main-header p {
            font-size: 0.9rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Firebase Setup ---
if not firebase_admin._apps:
    cred = credentials.Certificate(r"C:\Users\Poorvi\Downloads\hackindore-b8070-firebase-adminsdk-fbsvc-434bc483cc.json")
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://hackindore-b8070-default-rtdb.asia-southeast1.firebasedatabase.app/"
    })

# Header
st.markdown("""
<div class="main-header">
    <h1>🏙️ Smart Street Light Dashboard</h1>
    <p>Real-time monitoring & predictive maintenance</p>
</div>
""", unsafe_allow_html=True)

ref = db.reference("lux_readings")

# --- Enhanced Data Fetch Function ---
@st.cache_data(ttl=1)  # Cache for 1 second only
def get_data():
    try:
        data = ref.get()
        lux_list = []
        if data:
            current_time = datetime.now()
            data_items = list(data.items())
            
            for i, (key, val) in enumerate(data_items):
                if isinstance(val, dict) and "lux" in val:
                    # Create timestamps with 1-second intervals for real-time visualization
                    timestamp = current_time - timedelta(seconds=(len(data_items) - i) * 1)
                    
                    lux_list.append({
                        "timestamp": timestamp,
                        "lux": float(val["lux"]),
                        "id": key
                    })
        
        df = pd.DataFrame(lux_list)
        if not df.empty:
            df = df.sort_values('timestamp').tail(500)  # Latest 500 points
            df['time_str'] = df['timestamp'].dt.strftime('%H:%M:%S')
            df['date_str'] = df['timestamp'].dt.strftime('%Y-%m-%d')
            # Better datetime formatting for x-axis - show seconds for real-time feel
            df['datetime_str'] = df['timestamp'].dt.strftime('%H:%M:%S')
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# --- Predictive Analysis Functions ---
def analyze_light_patterns(df):
    if df.empty:
        return {}
    
    current_lux = df['lux'].iloc[-1]
    avg_lux = df['lux'].mean()
    std_lux = df['lux'].std()
    
    # Define proper thresholds for street lights
    critical_low = 50    # Street light failure
    warning_low = 100    # Dimming bulb
    normal_min = 150     # Normal operation
    
    # Maintenance predictions
    maintenance_score = 0
    alerts = []
    
    # Check for consistently low readings (possible bulb failure)
    recent_readings = df.tail(10)['lux']
    if recent_readings.mean() < critical_low:
        maintenance_score += 40
        alerts.append("🚨 Critical: Street light failure detected")
    elif recent_readings.mean() < warning_low:
        maintenance_score += 25
        alerts.append("⚠️ Warning: Bulb dimming detected")
    
    # Check for high variance (possible electrical issues)
    if std_lux > 50:
        maintenance_score += 20
        alerts.append("⚡ High variance - check electrical connections")
    
    # Check for recent spikes (possible sensor issues)
    recent_spikes = df.tail(20)
    if (recent_spikes['lux'] > 1000).sum() > 2:
        maintenance_score += 15
        alerts.append("📊 Sensor spikes detected - check sensor calibration")
    
    # Determine status
    if maintenance_score > 50:
        status = "🔴 Needs Immediate Attention"
        color = "red"
    elif maintenance_score > 25:
        status = "🟡 Schedule Maintenance Soon"
        color = "orange"
    else:
        status = "🟢 Operating Normally"
        color = "green"
    
    return {
        "current_lux": current_lux,
        "avg_lux": avg_lux,
        "std_lux": std_lux,
        "maintenance_score": maintenance_score,
        "status": status,
        "color": color,
        "alerts": alerts,
        "critical_low": critical_low,
        "warning_low": warning_low,
        "normal_min": normal_min
    }

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Controls")
    
    auto_refresh = st.checkbox("🔄 Auto-refresh", value=True)
    show_thresholds = st.checkbox("📏 Thresholds", value=True)
    chart_type = st.selectbox("📊 Chart", ["Line Chart", "Area Chart", "Scatter Plot"])
    time_range = st.selectbox("📅 Range", ["Last 1 Minute", "Last 5 Minutes", "Last 15 Minutes", "Last Hour", "Last 6 Hours", "All Data"])
    
    st.markdown("---")
    st.markdown("### 📊 Status Guide")
    st.markdown("""
    🔴 **Critical** < 50 lux  
    🟡 **Warning** < 100 lux  
    🟢 **Normal** > 150 lux
    """)

# Main dashboard
df = get_data()

if df.empty:
    st.warning("📭 No data available. Check sensor connection.")
    st.stop()

# Filter by time range
if time_range != "All Data":
    time_map = {
        "Last 1 Minute": 1/60,
        "Last 5 Minutes": 5/60, 
        "Last 15 Minutes": 15/60, 
        "Last Hour": 1, 
        "Last 6 Hours": 6
    }
    hours = time_map[time_range]
    cutoff_time = datetime.now() - timedelta(hours=hours)
    df = df[df['timestamp'] > cutoff_time]

analysis = analyze_light_patterns(df)

# Metrics row
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "🔆 Current Lux", 
        f"{analysis['current_lux']:.1f}",
        delta=f"{analysis['current_lux'] - analysis['avg_lux']:.1f}"
    )

with col2:
    st.metric(
        "📊 Average Lux", 
        f"{analysis['avg_lux']:.1f}",
        delta=f"±{analysis['std_lux']:.1f}"
    )

with col3:
    st.metric(
        "📈 Total Readings", 
        len(df),
        delta=f"Last {time_range.lower()}"
    )

with col4:
    st.metric(
        "🎯 Maintenance Score", 
        f"{analysis['maintenance_score']}/100",
        delta="Points"
    )

with col5:
    status_color = {"red": "🔴", "orange": "🟡", "green": "🟢"}[analysis['color']]
    st.metric(
        "🏥 System Status", 
        status_color,
        delta=analysis['status'].split(' ', 1)[1]
    )

# Status and alerts
if analysis['maintenance_score'] > 50:
    st.markdown(f"""
    <div class="alert-card">
        <h4>🚨 CRITICAL ALERT</h4>
        <p><strong>{analysis['status']}</strong></p>
        <small>Score: {analysis['maintenance_score']}/100</small>
    </div>
    """, unsafe_allow_html=True)
elif analysis['maintenance_score'] > 25:
    st.warning(f"⚠️ **{analysis['status']}** - Score: {analysis['maintenance_score']}/100")
else:
    st.markdown(f"""
    <div class="success-card">
        <h4>✅ System Healthy</h4>
        <p><strong>{analysis['status']}</strong></p>
        <small>Score: {analysis['maintenance_score']}/100</small>
    </div>
    """, unsafe_allow_html=True)

# Alerts (more compact)
if analysis['alerts']:
    with st.expander("🔔 Active Alerts", expanded=True):
        for alert in analysis['alerts']:
            st.markdown(f"• {alert}")

# IMPROVED MAIN CHART
st.markdown('<div class="chart-container">', unsafe_allow_html=True)
st.markdown("### 📈 Performance Monitor")

# Create color mapping based on lux levels
def get_color_for_lux(lux_value):
    if lux_value < 50:
        return '#ef4444'  # Red - Critical
    elif lux_value < 100:
        return '#f59e0b'  # Orange - Warning
    elif lux_value < 150:
        return '#eab308'  # Yellow - Caution
    else:
        return '#22c55e'  # Green - Normal

# Add color column to dataframe
df['color'] = df['lux'].apply(get_color_for_lux)
df['status_text'] = df['lux'].apply(lambda x: 
    'Critical' if x < 50 else 
    'Warning' if x < 100 else 
    'Caution' if x < 150 else 
    'Normal'
)

# Create the improved chart
fig = go.Figure()

if chart_type == "Area Chart":
    # Area chart with gradient fill
    fig.add_trace(go.Scatter(
        x=df['datetime_str'],
        y=df['lux'],
        mode='lines',
        name='Light Intensity',
        line=dict(color='#3b82f6', width=3),
        fill='tonexty',
        fillcolor='rgba(59, 130, 246, 0.1)',
        hovertemplate='<b>%{x}</b><br>Lux: %{y:.1f}<br>Status: %{customdata}<extra></extra>',
        customdata=df['status_text']
    ))
elif chart_type == "Scatter Plot":
    # Scatter plot with color coding
    fig.add_trace(go.Scatter(
        x=df['datetime_str'],
        y=df['lux'],
        mode='markers',
        name='Light Readings',
        marker=dict(
            color=df['lux'],
            colorscale=[[0, '#ef4444'], [0.3, '#f59e0b'], [0.6, '#eab308'], [1, '#22c55e']],
            size=8,
            colorbar=dict(
                title="Lux Level",
                tickvals=[50, 100, 150, 200],
                ticktext=['Critical', 'Warning', 'Caution', 'Normal']
            )
        ),
        hovertemplate='<b>%{x}</b><br>Lux: %{y:.1f}<br>Status: %{customdata}<extra></extra>',
        customdata=df['status_text']
    ))
else:  # Line Chart (default)
    # Enhanced line chart with better styling
    fig.add_trace(go.Scatter(
        x=df['datetime_str'],
        y=df['lux'],
        mode='lines+markers',
        name='Light Intensity',
        line=dict(color='#3b82f6', width=3),
        marker=dict(
            color=df['lux'],
            colorscale=[[0, '#ef4444'], [0.3, '#f59e0b'], [0.6, '#eab308'], [1, '#22c55e']],
            size=6,
            line=dict(width=1, color='white')
        ),
        hovertemplate='<b>%{x}</b><br>Lux: %{y:.1f}<br>Status: %{customdata}<extra></extra>',
        customdata=df['status_text']
    ))

# Add threshold lines if enabled
if show_thresholds:
    # Critical threshold
    fig.add_hline(
        y=analysis['critical_low'], 
        line_dash="dot", 
        line_color="#ef4444",
        line_width=2,
        annotation_text="🚨 Critical (50 lux)",
        annotation_position="top right"
    )
    
    # Warning threshold
    fig.add_hline(
        y=analysis['warning_low'], 
        line_dash="dash", 
        line_color="#f59e0b",
        line_width=2,
        annotation_text="⚠️ Warning (100 lux)",
        annotation_position="top right"
    )
    
    # Normal threshold
    fig.add_hline(
        y=analysis['normal_min'], 
        line_dash="dashdot", 
        line_color="#22c55e",
        line_width=2,
        annotation_text="✅ Normal (150 lux)",
        annotation_position="top right"
    )

# Add current reading annotation
current_reading = df.iloc[-1]
fig.add_annotation(
    x=current_reading['datetime_str'],
    y=current_reading['lux'],
    text=f"Current<br>{current_reading['lux']:.1f} lux",
    showarrow=True,
    arrowhead=2,
    arrowsize=1,
    arrowwidth=2,
    arrowcolor="#1f2937",
    ax=20,
    ay=-30,
    bgcolor="rgba(255,255,255,0.8)",
    bordercolor="#1f2937",
    borderwidth=1
)

# Update layout with better tick formatting for seconds
fig.update_layout(
    title=dict(
        text=f"Street Light Monitoring - {datetime.now().strftime('%H:%M:%S')}",
        x=0.5,
        font=dict(size=18, color='#1f2937')
    ),
    xaxis=dict(
        title="Time",
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)',
        tickangle=45,
        nticks=20,  # More ticks for second-level data
        tickmode='auto',
        type='category',
        tickfont=dict(size=9)
    ),
    yaxis=dict(
        title="Lux",
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)',
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor='rgba(128,128,128,0.3)',
        tickfont=dict(size=10)
    ),
    height=450,
    template="plotly_white",
    hovermode='x unified',
    showlegend=False,
    margin=dict(l=50, r=50, t=60, b=50),
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)'
)

st.plotly_chart(fig, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# Enhanced insights section (more compact)
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="compact-section">', unsafe_allow_html=True)
    st.markdown("### 📊 Analysis")
    
    # Calculate status distribution
    status_counts = df['status_text'].value_counts()
    total_readings = len(df)
    
    for status in ['Normal', 'Caution', 'Warning', 'Critical']:
        count = status_counts.get(status, 0)
        percentage = (count / total_readings) * 100 if total_readings > 0 else 0
        icon = {'Normal': '🟢', 'Caution': '🟡', 'Warning': '🟠', 'Critical': '🔴'}[status]
        st.markdown(f"{icon} **{status}**: {count} ({percentage:.1f}%)")
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="compact-section">', unsafe_allow_html=True)
    st.markdown("### 🕐 Activity")
    if not df.empty:
        latest_reading = df.iloc[-1]
        time_diff = datetime.now() - latest_reading['timestamp']
        
        st.markdown(f"**Latest:** {latest_reading['timestamp'].strftime('%H:%M:%S')}")
        st.markdown(f"**Updated:** {time_diff.total_seconds():.0f}s ago")
        st.markdown(f"**Status:** {latest_reading['status_text']}")
        st.markdown(f"**Points:** {len(df)} readings")
        
        if len(df) >= 2:
            trend = df['lux'].iloc[-1] - df['lux'].iloc[-2]
            trend_icon = "📈" if trend > 0 else "📉" if trend < 0 else "➡️"
            st.markdown(f"**Trend:** {trend_icon} {trend:+.1f} lux")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Compact data table
with st.expander("📋 Recent Data"):
    display_df = df[['datetime_str', 'lux', 'status_text']].tail(20).copy()
    display_df.columns = ['Time', 'Lux', 'Status']
    st.dataframe(display_df.iloc[::-1], hide_index=True, use_container_width=True, height=300)

# Auto-refresh - reduce sleep time for faster updates
if auto_refresh:
    time.sleep(1)  # Refresh every 1 second
    st.rerun()

# Compact Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #64748b; font-size: 0.9rem; padding: 0.5rem;'>
    🏙️ Smart City Monitoring | Updated: {datetime.now().strftime('%H:%M:%S')} | VCNL4040
</div>
""", unsafe_allow_html=True)
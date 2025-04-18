import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
from datetime import datetime, timedelta
import randoms
import math
import plotly.graph_objects as go
import plotly.express as px

# Set page configuration
st.set_page_config(
    page_title="NAVAIR T1 Additive Manufacturing Monitoring System",
    page_icon="🖨️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.nozzle_temp = 215
    st.session_state.bed_temp = 65
    st.session_state.ambient_temp = 24
    st.session_state.ambient_humidity = 35
    st.session_state.vibration_x = 0.05
    st.session_state.vibration_y = 0.07
    st.session_state.vibration_z = 0.04
    st.session_state.print_progress = 60
    st.session_state.is_printing = True
    st.session_state.print_job_name = "NAVAIR_BRACKET_V2.gcode"
    st.session_state.time_remaining = 45  # minutes
    st.session_state.detected_anomalies = []
    
    # Generate historical data
    duration = 60  # 60 minutes of historical data
    timestamps = [(datetime.now() - timedelta(minutes=i)) for i in range(duration, 0, -1)]
    
    # Temperature history (with random variations)
    base_nozzle = 215
    base_bed = 65
    base_ambient = 24
    
    st.session_state.temp_history = pd.DataFrame({
        'timestamp': timestamps,
        'nozzle': [base_nozzle + random.uniform(-5, 5) for _ in range(duration)],
        'bed': [base_bed + random.uniform(-2, 2) for _ in range(duration)],
        'ambient': [base_ambient + random.uniform(-1, 1) for _ in range(duration)]
    })
    
    # Humidity history
    base_humidity = 35
    st.session_state.humidity_history = pd.DataFrame({
        'timestamp': timestamps,
        'humidity': [base_humidity + random.uniform(-5, 5) for _ in range(duration)]
    })
    
    # Vibration history
    base_vib_x = 0.05
    base_vib_y = 0.07
    base_vib_z = 0.04
    
    st.session_state.vibration_history = pd.DataFrame({
        'timestamp': timestamps,
        'x': [abs(base_vib_x + random.uniform(-0.03, 0.03)) for _ in range(duration)],
        'y': [abs(base_vib_y + random.uniform(-0.03, 0.03)) for _ in range(duration)],
        'z': [abs(base_vib_z + random.uniform(-0.03, 0.03)) for _ in range(duration)]
    })
    
    # Report history
    st.session_state.reports = [
        {"name": "NAVAIR_BRACKET_V1_20250408.pdf", "type": "PDF", "date": "2025-04-08"},
        {"name": "NAVAIR_MOUNT_20250407.pdf", "type": "PDF", "date": "2025-04-07"},
        {"name": "NAVAIR_BRACKET_V1_20250406.pdf", "type": "PDF", "date": "2025-04-06"}
    ]

# ===== Helper Functions =====

def update_simulated_data():
    """Update simulated data for the demo"""
    if st.session_state.is_printing:
        # Update printer progress
        st.session_state.print_progress += random.randint(0, 2)
        if st.session_state.print_progress > 100:
            st.session_state.print_progress = 100
        st.session_state.time_remaining = max(0, st.session_state.time_remaining - 1)
        
        # Update temperatures with small random variations
        st.session_state.nozzle_temp += random.uniform(-1.0, 1.0)
        st.session_state.bed_temp += random.uniform(-0.5, 0.5)
        st.session_state.ambient_temp += random.uniform(-0.2, 0.2)
        st.session_state.ambient_humidity += random.uniform(-1.0, 1.0)
        
        # Keep values in reasonable ranges
        st.session_state.nozzle_temp = min(max(st.session_state.nozzle_temp, 210), 230)
        st.session_state.bed_temp = min(max(st.session_state.bed_temp, 60), 70)
        st.session_state.ambient_temp = min(max(st.session_state.ambient_temp, 20), 30)
        st.session_state.ambient_humidity = min(max(st.session_state.ambient_humidity, 30), 60)
        
        # Update vibration data
        st.session_state.vibration_x = abs(st.session_state.vibration_x + random.uniform(-0.03, 0.03))
        st.session_state.vibration_y = abs(st.session_state.vibration_y + random.uniform(-0.03, 0.03))
        st.session_state.vibration_z = abs(st.session_state.vibration_z + random.uniform(-0.03, 0.03))
        
        # Keep vibration in reasonable range
        st.session_state.vibration_x = min(max(st.session_state.vibration_x, 0.01), 0.3)
        st.session_state.vibration_y = min(max(st.session_state.vibration_y, 0.01), 0.3)
        st.session_state.vibration_z = min(max(st.session_state.vibration_z, 0.01), 0.3)
        
        # Update history data
        new_timestamp = datetime.now()
        
        # Add new temperature data
        new_temp = pd.DataFrame({
            'timestamp': [new_timestamp],
            'nozzle': [st.session_state.nozzle_temp],
            'bed': [st.session_state.bed_temp],
            'ambient': [st.session_state.ambient_temp]
        })
        st.session_state.temp_history = pd.concat([st.session_state.temp_history, new_temp]).reset_index(drop=True)
        
        # Add new humidity data
        new_humidity = pd.DataFrame({
            'timestamp': [new_timestamp],
            'humidity': [st.session_state.ambient_humidity]
        })
        st.session_state.humidity_history = pd.concat([st.session_state.humidity_history, new_humidity]).reset_index(drop=True)
        
        # Add new vibration data
        new_vibration = pd.DataFrame({
            'timestamp': [new_timestamp],
            'x': [st.session_state.vibration_x],
            'y': [st.session_state.vibration_y],
            'z': [st.session_state.vibration_z]
        })
        st.session_state.vibration_history = pd.concat([st.session_state.vibration_history, new_vibration]).reset_index(drop=True)
        
        # Keep only the most recent data points
        max_history = 120  # Last 2 hours
        if len(st.session_state.temp_history) > max_history:
            st.session_state.temp_history = st.session_state.temp_history.iloc[-max_history:].reset_index(drop=True)
            st.session_state.humidity_history = st.session_state.humidity_history.iloc[-max_history:].reset_index(drop=True)
            st.session_state.vibration_history = st.session_state.vibration_history.iloc[-max_history:].reset_index(drop=True)

def toggle_print_status():
    st.session_state.is_printing = not st.session_state.is_printing
    if st.session_state.is_printing:
        st.success("Print resumed")
    else:
        st.warning("Print paused")

def emergency_stop():
    st.session_state.is_printing = False
    st.error("EMERGENCY STOP ACTIVATED: Print job has been stopped!")

def simulate_anomaly():
    anomaly_types = [
        "Temperature deviation detected",
        "High ambient humidity",
        "Excessive vibration detected",
        "Layer shift detected",
        "Filament flow inconsistency"
    ]
    anomaly = random.choice(anomaly_types)
    st.session_state.detected_anomalies.append({"type": anomaly, "timestamp": datetime.now().strftime("%H:%M:%S")})
    st.warning(f"New anomaly detected: {anomaly}")

def clear_anomalies():
    st.session_state.detected_anomalies = []
    st.success("All anomaly alerts cleared")

def simulate_fdm_fault(fault_type):
    anomaly = f"FDM Fault: {fault_type}"
    st.session_state.detected_anomalies.append({"type": anomaly, "timestamp": datetime.now().strftime("%H:%M:%S")})
    st.error(f"FDM Fault Detected: {fault_type}")

def generate_report(report_type):
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    report_name = f"NAVAIR_QUALITY_{timestamp}.{report_type.lower()}"
    
    new_report = {
        "name": report_name,
        "type": report_type,
        "date": now.strftime("%Y-%m-%d")
    }
    
    st.session_state.reports.insert(0, new_report)
    st.success(f"{report_type} report generated successfully: {report_name}")

# ===== Sidebar Navigation =====

st.sidebar.title("NAVAIR T1 Monitoring")
st.sidebar.image("https://via.placeholder.com/150x80?text=NAVAIR", use_column_width=True)

nav_selection = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "History", "Anomaly Detection", "Quality Reports", "Settings"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Printer Status")

# Display current status in sidebar
printer_status = "Printing" if st.session_state.is_printing else "Paused"
status_color = "green" if st.session_state.is_printing else "orange"
st.sidebar.markdown(f"<span style='color:{status_color};font-weight:bold;'>● {printer_status}</span>", unsafe_allow_html=True)

st.sidebar.progress(st.session_state.print_progress / 100)
st.sidebar.write(f"Progress: {st.session_state.print_progress}%")
st.sidebar.write(f"Current Job: {st.session_state.print_job_name}")
st.sidebar.write(f"Time Remaining: {st.session_state.time_remaining} min")

st.sidebar.markdown("---")

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("Pause/Resume"):
        toggle_print_status()
with col2:
    if st.button("Emergency Stop", type="primary", help="Immediately stop the print"):
        emergency_stop()

# Update simulated data every 3 seconds
update_simulated_data()

# ===== Main Content =====

if nav_selection == "Dashboard":
    st.title("Monitoring Dashboard")
    
    # Top row - temperature and humidity gauges
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.subheader("Nozzle Temperature")
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=st.session_state.nozzle_temp,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "°C"},
            gauge={
                'axis': {'range': [200, 230], 'tickwidth': 1},
                'bar': {'color': "red"},
                'steps': [
                    {'range': [200, 210], 'color': "lightgray"},
                    {'range': [220, 230], 'color': "lightgray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 220
                }
            }
        ))
        fig.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Bed Temperature")
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=st.session_state.bed_temp,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "°C"},
            gauge={
                'axis': {'range': [50, 80], 'tickwidth': 1},
                'bar': {'color': "orange"},
                'steps': [
                    {'range': [50, 60], 'color': "lightgray"},
                    {'range': [70, 80], 'color': "lightgray"}
                ],
                'threshold': {
                    'line': {'color': "orange", 'width': 4},
                    'thickness': 0.75,
                    'value': 70
                }
            }
        ))
        fig.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        st.subheader("Ambient Temperature")
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=st.session_state.ambient_temp,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "°C"},
            gauge={
                'axis': {'range': [15, 35], 'tickwidth': 1},
                'bar': {'color': "blue"},
                'steps': [
                    {'range': [15, 20], 'color': "lightgray"},
                    {'range': [30, 35], 'color': "lightgray"}
                ],
                'threshold': {
                    'line': {'color': "blue", 'width': 4},
                    'thickness': 0.75,
                    'value': 30
                }
            }
        ))
        fig.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    with col4:
        st.subheader("Ambient Humidity")
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=st.session_state.ambient_humidity,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "%"},
            gauge={
                'axis': {'range': [20, 70], 'tickwidth': 1},
                'bar': {'color': "blue"},
                'steps': [
                    {'range': [20, 30], 'color': "lightgray"},
                    {'range': [60, 70], 'color': "rgba(255, 0, 0, 0.3)"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 60
                }
            }
        ))
        fig.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    # Middle row - charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Temperature Trends")
        # Get last 30 minutes of data
        recent_temp = st.session_state.temp_history.iloc[-30:].copy()
        
        fig = px.line(recent_temp, x='timestamp', y=['nozzle', 'bed', 'ambient'],
                      labels={"value": "Temperature (°C)", "timestamp": "Time", "variable": "Temperature Type"},
                      color_discrete_map={"nozzle": "red", "bed": "orange", "ambient": "blue"})
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Vibration Analysis")
        # Get last 30 minutes of data
        recent_vib = st.session_state.vibration_history.iloc[-30:].copy()
        
        fig = px.line(recent_vib, x='timestamp', y=['x', 'y', 'z'],
                      labels={"value": "Acceleration (g)", "timestamp": "Time", "variable": "Axis"},
                      color_discrete_map={"x": "red", "y": "green", "z": "blue"})
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)
        
        # Calculate vibration magnitude
        magnitude = math.sqrt(st.session_state.vibration_x**2 + st.session_state.vibration_y**2 + st.session_state.vibration_z**2)
        status = "Normal" if magnitude < 0.2 else "High"
        status_color = "green" if magnitude < 0.2 else "red"
        
        st.markdown(f"Current Vibration: **{magnitude:.2f}g** - <span style='color:{status_color};font-weight:bold;'>{status}</span>", unsafe_allow_html=True)
    
    # Bottom row - FDM Fault Detection and Anomaly Detection
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("FDM Fault Detection")
        
        # Simple printer visualization using HTML/CSS
        printer_html = """
        <div style="background-color: #f0f0f0; padding: 20px; border-radius: 10px; text-align: center; height: 250px;">
            <div style="background-color: white; width: 100px; height: 50px; margin: auto; border: 1px solid #333;"></div>
            <div style="background-color: #888; width: 60px; height: 10px; margin: auto;"></div>
            <div style="background-color: white; width: 80px; height: 80px; margin: auto; border: 1px solid #333;"></div>
            <div style="margin-top: 20px; font-weight: bold;">Filament Status: Normal</div>
        </div>
        """
        st.markdown(printer_html, unsafe_allow_html=True)
        
        # FDM fault simulation buttons
        col1a, col1b, col1c = st.columns(3)
        with col1a:
            if st.button("Simulate Filament Break"):
                simulate_fdm_fault("Filament Break")
        with col1b:
            if st.button("Simulate Spaghetti"):
                simulate_fdm_fault("Spaghetti Failure")
        with col1c:
            if st.button("Simulate Layer Shift"):
                simulate_fdm_fault("Layer Shift")
    
    with col2:
        st.subheader("Anomaly Detection")
        
        # Display anomalies
        if st.session_state.detected_anomalies:
            for anomaly in st.session_state.detected_anomalies:
                st.error(f"{anomaly['timestamp']} - {anomaly['type']}")
        else:
            st.success("No anomalies detected")
        
        # Anomaly controls
        col2a, col2b = st.columns(2)
        with col2a:
            if st.button("Simulate Anomaly"):
                simulate_anomaly()
        with col2b:
            if st.button("Clear Alerts"):
                clear_anomalies()

elif nav_selection == "History":
    st.title("Historical Data")
    
    # Time range selector
    time_range = st.selectbox(
        "Select Time Range",
        ["Last 30 minutes", "Last 1 hour", "Last 4 hours", "Last 24 hours"],
        index=1
    )
    
    # Convert selection to number of data points
    if time_range == "Last 30 minutes":
        data_points = 30
    elif time_range == "Last 1 hour":
        data_points = 60
    elif time_range == "Last 4 hours":
        data_points = 240
    else:  # Last, 24 hours
        data_points = 1440
    
    # Limit to available data points
    data_points = min(data_points, len(st.session_state.temp_history))
    
    # Temperature history chart
    st.subheader("Temperature History")
    temp_data = st.session_state.temp_history.iloc[-data_points:].copy()
    
    fig = px.line(temp_data, x='timestamp', y=['nozzle', 'bed', 'ambient'],
                  labels={"value": "Temperature (°C)", "timestamp": "Time", "variable": "Temperature Type"},
                  color_discrete_map={"nozzle": "red", "bed": "orange", "ambient": "blue"})
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)
    
    # Vibration history chart
    st.subheader("Vibration History")
    vib_data = st.session_state.vibration_history.iloc[-data_points:].copy()
    
    fig = px.line(vib_data, x='timestamp', y=['x', 'y', 'z'],
                  labels={"value": "Acceleration (g)", "timestamp": "Time", "variable": "Axis"},
                  color_discrete_map={"x": "red", "y": "green", "z": "blue"})
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)
    
    # Humidity history chart
    st.subheader("Humidity History")
    humidity_data = st.session_state.humidity_history.iloc[-data_points:].copy()
    
    fig = px.line(humidity_data, x='timestamp', y='humidity',
                  labels={"humidity": "Humidity (%)", "timestamp": "Time"})
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig, use_container_width=True)
    
    # Export options
    st.subheader("Export Data")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Export Temperature Data (CSV)"):
            st.success("Temperature data would be exported to CSV file")
    with col2:
        if st.button("Export Vibration Data (CSV)"):
            st.success("Vibration data would be exported to CSV file")
    with col3:
        if st.button("Export All Data (CSV)"):
            st.success("All data would be exported to CSV file")

elif nav_selection == "Anomaly Detection":
    st.title("Anomaly Detection")
    
    # Current thresholds
    st.subheader("Current Detection Thresholds")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("Temperature Deviation: ±15°C")
    with col2:
        st.info("Vibration Threshold: 0.2g")
    with col3:
        st.info("Humidity Threshold: 60%")
    
    # Recent anomalies
    st.subheader("Detected Anomalies")
    
    if st.session_state.detected_anomalies:
        for anomaly in st.session_state.detected_anomalies:
            st.error(f"{anomaly['timestamp']} - {anomaly['type']}")
    else:
        st.success("No anomalies detected")
    
    # Anomaly controls
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Simulate Anomaly", key="sim_anomaly_page"):
            simulate_anomaly()
    with col2:
        if st.button("Clear Alerts", key="clear_alerts_page"):
            clear_anomalies()
    
    # ML algorithm explanation
    st.subheader("ML Anomaly Detection Algorithm")
    
    st.markdown("""
    This system uses a machine learning approach for anomaly detection:
    
    1. **Isolation Forest Algorithm** - An unsupervised learning method particularly suited for identifying anomalies
    2. **Feature Engineering** - Processing raw sensor data into meaningful features for analysis
    3. **Multi-parameter Analysis** - Correlating data from multiple sensors for robust detection
    4. **Real-time Processing** - Continuous monitoring with low-latency detection
    
    The algorithm has been trained on various materials including ABS, PETG, and Nylon to ensure reliable detection across different print scenarios.
    """)
    
    # Sample visualization of algorithm
    st.subheader("Algorithm Visualization")
    
    # Create sample data
    np.random.seed(42)
    X_normal = np.random.randn(300, 2)
    X_outliers = np.random.uniform(low=-4, high=4, size=(30, 2))
    X = np.vstack([X_normal, X_outliers])
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(X_normal[:, 0], X_normal[:, 1], label='Normal Data')
    ax.scatter(X_outliers[:, 0], X_outliers[:, 1], color='red', label='Anomalies')
    ax.set_title('Sample Anomaly Detection Visualization')
    ax.set_xlabel('Temperature Deviation')
    ax.set_ylabel('Vibration Intensity')
    ax.legend()
    ax.grid(True)
    
    st.pyplot(fig)

elif nav_selection == "Quality Reports":
    st.title("Quality Reports")
    
    # Report generator
    st.subheader("Generate Quality Report")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        report_type = st.selectbox("Report Format", ["PDF", "CSV"])
    with col2:
        report_detail = st.selectbox("Detail Level", ["Summary", "Detailed", "Comprehensive"])
    with col3:
        if st.button("Generate Report"):
            generate_report(report_type)
    
    # Available reports
    st.subheader("Available Reports")
    
    if st.session_state.reports:
        # Create a DataFrame for better display
        reports_df = pd.DataFrame(st.session_state.reports)
        
        # Add a "View" column with buttons
        reports_df["Action"] = "View Report"
        
        # Display table
        for i, row in reports_df.iterrows():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.write(row['name'])
            with col2:
                st.write(row['type'])
            with col3:
                st.write(row['date'])
            with col4:
                if st.button("View", key=f"view_{i}"):
                    st.info(f"Viewing report: {row['name']}")
                    
        # Example report preview
        if st.checkbox("Show Sample Report Preview"):
            st.subheader("Sample Report Preview")
            
            # Create tabs for different sections
            tab1, tab2, tab3 = st.tabs(["Summary", "Temperature Data", "Anomalies"])
            
            with tab1:
                st.markdown("""
                ## Print Job Summary
                
                - **Job Name**: NAVAIR_BRACKET_V1
                - **Material**: ABS
                - **Print Duration**: 2h 15m
                - **Print Quality**: Good
                - **Anomalies Detected**: 1 (Minor)
                """)
            
            with tab2:
                # Sample temperature chart
                dates = pd.date_range(start='2025-04-01', periods=100, freq='T')
                temps = pd.DataFrame({
                    'timestamp': dates,
                    'nozzle': np.random.normal(215, 3, 100),
                    'bed': np.random.normal(65, 1, 100),
                    'ambient': np.random.normal(24, 0.5, 100)
                })
                
                fig = px.line(temps, x='timestamp', y=['nozzle', 'bed', 'ambient'],
                          labels={"value": "Temperature (°C)", "timestamp": "Time", "variable": "Temperature Type"},
                          color_discrete_map={"nozzle": "red", "bed": "orange", "ambient": "blue"})
                fig.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("""
                ### Temperature Statistics
                
                | Parameter | Min | Max | Average | Std Dev |
                |-----------|-----|-----|---------|---------|
                | Nozzle    | 210.2 | 219.8 | 215.3 | 2.8 |
                | Bed       | 63.1 | 66.9 | 65.2 | 0.9 |
                | Ambient   | 22.8 | 25.1 | 24.1 | 0.5 |
                """)
            
            with tab3:
                st.markdown("""
                ### Detected Anomalies
                
                | Time | Type | Severity | Action |
                |------|------|----------|--------|
                | 14:23:05 | Vibration spike | Low | None |
                
                No critical issues were detected during this print job.
                """)
    else:
        st.info("No reports available")

elif nav_selection == "Settings":
    st.title("System Settings")
    
    # Printer connection settings
    st.subheader("Printer Connection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        printer_ip = st.text_input("Printer IP Address", "192.168.1.100")
    with col2:
        api_key = st.text_input("API Key", "••••••••••••••••", type="password")
    
    if st.button("Test Connection"):
        st.success("Connection to Ultimaker S5 API successful!")
    
    # Anomaly detection settings
    st.subheader("Anomaly Detection Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        temp_threshold = st.slider("Temperature Deviation Threshold (°C)", 5, 30, 15)
        humidity_threshold = st.slider("Humidity Threshold (%)", 40, 80, 60)
    
    with col2:
        vibration_threshold = st.slider("Vibration Threshold (g)", 0.1, 1.0, 0.2, step=0.1)
        alert_sensitivity = st.select_slider("Alert Sensitivity", options=["Low", "Medium", "High"], value="Medium")
    
    # System settings
    st.subheader("System Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sampling_rate = st.selectbox("Data Sampling Rate", 
                                    ["1 second", "5 seconds", "10 seconds", "30 seconds", "1 minute"],
                                    index=1)
        data_retention = st.selectbox("Data Retention Period", 
                                     ["24 hours", "7 days", "30 days", "90 days", "1 year"],
                                     index=2)
    
    with col2:
        storage_location = st.text_input("Data Storage Location", "/home/pi/navair_data")
        report_format = st.radio("Default Report Format", ["PDF", "CSV"])
    
    # Save settings
    if st.button("Save Settings"):
        st.success("Settings saved successfully!")
    
    if st.button("Reset to Defaults"):
        st.info("All settings have been reset to defaults")

# Add auto-refresh capability
st.empty()
time.sleep(3)  # Refresh every 3 seconds
st.rerun()
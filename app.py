import streamlit as st
import pandas as pd
import psycopg2
import time
import os

# 1. Page Configuration
st.set_page_config(page_title="Eagle Vision Dashboard", layout="wide")
st.title("🏗️ Construction Equipment Utilization Dashboard")

# 2. Database Connection Function
def get_data():
    try:
        conn = psycopg2.connect("host=db dbname=equipment_db user=user password=pass")
        df = pd.read_sql("SELECT * FROM equipment_logs ORDER BY id DESC LIMIT 10", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame() 

# 3. Layout Setup
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Live Processed Feed 🔴")
    # Placeholder for the image
    video_frame = st.empty()

with col2:
    st.subheader("Real-time Analytics")
    # Placeholders for metrics to prevent shifting
    state_metric = st.empty()
    activity_metric = st.empty()
    util_metric = st.empty()
    st.write("---")
    log_table = st.empty()

# 4. Shared Data Path
frame_path = '/app/shared/latest_frame.jpg'

# 5. Optimized Update Loop
while True:
    # A. Update Video Frame
    if os.path.exists(frame_path):
        try:
            # We use the placeholder to update ONLY the image
            video_frame.image(frame_path, use_container_width=True)
        except Exception:
            pass

    # B. Update Metrics & Table
    df = get_data()
    if not df.empty:
        latest = df.iloc[0]
        # Update each metric in its specific placeholder
        state_metric.metric("Current State", latest['state'])
        activity_metric.metric("Current Activity", latest['activity'])
        util_metric.metric("Utilization Score", f"{latest['utilization_percent']}%")
        # Update the table
        log_table.dataframe(df[['timestamp_str', 'state', 'activity']], use_container_width=True)
    else:
        # If no data, show a quiet message in the log table area
        log_table.info("Waiting for database entries...")

    # C. Control the speed (Crucial for stability)
    # 0.2s is a sweet spot for CPU-based processing
    time.sleep(0.2) 
    
    # REMOVED st.rerun() to stop the flickering
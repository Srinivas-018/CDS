# detector.py

import pandas as pd
import numpy as np

def analyze_file(filepath):
    # Load the CSV file and ensure timestamp is a datetime object
    df = pd.read_csv(filepath)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    expected_cols = {'user_id', 'timestamp', 'event_type', 'tab_switches', 'idle_time'}
    if not expected_cols.issubset(set(df.columns)):
        return {"error": "Missing required columns in uploaded CSV."}

    # --- NEW: Find start and end times for each user ---
    start_times = df[df['event_type'] == 'start_test'].groupby('user_id')['timestamp'].min().rename('start_time')
    end_times = df[df['event_type'] == 'end_test'].groupby('user_id')['timestamp'].min().rename('end_time')

    # Group by user for main behavior stats
    user_stats = df.groupby('user_id').agg({
        'tab_switches': 'max',
        'idle_time': ['mean', 'max'],
        'event_type': 'count'
    }).reset_index()

    user_stats.columns = ['user_id', 'total_tab_switches', 'avg_idle_time', 'max_idle_time', 'total_events']
    
    # --- NEW: Merge times into the main stats dataframe ---
    user_stats = pd.merge(user_stats, start_times, on='user_id', how='left')
    user_stats = pd.merge(user_stats, end_times, on='user_id', how='left')
    
    # Format and clean up data for display
    user_stats['avg_idle_time'] = user_stats['avg_idle_time'].round(2)
    # Format time columns for better display in the table, handle missing times
    user_stats['start_time'] = user_stats['start_time'].dt.strftime('%H:%M:%S').fillna('N/A')
    user_stats['end_time'] = user_stats['end_time'].dt.strftime('%H:%M:%S').fillna('N/A')

    # Calculate suspicion score
    def score(row):
        score = 0
        if row['total_tab_switches'] > 5: score += 3
        if row['avg_idle_time'] > 20: score += 2
        if row['max_idle_time'] > 60: score += 2
        if row['total_events'] < 10: score += 1
        return score
    user_stats['suspicion_score'] = user_stats.apply(score, axis=1)

    # Define risk level
    def risk_level(score):
        if score >= 6: return 'High'
        elif score >= 3: return 'Medium'
        else: return 'Low'
    user_stats['risk_level'] = user_stats['suspicion_score'].apply(risk_level)

    # Calculate risk level percentages for the bar chart
    risk_percentages = user_stats['risk_level'].value_counts(normalize=True).mul(100).round(1).to_dict()
    chart_data = {
        'labels': ['High', 'Medium', 'Low'],
        'data': [risk_percentages.get('High', 0), risk_percentages.get('Medium', 0), risk_percentages.get('Low', 0)]
    }

    return {
        'report_df': user_stats,
        'chart_data': chart_data
    }
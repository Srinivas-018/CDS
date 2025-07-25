import pandas as pd
import numpy as np

def analyze_file(filepath):
    # Load the CSV file
    df = pd.read_csv(filepath)

    # Assumptions:
    # Your log should include at least: ['user_id', 'timestamp', 'event_type', 'tab_switches', 'idle_time']
    # Add mock handling for missing columns
    expected_cols = {'user_id', 'timestamp', 'event_type', 'tab_switches', 'idle_time'}
    if not expected_cols.issubset(set(df.columns)):
        return pd.DataFrame([{"Error": "Missing required columns in uploaded CSV."}])

    # Step 1: Preprocess timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.sort_values(by=['user_id', 'timestamp'], inplace=True)

    # Step 2: Group by user for behavior stats
    user_stats = df.groupby('user_id').agg({
        'tab_switches': 'sum',
        'idle_time': ['mean', 'max'],
        'event_type': 'count'
    }).reset_index()

    # Flatten column names
    user_stats.columns = ['user_id', 'total_tab_switches', 'avg_idle_time', 'max_idle_time', 'total_events']

    # Step 3: Calculate a simple cheating suspicion score
    def score(row):
        score = 0
        if row['total_tab_switches'] > 5:
            score += 3
        if row['avg_idle_time'] > 20:
            score += 2
        if row['max_idle_time'] > 60:
            score += 2
        if row['total_events'] < 10:
            score += 1
        return score

    user_stats['suspicion_score'] = user_stats.apply(score, axis=1)

    # Step 4: Add risk level
    def risk_level(score):
        if score >= 6:
            return 'High'
        elif score >= 3:
            return 'Medium'
        else:
            return 'Low'

    user_stats['risk_level'] = user_stats['suspicion_score'].apply(risk_level)

    return user_stats

# app.py

from flask import Flask, render_template, request, redirect, url_for, flash
import os
import pandas as pd
from analysis.detector import analyze_file

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = 'supersecretkey'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and file.filename.endswith('.csv'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        analysis_results = analyze_file(filepath)

        if 'error' in analysis_results:
            flash(analysis_results['error'])
            return redirect(url_for('index'))
            
        report_df = analysis_results['report_df']
        chart_data = analysis_results['chart_data']
        
        # Convert dataframe to a list of dictionaries to pass to the template
        report_list = report_df.to_dict(orient='records')

        return render_template(
            'reports.html',
            report=report_list, # Pass the list of dicts
            chart_data=chart_data,
            filename=file.filename # Pass the filename for building links
        )
    else:
        flash('Please upload a valid .csv file.')
        return redirect(url_for('index'))

# --- NEW ROUTE FOR USER DETAIL VIEW ---
@app.route('/user/<filename>/<user_id>')
def user_details(filename, user_id):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        df = pd.read_csv(filepath)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        user_df = df[df['user_id'] == user_id]

        if user_df.empty:
            flash(f'User {user_id} not found in the file.')
            return redirect(url_for('index'))

        # --- CORRECTED: Filter out start/end test for the pie chart ---
        events_for_pie = user_df[~user_df['event_type'].isin(['start_test', 'end_test'])]
        event_counts = events_for_pie['event_type'].value_counts()
        
        pie_chart_data = {
            'labels': event_counts.index.tolist(),
            'data': [int(count) for count in event_counts.values]
        }
        
        # Keep the logic to display start/end times on the page
        start_time_row = user_df[user_df['event_type'] == 'start_test']['timestamp']
        end_time_row = user_df[user_df['event_type'] == 'end_test']['timestamp']
        start_time = start_time_row.iloc[0].strftime('%Y-%m-%d %H:%M:%S') if not start_time_row.empty else 'Not found'
        end_time = end_time_row.iloc[0].strftime('%Y-%m-%d %H:%M:%S') if not end_time_row.empty else 'Not found'

        return render_template(
            'user_detail.html',
            user_id=user_id,
            chart_data=pie_chart_data,
            start_time=start_time,
            end_time=end_time
        )
    except FileNotFoundError:
        flash('Original data file not found. Please re-upload.')
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
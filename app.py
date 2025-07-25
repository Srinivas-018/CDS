from flask import Flask, render_template, request, redirect, url_for
import os
import pandas as pd

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file part'
    
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    # Import the analysis logic here later
    from analysis.detector import analyze_file
    report_df = analyze_file(filepath)

    # Save result to pass to template
    return render_template('reports.html', report=report_df)

if __name__ == '__main__':
    app.run(debug=True)

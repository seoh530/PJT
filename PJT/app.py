import plotly
import json
import os
from flask import Flask, request, render_template, redirect, url_for
from data_parser import parse_txt_file, records_to_dataframe, split_by_device_type
from scatter_plotter import create_animated_3d_scatter

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def upload_file():
    return render_template('upload.html')

@app.route('/uploader', methods=['GET', 'POST'])
def uploader_file():
    if request.method == 'POST':
        f = request.files['file']
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f.filename)
        f.save(file_path)
        
        records = parse_txt_file(file_path)
        df = records_to_dataframe(records)

        hmd_df, hand_df = split_by_device_type(df)

        fig = None
        time_stamps = []

        if not hmd_df.empty or not hand_df.empty:
            fig, time_stamps = create_animated_3d_scatter(hmd_df, hand_df)

        min_timestamp = df['recordTimeStamp'].min()
        max_timestamp = df['recordTimeStamp'].max()

        fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return render_template('plot.html', fig=fig_json, min_timestamp=min_timestamp, max_timestamp=max_timestamp, time_stamps=time_stamps)

if __name__ == '__main__':
    app.run(debug=True)

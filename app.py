import os
from flask import Flask, request, render_template, redirect, url_for
import pandas as pd
import plotly.express as px

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def dfs(lines, depth=0):
    block = {}
    while True:
        try:
            line = next(lines).strip()
        except StopIteration:
            break

        if line.startswith("recordTimeStamp"):
            block['recordTimeStamp'] = int(line.split(':')[1].strip())
        elif line.startswith("deviceType"):
            block['deviceType'] = line.split(':')[1].strip()
        elif line.startswith("hand:"):
            block['hand'] = line.split(':')[1].strip()
        elif line.startswith("key:"):
            key = int(line.split(':')[1].strip())
            block['key'] = key
        elif line.startswith("orientation") or line.startswith("position"):
            field = line.split()[0]
            nested_block = dfs(lines, depth + 1)
            block[field] = nested_block
        elif line == "}":
            if depth == 0:
                break
            return block
    return block

def parse_record_block(block, prev_position, prev_orientation):
    lines = iter(block.strip().split('\n'))
    record = dfs(lines)
    
    if 'position' not in record:
        record['position'] = prev_position.copy()
    if 'orientation' not in record:
        record['orientation'] = prev_orientation.copy()

    return record

def parse_txt_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = file.read()
    blocks = data.split('records {')[1:]
    blocks = [block.rsplit('}', 1)[0] for block in blocks]
    records = []
    prev_position = {'x': 0, 'y': 0, 'z': 0}
    prev_orientation = {'w': 0, 'x': 0, 'y': 0, 'z': 0}
    for block in blocks:
        record = parse_record_block(block, prev_position, prev_orientation)
        if 'deviceType' in record:
            records.append(record)
            prev_position = record['position']
            prev_orientation = record['orientation']
    return records

def records_to_dataframe(records):
    data = []
    for record in records:
        position = record.get('position', {})
        orientation = record.get('orientation', {})
        data.append({
            'recordTimeStamp': record['recordTimeStamp'],
            'deviceType': record.get('deviceType', None),
            'hand': record.get('hand', None),
            'x_pos': position.get('x', 0),
            'y_pos': position.get('y', 0),
            'z_pos': position.get('z', 0),  # Forward is positive z
            'w_ori': orientation.get('w', 0),
            'x_ori': orientation.get('x', 0),
            'y_ori': orientation.get('y', 0),
            'z_ori': orientation.get('z', 0)
        })
    df = pd.DataFrame(data)
    return df

def split_by_device_type(df):
    if 'deviceType' in df.columns:
        hmd_df = df[df['deviceType'] == 'DEVICE_TYPE_HMD'].copy()
        hand_df = df[df['deviceType'] == 'DEVICE_TYPE_HAND_TRACKING'].copy()
        return hmd_df, hand_df
    else:
        return pd.DataFrame(), pd.DataFrame()

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
        df['x_pos'], df['y_pos'], df['z_pos'] = df['z_pos'], df['x_pos'], df['y_pos']  # 축을 변경

        hmd_df, hand_df = split_by_device_type(df)

        fig_hmd = None
        fig_hand_right = None
        fig_hand_left = None

        if not hmd_df.empty:
            fig_hmd = px.scatter_3d(hmd_df, x='x_pos', y='y_pos', z='z_pos', color='recordTimeStamp', title='HMD Device Position Over Time')
            fig_hmd.update_layout(scene=dict(
                xaxis=dict(title='X (right)'),
                yaxis=dict(title='Y (up)'),
                zaxis=dict(title='Z (forward)')
            ), height=800)

        if not hand_df.empty:
            right_hand_df = hand_df[hand_df['hand'] == 'HAND_RIGHT']
            left_hand_df = hand_df[hand_df['hand'] == 'HAND_LEFT']

            if not right_hand_df.empty:
                fig_hand_right = px.scatter_3d(right_hand_df, x='x_pos', y='y_pos', z='z_pos', color='recordTimeStamp', title='Right Hand Position Over Time (Key=1)')
                fig_hand_right.update_layout(scene=dict(
                    xaxis=dict(title='X (right)'),
                    yaxis=dict(title='Y (up)'),
                    zaxis=dict(title='Z (forward)')
                ), height=800)

            if not left_hand_df.empty:
                fig_hand_left = px.scatter_3d(left_hand_df, x='x_pos', y='y_pos', z='z_pos', color='recordTimeStamp', title='Left Hand Position Over Time (Key=1)')
                fig_hand_left.update_layout(scene=dict(
                    xaxis=dict(title='X (right)'),
                    yaxis=dict(title='Y (up)'),
                    zaxis=dict(title='Z (forward)')
                ), height=800)

        return render_template('plot.html', fig_hmd=fig_hmd.to_html(full_html=False) if fig_hmd else None,
                                          fig_hand_right=fig_hand_right.to_html(full_html=False) if fig_hand_right else None,
                                          fig_hand_left=fig_hand_left.to_html(full_html=False) if fig_hand_left else None)

if __name__ == '__main__':
    app.run(debug=True)

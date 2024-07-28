import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def parse_record_block(block, prev_position, prev_orientation):
    record = {}
    record['recordTimeStamp'] = 0
    lines = iter(block.strip().split('\n'))
    hand = None
    key = None
    position = prev_position.copy()
    orientation = prev_orientation.copy()
    inside_pose = False
    for line in lines:
        line = line.strip()

        # if (len(line.split(':')) > 0):
        #     print(line.split(':')[1].strip())

        if line.startswith("recordTimestamp"):
            record['recordTimeStamp'] = line.split(':')[1].strip()
  
        elif line.startswith("deviceType"):
            record['deviceType'] = line.split(':')[1].strip()

        elif "pose" in line or "handPose" in line:
            inside_pose = True
            handPose_block = line.startswith("handPose")
            while inside_pose:
                line = next(lines).strip()
                if handPose_block and line.startswith("hand:"):
                    hand = line.split(':')[1].strip()
                elif handPose_block and line.startswith("key:"):
                    key = int(line.split(':')[1].strip())

                elif line.startswith("orientation"):
                    orientation = prev_orientation.copy()
                    while "}" not in line:
                        line = next(lines).strip()
                        if "w" in line or "x" in line or "y" in line or "z" in line:
                            axis, value = line.split(':')
                            orientation[axis.strip()] = float(value.strip())
                elif line.startswith("position") and (not handPose_block or (handPose_block and key == 1)):
                    position = prev_position.copy()
                    while "}" not in line:
                        line = next(lines).strip()
                        if "x" in line or "y" in line or "z" in line:
                            axis, value = line.split(':')
                            position[axis.strip()] = float(value.strip())
                    record['position'] = position
                    record['orientation'] = orientation
                    if handPose_block:
                        record['hand'] = hand
                    break
            inside_pose = False
    record['position'] = position
    record['orientation'] = orientation
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

# file_path = 'test_data.txt'
# records = parse_txt_file(file_path)

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
            'z_pos': position.get('z', 0),
            'w_ori': orientation.get('w', 0),
            'x_ori': orientation.get('x', 0),
            'y_ori': orientation.get('y', 0),
            'z_ori': orientation.get('z', 0)
        })
    df = pd.DataFrame(data)
    return df

# df = records_to_dataframe(records)


def split_by_device_type(df):
    if 'deviceType' in df.columns:
        hmd_df = df[df['deviceType'] == 'DEVICE_TYPE_HMD'].copy()
        hand_df = df[df['deviceType'] == 'DEVICE_TYPE_HAND_TRACKING'].copy()
        return hmd_df, hand_df
    else:
        return pd.DataFrame(), pd.DataFrame()

# hmd_df, hand_df = split_by_device_type(df)


# # 텍스트 파일 파싱 및 DataFrame 변환
# file_path = 'test_data.txt'
# records = parse_txt_file(file_path)
# df = records_to_dataframe(records)
# print("====================")
# print(df[500:520])  # DataFrame의 첫 몇 줄 출력

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

        fig_hmd = None
        fig_hand_right = None
        fig_hand_left = None

        if not hmd_df.empty:
            fig_hmd = create_animated_3d_scatter(hmd_df)
            
        if not hand_df.empty:
            right_hand_df = hand_df[hand_df['hand'] == 'HAND_RIGHT']
            left_hand_df = hand_df[hand_df['hand'] == 'HAND_LEFT']

            if not right_hand_df.empty:
                fig_hand_right = create_animated_3d_scatter(right_hand_df)

            if not left_hand_df.empty:
                fig_hand_left = create_animated_3d_scatter(left_hand_df)

        return render_template('plot.html', fig_hmd=fig_hmd.to_html(full_html=False) if fig_hmd else None,
                                          fig_hand_right=fig_hand_right.to_html(full_html=False) if fig_hand_right else None,
                                          fig_hand_left=fig_hand_left.to_html(full_html=False) if fig_hand_left else None)

def create_animated_3d_scatter(df):
    df = df.sort_values('recordTimeStamp')
    fig = px.scatter_3d(df, x='z_pos', y='x_pos', z='y_pos', range_x=[-1.0,1.0], range_y=[-1.0,1.0], range_z=[-1.0,2.0], animation_frame='recordTimeStamp', title="")
    fig.update_layout(scene=dict(
        xaxis=dict(title='Z'),
        yaxis=dict(title='X'),
        zaxis=dict(title='Y')
    ), height=800)
    return fig

if __name__ == '__main__':
    app.run(debug=True)
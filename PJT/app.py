import json
import os
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
import plotly.graph_objs as go
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

def split_by_device_type(df):
    if 'deviceType' in df.columns:
        hmd_df = df[df['deviceType'] == 'DEVICE_TYPE_HMD'].copy()
        hand_df = df[df['deviceType'] == 'DEVICE_TYPE_HAND_TRACKING'].copy()
        return hmd_df, hand_df
    else:
        return pd.DataFrame(), pd.DataFrame()


def create_animated_3d_scatter(hmd_df, hand_df):
    frames = []
    time_stamps = sorted(hand_df['recordTimeStamp'].unique())

    all_hmd_trace = go.Scatter3d(
        x=hmd_df['z_pos'],
        y=hmd_df['x_pos'],
        z=hmd_df['y_pos'],
        mode='lines',
        marker=dict(size=5, color='blue'),
        name='HMD (All Time)'
    )
    
    all_right_hand_trace = go.Scatter3d(
        x=hand_df[hand_df['hand'] == 'HAND_RIGHT']['z_pos'],
        y=hand_df[hand_df['hand'] == 'HAND_RIGHT']['x_pos'],
        z=hand_df[hand_df['hand'] == 'HAND_RIGHT']['y_pos'],
        mode='lines',
        marker=dict(size=5, color='red'),
        name='Right Hand (All Time)'
    )
    
    all_left_hand_trace = go.Scatter3d(
        x=hand_df[hand_df['hand'] == 'HAND_LEFT']['z_pos'],
        y=hand_df[hand_df['hand'] == 'HAND_LEFT']['x_pos'],
        z=hand_df[hand_df['hand'] == 'HAND_LEFT']['y_pos'],
        mode='lines',
        marker=dict(size=5, color='green'),
        name='Left Hand (All Time)'
    )

    for timestamp in time_stamps:
        frame_data = []
        
        hmd_data = hmd_df[hmd_df['recordTimeStamp'] == timestamp]
        if not hmd_data.empty:
            frame_data.append(go.Scatter3d(
                x=hmd_data['z_pos'],
                y=hmd_data['x_pos'],
                z=hmd_data['y_pos'],
                mode='markers',
                marker=dict(size=5, color='blue'),
                name='HMD'
            ))
        
        right_hand_data = hand_df[(hand_df['recordTimeStamp'] == timestamp) & (hand_df['hand'] == 'HAND_RIGHT')]
        if not right_hand_data.empty:
            frame_data.append(go.Scatter3d(
                x=right_hand_data['z_pos'],
                y=right_hand_data['x_pos'],
                z=right_hand_data['y_pos'],
                mode='markers',
                marker=dict(size=5, color='red'),
                name='Right Hand'
            ))
        
        left_hand_data = hand_df[(hand_df['recordTimeStamp'] == timestamp) & (hand_df['hand'] == 'HAND_LEFT')]
        if not left_hand_data.empty:
            frame_data.append(go.Scatter3d(
                x=left_hand_data['z_pos'],
                y=left_hand_data['x_pos'],
                z=left_hand_data['y_pos'],
                mode='markers',
                marker=dict(size=5, color='green'),
                name='Left Hand'
            ))
        
        frames.append(go.Frame(data=frame_data, name=str(timestamp)))
    
    sliders = [dict(
        steps=[dict(method='animate', args=[[str(ts)], dict(mode='immediate', frame=dict(duration=300, redraw=True), transition=dict(duration=0))], label=str(ts)) for ts in time_stamps],
        transition=dict(duration=0),
        x=0,
        y=0,
        currentvalue=dict(font=dict(size=12), prefix='Time: ', visible=True, xanchor='center'),
        len=1.0
    )]
    
    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=hmd_df['z_pos'], y=hmd_df['x_pos'], z=hmd_df['y_pos'], 
                mode='markers', marker=dict(size=5, color='blue'), name='HMD'
            ),
            go.Scatter3d(
                x=hand_df[hand_df['hand'] == 'HAND_RIGHT']['z_pos'], y=hand_df[hand_df['hand'] == 'HAND_RIGHT']['x_pos'], 
                z=hand_df[hand_df['hand'] == 'HAND_RIGHT']['y_pos'], mode='markers', marker=dict(size=5, color='red'), name='Right Hand'
            ),
            go.Scatter3d(
                x=hand_df[hand_df['hand'] == 'HAND_LEFT']['z_pos'], y=hand_df[hand_df['hand'] == 'HAND_LEFT']['x_pos'], 
                z=hand_df[hand_df['hand'] == 'HAND_LEFT']['y_pos'], mode='markers', marker=dict(size=5, color='green'), name='Left Hand'
            )
        ],
        layout=go.Layout(
            scene=dict(
                xaxis=dict(title='Z', range=[-1.0, 1.0], tickvals=[-1, -0.5, 0, 0.5, 1], titlefont=dict(size=14, color='black', family='Arial, sans-serif', weight='bold'), tickfont=dict(size=12, color='black', family='Arial, sans-serif', weight='bold')),
                yaxis=dict(title='X', range=[-1.0, 1.0], tickvals=[-1, -0.5, 0, 0.5, 1], titlefont=dict(size=14, color='black', family='Arial, sans-serif', weight='bold'), tickfont=dict(size=12, color='black', family='Arial, sans-serif', weight='bold')),
                zaxis=dict(title='Y', range=[-1.0, 2.0], tickvals=[-1, 0, 1, 2], titlefont=dict(size=14, color='black', family='Arial, sans-serif', weight='bold'), tickfont=dict(size=12, color='black', family='Arial, sans-serif', weight='bold'))
            ),
            height=700,
            sliders=sliders,
            legend=dict(
                font=dict(
                    size=14
                ),
                itemsizing='constant'
            ),
            updatemenus=[
                dict(
                    type="buttons",
                    showactive=True,
                    buttons=[
                        dict(label="Animated Points",
                             method="update",
                             args=[{"visible": [True, True, True, False, False, False]}]),
                        dict(label="All Time Lines",
                             method="update",
                             args=[{"visible": [False, False, False, True, True, True]}])
                    ],
                    pad=dict(r=10, t=10),
                    direction="left",
                    x=0.0,
                    xanchor="left",
                    y=1.15,
                    yanchor="top"
                )
            ]
        ),
        frames=frames
    )
    
    fig.add_trace(all_hmd_trace)
    fig.add_trace(all_right_hand_trace)
    fig.add_trace(all_left_hand_trace)

    return fig, time_stamps


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
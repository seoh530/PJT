import plotly.graph_objects as go

def create_animated_3d_scatter(hmd_df, hand_df):
    frames = []
    time_stamps = sorted(hand_df['recordTimeStamp'].unique())

    all_hmd_trace = go.Scatter3d(
        x=hmd_df['z_pos'],
        y=hmd_df['x_pos'],
        z=hmd_df['y_pos'],
        mode='lines',
        marker=dict(size=5, color='blue'),
        name='HMD (All Time)',
        visible=True
    )
    
    all_right_hand_trace = go.Scatter3d(
        x=hand_df[hand_df['hand'] == 'HAND_RIGHT']['z_pos'],
        y=hand_df[hand_df['hand'] == 'HAND_RIGHT']['x_pos'],
        z=hand_df[hand_df['hand'] == 'HAND_RIGHT']['y_pos'],
        mode='lines',
        marker=dict(size=5, color='red'),
        name='Right Hand (All Time)',
        visible=True
    )
    
    all_left_hand_trace = go.Scatter3d(
        x=hand_df[hand_df['hand'] == 'HAND_LEFT']['z_pos'],
        y=hand_df[hand_df['hand'] == 'HAND_LEFT']['x_pos'],
        z=hand_df[hand_df['hand'] == 'HAND_LEFT']['y_pos'],
        mode='lines',
        marker=dict(size=5, color='green'),
        name='Left Hand (All Time)',
        visible=True
    )

    previous_hmd = {'x_pos': None, 'y_pos': None, 'z_pos': None}
    previous_right_hand = {'x_pos': None, 'y_pos': None, 'z_pos': None}
    previous_left_hand = {'x_pos': None, 'y_pos': None, 'z_pos': None}

    for timestamp in time_stamps:
        frame_data = []

        hmd_data = hmd_df[hmd_df['recordTimeStamp'] == timestamp]
        right_hand_data = hand_df[(hand_df['recordTimeStamp'] == timestamp) & (hand_df['hand'] == 'HAND_RIGHT')]
        left_hand_data = hand_df[(hand_df['recordTimeStamp'] == timestamp) & (hand_df['hand'] == 'HAND_LEFT')]

        if not hmd_data.empty:
            previous_hmd = {
                'x_pos': hmd_data['x_pos'].values[0],
                'y_pos': hmd_data['y_pos'].values[0],
                'z_pos': hmd_data['z_pos'].values[0]
            }
            frame_data.append(go.Scatter3d(
                x=[previous_hmd['z_pos']],
                y=[previous_hmd['x_pos']],
                z=[previous_hmd['y_pos']],
                mode='markers',
                marker=dict(size=5, color='blue'),
                name='HMD'
            ))
        else:
            if previous_hmd['x_pos'] is not None:
                frame_data.append(go.Scatter3d(
                    x=[previous_hmd['z_pos']],
                    y=[previous_hmd['x_pos']],
                    z=[previous_hmd['y_pos']],
                    mode='markers',
                    marker=dict(size=5, color='blue'),
                    name='HMD'
                ))

        if not right_hand_data.empty:
            previous_right_hand = {
                'x_pos': right_hand_data['x_pos'].values[0],
                'y_pos': right_hand_data['y_pos'].values[0],
                'z_pos': right_hand_data['z_pos'].values[0]
            }
            frame_data.append(go.Scatter3d(
                x=[previous_right_hand['z_pos']],
                y=[previous_right_hand['x_pos']],
                z=[previous_right_hand['y_pos']],
                mode='markers',
                marker=dict(size=5, color='red'),
                name='Right Hand'
            ))
        else:
            if previous_right_hand['x_pos'] is not None:
                frame_data.append(go.Scatter3d(
                    x=[previous_right_hand['z_pos']],
                    y=[previous_right_hand['x_pos']],
                    z=[previous_right_hand['y_pos']],
                    mode='markers',
                    marker=dict(size=5, color='red'),
                    name='Right Hand'
                ))

        if not left_hand_data.empty:
            previous_left_hand = {
                'x_pos': left_hand_data['x_pos'].values[0],
                'y_pos': left_hand_data['y_pos'].values[0],
                'z_pos': left_hand_data['z_pos'].values[0]
            }
            frame_data.append(go.Scatter3d(
                x=[previous_left_hand['z_pos']],
                y=[previous_left_hand['x_pos']],
                z=[previous_left_hand['y_pos']],
                mode='markers',
                marker=dict(size=5, color='green'),
                name='Left Hand'
            ))
        else:
            if previous_left_hand['x_pos'] is not None:
                frame_data.append(go.Scatter3d(
                    x=[previous_left_hand['z_pos']],
                    y=[previous_left_hand['x_pos']],
                    z=[previous_left_hand['y_pos']],
                    mode='markers',
                    marker=dict(size=5, color='green'),
                    name='Left Hand'
                ))

        frames.append(go.Frame(
            data=frame_data,
            name=str(timestamp),
            layout=dict(
                scene=dict(
                    xaxis=dict(range=[-1.0, 2.0]),
                    yaxis=dict(range=[-1.0, 2.0]),
                    zaxis=dict(range=[-1.0, 2.0])
                )
            )
        ))

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
                x=hmd_df['z_pos'], 
                y=hmd_df['x_pos'], 
                z=hmd_df['y_pos'],
                mode='markers', marker=dict(size=5, color='blue'), name='HMD'
            ),
            go.Scatter3d(
                x=hand_df[hand_df['hand'] == 'HAND_RIGHT']['z_pos'],
                y=hand_df[hand_df['hand'] == 'HAND_RIGHT']['x_pos'],
                z=hand_df[hand_df['hand'] == 'HAND_RIGHT']['y_pos'], 
                mode='markers', marker=dict(size=5, color='red'), name='Right Hand'
            ),
            go.Scatter3d(
                x=hand_df[hand_df['hand'] == 'HAND_LEFT']['z_pos'], 
                y=hand_df[hand_df['hand'] == 'HAND_LEFT']['x_pos'],
                z=hand_df[hand_df['hand'] == 'HAND_LEFT']['y_pos'], 
                mode='markers', marker=dict(size=5, color='green'), name='Left Hand'
            ),
            all_hmd_trace,
            all_right_hand_trace,
            all_left_hand_trace
        ],
        layout=go.Layout(
            scene=dict(
                xaxis=dict(title='Z', range=[-1.0, 2.0], tickvals=[-1, -0.5, 0, 0.5, 1, 1.5, 2], 
                           titlefont=dict(size=14, color='black', family='Arial, sans-serif', weight='bold'), 
                           tickfont=dict(size=12, color='black', family='Arial, sans-serif', weight='bold')),
                yaxis=dict(title='X', range=[-1.0, 2.0], tickvals=[-1, -0.5, 0, 0.5, 1, 1.5, 2], 
                           titlefont=dict(size=14, color='black', family='Arial, sans-serif', weight='bold'), 
                           tickfont=dict(size=12, color='black', family='Arial, sans-serif', weight='bold')),
                zaxis=dict(title='Y', range=[-1.0, 2.0], tickvals=[-1, 0, 1, 2], 
                           titlefont=dict(size=14, color='black', family='Arial, sans-serif', weight='bold'), 
                           tickfont=dict(size=12, color='black', family='Arial, sans-serif', weight='bold'))
            ),
            height=900,
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
                    direction="down",
                    buttons=[
                        dict(label="Animated Points",
                             method="update",
                             args=[{"visible": [True, True, True, False, False, False]}, 
                                   {"scene": dict(xaxis=dict(range=[-1.0, 2.0]), yaxis=dict(range=[-1.0, 2.0]), zaxis=dict(range=[-1.0, 2.0]))}]),
                        dict(label="All Time Lines",
                             method="update",
                             args=[{"visible": [False, False, False, True, True, True]}, 
                                   {"scene": dict(xaxis=dict(range=[-1.0, 2.0]), yaxis=dict(range=[-1.0, 2.0]), zaxis=dict(range=[-1.0, 2.0]))}])
                    ],
                    pad=dict(r=10, t=10),
                    x=1.15,
                    xanchor="right",
                    y=0.5,
                    yanchor="middle"
                )
            ]
        ),
        frames=frames
    )
    
    fig.add_trace(all_hmd_trace)
    fig.add_trace(all_right_hand_trace)
    fig.add_trace(all_left_hand_trace)

    return fig, time_stamps

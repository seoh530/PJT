import pandas as pd

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

                    if 'hand' in record:
                        position['y'] += 1.6

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

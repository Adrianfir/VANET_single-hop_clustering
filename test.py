import re
if ":" not in '26320726#2_0':
    match = re.search(r'-?\d+#\d', '26320726#2_0')

    if match:
        lane_id = match.group()
print(lane_id)
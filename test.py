import re
lane_id = "157802105_0"
if ":" in lane_id:
    pass
else:
    pattern = re.compile(f"^(.*?){re.escape('_')}")
    match = pattern.search(lane_id)
    if match:
        lane_id = match.group(1)

print(lane_id)
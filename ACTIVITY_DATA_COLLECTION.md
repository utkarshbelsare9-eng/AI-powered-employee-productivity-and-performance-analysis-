# Activity Data Collection & Analysis

## Collection pipeline

Employee workstation/browser
→ aggregate event counters
→ 60-second activity interval
→ authenticated `/api/activity/agent/ping` or browser `/api/activity/ping`
→ `activity_logs`
→ daily aggregation/timesheet
→ analytics/performance/ML features

## Stored features

- `keyboard_events`: number of keyboard presses in the interval (not the actual keys)
- `mouse_moves`: number of movement events
- `mouse_clicks`: number of clicks
- `scroll_events`: number of scroll events
- `idle_seconds`: inactivity duration within the interval
- `active_application`: process/application name only
- `mouse_active`, `keyboard_active`: derived activity flags
- `source`: browser or desktop_agent

## Analysis-ready metrics

From these interval records the application can derive:
- active computer hours
- keyboard-active hours
- mouse-active hours
- activity density
- interaction rate per active hour
- idle ratio
- application usage distribution
- productive/active/idle timeline

The design deliberately avoids collecting typed text, key identities, clipboard contents, screenshots, or window/document titles.

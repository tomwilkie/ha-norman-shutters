# Norman Shutters for Home Assistant

Custom Home Assistant integration for [Norman PerfectTilt](https://normanusa.com/) motorized plantation shutters, installable via HACS.

## Features

- Automatic hub discovery via Zeroconf (mDNS) — no IP address required in most cases
- One **cover** entity per window with open, close, and tilt control
- One **battery** sensor entity per window
- Local polling every 30 seconds; no cloud dependency

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click the three-dot menu → **Custom repositories**
4. Add `https://github.com/tomwilkie/ha-norman-shutters` with category **Integration**
5. Install **Norman Shutters** and restart Home Assistant

### Manual

Copy `custom_components/norman_shutters/` into your Home Assistant `config/custom_components/` directory and restart.

## Configuration

1. Go to **Settings → Integrations → Add Integration**
2. Search for **Norman Shutters**
3. If your hub is on the local network it will be discovered automatically — confirm to add it
4. If not discovered, enter the hub IP address manually

## Requirements

- Norman PerfectTilt Hub on the local network
- Home Assistant 2023.1 or later
- Python library: [pynormanshutters](https://github.com/tomwilkie/pynormanshutters) (installed automatically)

## Adjusting API key names

The field names used to parse `get_window_info()` responses (e.g. `"mac"`, `"angle"`, `"battery"`) are based on reverse-engineering. If your shutters report incorrect state, run the CLI to inspect the real response:

```sh
cd pynormanshutters
python main.py get_window_info
```

Then update `_parse_window_info` in `coordinator.py` and `current_cover_tilt_position` in `cover.py` to match.

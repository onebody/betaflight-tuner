# Betaflight Tuner Skill

WorkBuddy AI Agent skill for Betaflight flight controller tuning.

## Features

- 🔧 **CLI Serial Mode**: Direct connection to flight controller via USB serial
- 🌐 **Web Ground Station Mode**: Automate Betaflight Configurator web version
- 📊 **Rate Tuning**: Support 4 styles (freestyle, race, smooth, aggressive)
- 🎯 **PID Tuning**: Support 4 presets (5inch, 5inch_race, 3inch, 7inch)
- 📡 **VTX Configuration**: Set band, channel, power
- 📺 **OSD Configuration**: Set units, alarm thresholds
- ⚙️ **ESC Configuration**: DShot settings, RPM filter
- 📦 **Preset Import**: Import .BFL preset files
- 📈 **Blackbox Analysis**: Analyze flight logs (experimental)

## Installation

1. Clone this repository or download the skill package
2. Import into WorkBuddy: `/skill-installer install --path /path/to/betaflight-tuner`
3. Connect flight controller via USB
4. Enter CLI mode in Betaflight Configurator
5. Ask AI: "Help me tune my 5-inch racing drone"

## Requirements

- Python 3.6+
- pyserial (for CLI serial mode): `pip install pyserial`
- playwright (for web ground station mode, optional): `pip install playwright`

## Usage

### CLI Serial Mode

```bash
# Initialize (restore factory settings)
python3 scripts/tune.py --port /dev/cu.usbmodem0x80000001 --action init

# Set Rate (race style)
python3 scripts/tune.py --port /dev/cu.usbmodem0x80000001 --action rate --style race

# Set PID (5-inch preset)
python3 scripts/tune.py --port /dev/cu.usbmodem0x80000001 --action pid --preset 5inch

# Full tuning
python3 scripts/tune.py --port /dev/cu.usbmodem0x80000001 --action all --style race --preset 5inch_race
```

### Web Ground Station Mode

```bash
python3 scripts/groundstation.py --action read --output /tmp/fc_params.json
```

## Project Structure

```
betaflight-tuner/
├── SKILL.md              # Skill definition and usage guide
├── scripts/
│   ├── fc_serial.py     # Serial communication module
│   ├── tune.py          # Main tuning script
│   └── groundstation.py # Web ground station automation
├── references/          # Reference documentation
├── templates/           # Report templates
└── evals/              # Test cases
```

## Safety Warnings

⚠️ **Always backup your configuration before tuning!**

⚠️ **Some settings may cause USB disconnection. Reconnect USB if needed.**

⚠️ **Test motors without props first!**

⚠️ **ESC protocol settings may cause firmware issues. Use with caution.**

## Tested Configurations

- ✅ Betaflight 4.3.0
- ✅ Rate tuning (all styles)
- ✅ PID tuning (all presets)
- ✅ VTX configuration
- ✅ OSD configuration
- ⚠️ ESC configuration (partial, skipped dangerous operations)
- ❌ Blackbox analysis (not tested)
- ❌ Web ground station (not tested)

## Known Issues

1. **Firmware corruption**: Setting `motor_pwm_protocol` may cause USB disconnection
2. **ESC config incomplete**: Skipped `motor_pwm_protocol` setting (risky)
3. **Filter params**: Betaflight 4.x parameter names to be confirmed
4. **Reconnect timeout**: May need to wait 10+ seconds after reboot

## Troubleshooting

### Flight controller not detected

```bash
# Check serial devices
ls -la /dev/cu.* | grep -E "(usbmodem|usbserial)"

# If not detected, reconnect USB and wait 5 seconds
```

### CLI mode not entering

1. Open Betaflight Configurator
2. Connect to flight controller
3. Click "CLI" tab
4. Send `#` command manually to enter CLI mode

### USB disconnected after setting ESC protocol

1. Reconnect USB
2. Wait for system to reload driver (10+ seconds)
3. If still not detected, may need to reflash firmware

## Contributing

Issues and pull requests are welcome!

## License

MIT

## Author

onebody

## Version

v1.0 - 2026-06-21

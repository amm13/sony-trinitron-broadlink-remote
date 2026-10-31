# Sony Trinitron BroadLink Remote

A **visual remote control for classic Sony Trinitron TVs**, using a **BroadLink RM Mini 3** IR blaster on your local network. Python/Tkinter desktop app, primarily for Windows.

This community project includes Sony RM-833-style keys, source selection, an optional configurable **RGB SCART shortcut**, a confirmed-on-some-models Sony service-mode sequence, and user-learned/custom IR commands. **It is not affiliated with Sony or BroadLink.**

![Interface preview](docs/interface-preview.png)

## Quick start

1. Install **Python 3.10+** for Windows, including the `py` launcher.
2. Download and extract the repository.
3. Double-click `launch_remote.bat`. It installs the pinned `broadlink` dependency if needed.
4. Keep your PC and RM Mini 3 on the same LAN. In the BroadLink mobile app, disable **Lock device** if local authentication is blocked.
5. Find/connect to the BroadLink. Test **VOL +** or **MENU** first.

Alternatively:

```powershell
py -m pip install -r requirements.txt
py sony_trinitron_remote.py
```

## Features

- Power, mute, volume, channels, numeric keys, MENU, Display/i+, color buttons.
- **SOURCE / AV** input switching.
- **RGB SCART / RGB-Pi shortcut:** defaults to `TV → SOURCE → SOURCE`, with an editable number of SOURCE presses. This is a macro, *not* a universal direct-input command. Confirm the TV actually displays RGB.
- Configurable VTR/MDP and additional remote keys with manual BroadLink Base64 codes or IR learning.
- Sony BE-3B service-mode access from standby with a confirmation dialog.

## Safety

Service settings can damage TV configuration. Photograph original values before adjusting. Do not run RGB macro from service mode. Avoid unknown TT commands or factory reset codes. Never open a CRT TV to make internal adjustments unless appropriately trained; it may retain dangerous voltages even when unplugged.

## Privacy

The repository does not contain any owner-specific IP address, address, email, credential, device serial number or other local configuration data. Runtime configuration is saved locally to:

```text
%APPDATA%\SonyTrinitronBroadLink\remote_config.json
```

Do not upload that file, learned codes, or private logs.

## Documentation and tests

- [IR code provenance and feature status](docs/IR_CODES.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Security](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

```powershell
py -m unittest discover -s tests -v
```

## Attribution

Licensed under [MIT](LICENSE). IR codes originate from a [Home Assistant community post by amarata](https://community.home-assistant.io/t/tv-sony-trinitron-broadlink-and-base-64-codes-for-remote-control/768889). See [NOTICE](NOTICE.md). Product names and trademarks are used only to identify compatibility.
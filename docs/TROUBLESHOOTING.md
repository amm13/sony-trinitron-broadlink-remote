# Troubleshooting

## BroadLink not found

- Keep the computer and the BroadLink on the same LAN, without wireless client isolation.
- Confirm the BroadLink is powered and connected in the mobile app.
- Check whether the Windows firewall blocks local UDP discovery.

## `Authentication failed`

Disable **Lock device** in the BroadLink mobile app's device settings. The remote can then accept local commands from the Python library.

## TV responds to volume but not Display

Use **Display/i+**, which transmits five frames. Sony television models may require different signals.

## SOURCE works but RGB SCART selects the wrong input

- Make sure the TV is outside service mode (`TT`).
- Press **TV** to begin from a known state.
- Change the number of SOURCE presses in the TV & Inputs tab.
- Verify that the SCART socket actually supports RGB.

## The blaster cannot tell whether the TV is in RGB

This is normal: the BroadLink sends IR but cannot query the selected input from a legacy television.

## The service menu does not appear

Ensure the TV is in standby, not fully powered off. The service macro repeats each key five times. Different Sony chassis can use different sequences.

## A key asks for a Base64 code

That key has no verified built-in IR code. Learn a code from a working remote or assign a previously captured code.

## The app will not open

Run `py --version`; install Python with Tkinter if necessary. Install dependencies using `py -m pip install -r requirements.txt`; execute `py sony_trinitron_remote.py` in PowerShell for diagnostic output.

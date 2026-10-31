# IR codes and compatibility

IR commands are stored as BroadLink Base64 payloads in `CODES` inside `sony_trinitron_remote.py`. A Sony SIRC key often needs multiple frames; this app supports repeat counts from 1 to 8.

| Key group | Implementation | Notes |
| --- | --- | --- |
| Power / TV / volume / menu | Built-in IR captures | Tested with some Sony Trinitrons; behavior may vary |
| Info (Display/i+) | Built-in; sent 5 times | Some Sony receivers require more repeats |
| SOURCE / AV | Built-in capture | Validate input selection on your model |
| RGB SCART shortcut | Macro: TV + SOURCE × N | Default N=2; not a direct RGB command |
| Numeric 0–9 | Built-in IR captures | Check on your model |
| Service controls | Existing captures; confirmation for service macro | Do not change undocumented settings |
| Teletext, picture, VTR/MDP | Configurable / learnable | Unknown codes are never emitted automatically |

**Code attribution:** [Home Assistant community (amarata)](https://community.home-assistant.io/t/tv-sony-trinitron-broadlink-and-base-64-codes-for-remote-control/768889).

## How learning works

The BroadLink can learn an IR payload from an existing working remote. The app stores learned commands locally in the user's Windows application-data folder. It does not upload them to a server.

The app cannot determine the TV's currently selected input. A source-selection macro must start from a known state and the user must verify the result.

For compatible BE-3B televisions, the service shortcut sends `Display/i+ → 5 → Vol+ → TV`, with five repeated frames per key. Verify the result on-screen.

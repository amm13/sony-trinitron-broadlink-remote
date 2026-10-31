# Contributing

Pull requests and reproducible issue reports are welcome.

## Development

- Python 3.10+ with Tkinter.
- `python -m pip install -r requirements.txt`
- `python -m unittest discover -s tests -v`
- `python sony_trinitron_remote.py`

Before adding an IR code:

1. State the exact device/remote model it was tested with, **without including serial numbers**.
2. Describe whether it was **captured/learned** or taken from another source, and credit that source.
3. Mark uncertain commands as unverified; do not add destructive factory-reset or service initialization macros.
4. Test ordinary keys before service-mode operations.
5. Do not include local IP addresses, personal data, tokens, logs or runtime configuration.

For a UI issue, supply reproduction steps and ideally a privacy-safe screenshot.
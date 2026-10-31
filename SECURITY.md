# Security and privacy

- The application operates on the **local network** and controls an IR blaster. It does not operate a web service or store user accounts.
- It can discover BroadLink device addresses at runtime. **Do not commit** runtime logs, `remote_config.json`, screenshots containing personal details, home addresses or credentials.
- User-learned infrared packets are stored locally in `%APPDATA%\SonyTrinitronBroadLink\remote_config.json`, not in the repository.
- **Service mode changes TV settings.** Only enter it deliberately, keep original values, and avoid unknown reset codes.
- A CRT can retain hazardous voltage even when unplugged. No disassembly is needed to use the app.
- Report vulnerabilities through a private channel to the repository maintainers, rather than posting sensitive details in a public issue.
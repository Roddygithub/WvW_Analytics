# EI update check (cron/systemd)

This project ships a helper to check for new Elite Insights (EI) releases without auto-installing.

## Scripts

- `scripts/check_ei_update.py`:
  - Calls GitHub API `https://api.github.com/repos/baaron4/GW2-Elite-Insights-Parser/releases/latest`
  - Compares `tag_name` with your local `ei_version.txt` (path configurable via `EI_VERSION_FILE` env, default: project root).
  - Prints either:
    - `New EI version available: {latest} (current: {current})` and lists asset download URLs
    - or `EI is up to date (version {current})`

- `scripts/check_ei_update.sh`:
  - Bash wrapper to run the Python script with your venv activated.
  - Adjust `cd` path if your deploy root differs.

## Cron example

Add to crontab (edit with `crontab -e`):

```
0 4 * * * /home/roddy/WvW_Analytics/scripts/check_ei_update.sh >> /var/log/ei_update.log 2>&1
```

Adjust paths (`/home/roddy/WvW_Analytics`, log path) as needed.

## systemd timer example (optional)

`/etc/systemd/system/ei-update.service`:
```
[Unit]
Description=Check Elite Insights updates

[Service]
Type=oneshot
User=syff
WorkingDirectory=/home/roddy/WvW_Analytics
ExecStart=/home/roddy/WvW_Analytics/scripts/check_ei_update.sh
```

`/etc/systemd/system/ei-update.timer`:
```
[Unit]
Description=Run EI update check daily

[Timer]
OnCalendar=*-*-* 04:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable timer (manual):
```
sudo systemctl daemon-reload
sudo systemctl enable --now ei-update.timer
```

This only reports available versions; install/update EI manually as desired.***

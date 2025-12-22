# WvW Analytics

A professional WvW combat analytics platform for Guild Wars 2.

## Features

- **Log Analysis**: Upload and analyze `.evtc` / `.zevtc` files or dps.report URLs
- **WvW-Only Filter**: Automatically rejects PvE/PvP logs
- **Single Fight View**: Detailed per-player stats (DPS, boons, CC, healing, etc.)
- **Multi-Log Sessions**: Aggregate stats across multiple fights
- **META by Context**: View top specs and stats by Zerg, Guild Raid, or Roam contexts

## Tech Stack

- **Backend**: Python 3.11+ with FastAPI
- **Database**: SQLite (PostgreSQL-ready via SQLAlchemy)
- **Frontend**: Server-rendered Jinja2 templates with Tailwind CSS
- **Interactivity**: HTMX + Alpine.js
- **Testing**: pytest

## Project Structure

```
wvw-analytics/
├── app/              # Python backend
├── templates/        # Jinja2 templates
├── static/           # CSS, JS, images
├── docs/             # Documentation (EVTC spec, UI/UX)
└── tests/            # pytest tests
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload
```

## Design Philosophy

- **No AI/ML**: Pure analytics, no recommendations
- **WvW-Only**: Focused exclusively on WvW combat
- **Clean Architecture**: Maintainable, professional codebase
- **GW2 Aesthetic**: Dark fantasy theme (red/black/gold, parchment tones)

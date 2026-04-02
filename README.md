# Hangman Game

A Hangman project with two playable clients:

1. Desktop app built with Python + Tkinter
2. Browser frontend (HTML/CSS/JS) with shared stats API

## Highlights

### Desktop (Tkinter)

- Difficulty and theme support
- Timer mode and hint economy
- Restart and pause/resume controls
- Local stats persistence in stats.json
- Custom word pack editor
- Achievement tracking and leaderboard

### Web Frontend

- Screenshot-inspired UI with outlined key tiles
- Profile system (create, switch, rename, delete)
- Profile avatar color selection
- Custom pack import/export (JSON)
- Settings drawer:
  - Timer seconds
  - Hints per round
  - Sound toggle
  - Reduced motion toggle
  - Contrast-safe mode
- Quick stats strip:
  - Win rate
  - Average misses
  - Best timer streak
- Balloon micro-animations:
  - Idle float
  - Pop particles on wrong guess
- Accessibility polish (focus rings + ARIA labels)

## Requirements

- Python 3.8+
- Tkinter (usually included with Python)

## Project Structure

- `app.py`: Desktop Tkinter game
- `game_logic.py`: Core game state/rules
- `stats_store.py`: Desktop stats load/save logic
- `web_server.py`: Static server + `/api/stats` endpoint
- `frontend/index.html`: Web UI
- `frontend/style.css`: Web styles
- `frontend/script.js`: Web game logic
- `tests/test_game_logic.py`: Game logic tests
- `tests/test_stats_store.py`: Stats store tests
- `build_windows.bat`: Build desktop executable (PyInstaller)
- `build_windows.ps1`: Build desktop executable (PowerShell)

## Run Desktop App

```bash
python app.py
```

## Run Web Frontend (With Shared Stats API)

```bash
python web_server.py
```

Then open:

- `http://localhost:5500/frontend/`

Stats API endpoint:

- `http://localhost:5500/api/stats`

## Shared Stats

The desktop and web versions can both read/write the same `stats.json` file through compatible fields.

## Run Tests

```bash
python -m unittest discover -s tests -v
```

## Build Windows Executable

Command Prompt:

```bat
build_windows.bat
```

PowerShell:

```powershell
./build_windows.ps1
```

Output folder:

- `dist/Hangman/`

## Notes

- Frontend and desktop are intentionally independent UIs with shared persistence.
- If `web_server.py` is not running, frontend falls back to localStorage.

## Contributing

Contributions are welcome via issues and pull requests.

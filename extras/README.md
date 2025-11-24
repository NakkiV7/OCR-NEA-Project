FreeKnight WASD Demo

This is a minimal pygame demo that uses the FreeKnight assets in `assets/FreeKnight_v1/Colour1/NoOutline/120x80_PNGSheets`.

Requirements

- Python 3.8+
- `pygame` (see `requirements.txt`)

Install and run (PowerShell on Windows):

```powershell
python -m pip install -r requirements.txt
python .\main.py
```

Controls

- W A S D — Move the knight
- Close the window to exit

Notes

- The demo expects `_Idle.png` and `_Run.png` sprite sheets to exist in the `120x80_PNGSheets` folder. If you want different color variants, point `ASSETS_DIR` in `main.py` to a different folder under `assets/FreeKnight_v1`.
- Frame size and scaling are configurable in `main.py` via `FRAME_W`, `FRAME_H`, and `SCALE`.

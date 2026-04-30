# Squad Sheet Generator (Web)

A web version of the Squad Sheet Generator. Users upload a squadding HTML file in their browser and download the generated PDF — no local install required.

## Files

- `app.py` — the Streamlit web app (all squad parsing + LaTeX logic from the original script)
- `requirements.txt` — Python dependencies
- `packages.txt` — system packages (TeX Live) for Streamlit Community Cloud
- `LogoSmall.png` — *(optional)* place your league logo here to bundle a default. Users can also upload their own via the UI.

## Run locally (for testing)

```bash
pip install -r requirements.txt
# Make sure pdflatex is installed (MacTeX, MiKTeX, or TeX Live)
streamlit run app.py
```

The app opens at <http://localhost:8501>.

## Deploy free on Streamlit Community Cloud

1. Push this folder to a **public GitHub repo** (e.g. `squad-sheets-web`).
2. Go to <https://share.streamlit.io> and sign in with GitHub.
3. Click **New app**, select your repo, branch `main`, and main file `app.py`.
4. Click **Deploy**. First boot takes ~5 minutes because it installs TeX Live from `packages.txt`.
5. You'll get a public URL like `https://your-app.streamlit.app` — share that with anyone.

## Deploy elsewhere

Any Linux host with Python 3.9+ and TeX Live works:

```bash
sudo apt install texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended
pip install -r requirements.txt
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

For production, put it behind nginx + a domain, or deploy to Render / Railway / Fly.io with the included `packages.txt` translated to their build config.

## Notes

- Each user's files are processed in a private temp directory, so concurrent users don't collide.
- The original Tkinter script (`generate_squad_sheets.py`) still works locally for users who prefer the desktop app.

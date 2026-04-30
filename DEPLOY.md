# Deploying to `squads.wnpl.org`

End-to-end steps to get the squad sheet generator live at `https://squads.wnpl.org`. About 30 minutes of work, mostly waiting on DNS.

---

## Step 1 — Push the project to GitHub

1. Create a new GitHub repo (public is easiest; private also works on Render).
2. Drop the contents of the `squad_sheets_web` folder at the root of the repo. The repo should look like:
   ```
   app.py
   Dockerfile
   .dockerignore
   render.yaml
   requirements.txt
   packages.txt        ← only used if you ever switch back to Streamlit Cloud; harmless on Render
   README.md
   DEPLOY.md
   LogoSmall.png       ← optional, bundles a default logo
   ```
3. Commit and push to `main`.

---

## Step 2 — Deploy on Render

1. Go to <https://render.com> and sign up / log in (free, can use GitHub OAuth).
2. Click **New +** → **Blueprint**.
3. Connect your GitHub account if you haven't, then pick the repo you just pushed.
4. Render reads `render.yaml` automatically. It'll show a service called **squad-sheets** on the **free** plan. Click **Apply**.
5. First build takes ~5–8 minutes (it's installing TeX Live in the Docker image). You can watch the build log in the Render dashboard.
6. When it's done, Render gives you a URL like `https://squad-sheets-xyz.onrender.com`. Open it — you should see the app. Test it with a real squadding HTML file before continuing.

> **Free-tier note:** the service sleeps after 15 minutes of inactivity. The first request after a quiet period takes ~30 seconds to wake up. Bump to the **Starter** plan ($7/mo) in Render to keep it always-on.

---

## Step 3 — Add the custom domain in Render

1. In your Render dashboard → **squad-sheets** service → **Settings** → **Custom Domains**.
2. Click **Add Custom Domain**, enter `squads.wnpl.org`, click **Save**.
3. Render shows you a **CNAME target** that looks like `squad-sheets-xyz.onrender.com`. **Copy this.**
4. Render also shows the domain status as "Pending verification" — that's expected until DNS is set up.

---

## Step 4 — Add the CNAME at IONOS

`wnpl.org` is hosted at IONOS (1&1), so DNS changes happen there.

1. Log in to <https://www.ionos.com> with the account that owns `wnpl.org`.
2. Click **Domains & SSL** in the sidebar.
3. Click **wnpl.org**, then click the **DNS** tab.
4. Click **Add Record** → choose **CNAME**.
5. Fill in:
   - **Host name:** `squads`   *(just the prefix — IONOS appends `.wnpl.org`)*
   - **Points to:** the CNAME target Render gave you (e.g. `squad-sheets-xyz.onrender.com`)
   - **TTL:** 1 hour (3600s) is fine
6. Save.

---

## Step 5 — Wait, then verify

1. DNS propagation usually takes 5–30 minutes. You can check progress with:
   ```bash
   dig squads.wnpl.org CNAME
   ```
   You should see your `*.onrender.com` target.
2. Render will detect the DNS change automatically and issue a **Let's Encrypt TLS certificate** within a few minutes after that. The Custom Domains panel will flip from "Pending" to "Verified" with a green checkmark.
3. Visit <https://squads.wnpl.org>. Done.

---

## Linking from the existing wnpl.org site

To add a link from the main site, edit `Main.htm` (or wherever your menu lives) on IONOS and add something like:

```html
<a href="https://squads.wnpl.org" target="_blank">Squad Sign-In Sheets</a>
```

Upload via IONOS File Manager or FTP, same as any other site update.

---

## Updating the app later

Any push to `main` on GitHub triggers an automatic redeploy (because `autoDeploy: true` in `render.yaml`). No manual steps needed.

---

## If something breaks

- **Render build fails** → check the build log; usually it's a typo in `Dockerfile` or a missing file
- **`https://squads.wnpl.org` shows a cert warning** → DNS hasn't fully propagated yet. Wait another 15 min, then refresh
- **CNAME won't save in IONOS** because there's already an A record for `squads` → delete the existing record first, then add the CNAME
- **First load after quiet period is slow** → free tier cold start; upgrade to Starter or set up an external uptime ping (e.g. UptimeRobot every 10 min) to keep it warm

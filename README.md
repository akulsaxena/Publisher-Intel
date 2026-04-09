# Joveo Publisher Intel — Setup Guide

Automated daily Slack digest for the Partnerships team.
Runs every weekday morning at 8:30 AM IST, posts to `#supply-partnership-product`.

---

## What you need (takes ~15 minutes total)

| Thing | Where to get it | Time |
|---|---|---|
| Gemini API key | aistudio.google.com/apikey | 2 min |
| Slack Webhook URL | api.slack.com/apps | 5 min |
| GitHub account | github.com | already have it |
| Render account | render.com (free) | 3 min |

---

## Step 1 — Get your Gemini API key

1. Go to https://aistudio.google.com/apikey
2. Sign in with your Google account
3. Click **Create API key**
4. Copy it — looks like `AIzaSy...`

> Free tier gives you 1,500 requests/day — way more than you need.

---

## Step 2 — Create your Slack Webhook

1. Go to https://api.slack.com/apps
2. Click **Create New App** → **From Scratch**
3. Name it `Publisher Intel`, pick your workspace → **Create App**
4. In the left sidebar → **Incoming Webhooks** → toggle **Activate Incoming Webhooks** ON
5. Click **Add New Webhook to Workspace**
6. Pick the `#supply-partnership-product` channel → **Allow**
7. Copy the Webhook URL — looks like `https://hooks.slack.com/services/T.../B.../xxx`

---

## Step 3 — Push to GitHub

Create a new **private** GitHub repo and push these 3 files:

```
brief.py
requirements.txt
render.yaml
```

```bash
git init
git add .
git commit -m "Joveo Publisher Intel"
git remote add origin https://github.com/YOUR_USERNAME/joveo-intel.git
git push -u origin main
```

---

## Step 4 — Deploy on Render

1. Go to https://render.com and sign up (free)
2. Click **New** → **Cron Job**
3. Connect your GitHub account and select the `joveo-intel` repo
4. Render will auto-detect `render.yaml` — click **Apply**
5. In the service settings → **Environment** → add two variables:

   | Key | Value |
   |---|---|
   | `GEMINI_API_KEY` | Your key from Step 1 |
   | `SLACK_WEBHOOK_URL` | Your webhook from Step 2 |

6. Click **Save Changes** → **Deploy**

---

## Step 5 — Test it manually

In Render, go to your cron job → click **Trigger Run**.
Check `#supply-partnership-product` in Slack — brief should appear within ~60 seconds.

---

## Schedule

| Day | What gets researched |
|---|---|
| Monday | P0 publishers (top 26 strategic partners) |
| Tuesday | P1/P2 Batch 1 |
| Wednesday | P1/P2 Batch 2 |
| Thursday | P0 publishers again |
| Friday | P1/P2 Batch 3 |

Runs at **8:30 AM IST** every weekday (3:00 AM UTC).
To change the time, edit the `schedule` line in `render.yaml`.
Use https://crontab.guru to convert times.

---

## Changing the run time

Edit `render.yaml`:
```yaml
schedule: "0 3 * * 1-5"   # currently 8:30 AM IST
```

Some common IST times:
- 8:00 AM IST → `"30 2 * * 1-5"`
- 9:00 AM IST → `"30 3 * * 1-5"`
- 9:30 AM IST → `"0 4 * * 1-5"`

---

## Troubleshooting

**Brief not appearing in Slack**
→ Check Render logs for errors
→ Verify `SLACK_WEBHOOK_URL` is correct and the app is still in the channel

**Gemini returning empty or weak results**
→ Google Search grounding may be temporarily limited — re-trigger manually
→ Check AI Studio dashboard for quota usage

**Want to add a publisher to P0?**
→ Edit the `P0_PUBLISHERS` list in `brief.py` and push to GitHub
→ Render auto-deploys on push

---

## Files

| File | Purpose |
|---|---|
| `brief.py` | Main script — all logic lives here |
| `requirements.txt` | Python dependencies |
| `render.yaml` | Render deployment config |

# 🚂 RAILWAY QUICK START - 5 MINUTE DEPLOY

## 📦 STEP 1: GITHUB (2 minutes)

```bash
# In your project folder:
git init
git add .
git commit -m "NBA Betting API"
git remote add origin https://github.com/YOUR_USERNAME/nba-betting-api.git
git push -u origin main
```

---

## 🚀 STEP 2: RAILWAY (2 minutes)

1. Go to **railway.app**
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose **nba-betting-api**
5. Railway auto-deploys! ⏳

---

## 🔗 STEP 3: GET URL (30 seconds)

1. Click **"Settings"** → **"Generate Domain"**
2. Copy URL: `https://nba-betting-api-production-xxxx.up.railway.app`

---

## ✅ STEP 4: TEST (30 seconds)

```bash
curl https://YOUR-RAILWAY-URL.up.railway.app/api/health
```

Should return: `{"success": true, "status": "healthy"}`

---

## 🎯 STEP 5: UPDATE BASE44

In Base44 JavaScript, change:

```javascript
// OLD:
const API_URL = 'http://localhost:5000/api';

// NEW:
const API_URL = 'https://YOUR-RAILWAY-URL.up.railway.app/api';
```

---

## ✅ DONE!

Your API is now:
✅ Live 24/7
✅ Accessible from anywhere
✅ Auto-deploys on git push
✅ Free tier available

---

## 🔄 TO UPDATE LATER:

```bash
# Make changes to code
git add .
git commit -m "Updated X"
git push

# Railway auto-deploys!
```

---

## 📊 FILES INCLUDED:

✅ `Procfile` - Railway startup command
✅ `railway.json` - Railway config
✅ `runtime.txt` - Python version
✅ `.gitignore` - Git ignore rules
✅ `requirements.txt` - Dependencies
✅ Updated Flask app for Railway PORT

---

## 🐛 TROUBLESHOOTING:

**Build failed?**
- Check Railway logs in dashboard
- Verify all files are in repo

**API not responding?**
- Check Railway logs
- Verify domain is generated

**CORS errors in Base44?**
- Already configured in Flask app
- Should work automatically

---

## 💰 PRICING:

- **Free:** $5 credit/month (plenty for this!)
- **Hobby:** $5/month if you exceed free tier

---

**Need help? Check `RAILWAY_DEPLOYMENT.md` for full guide!**

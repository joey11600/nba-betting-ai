# 🚂 RAILWAY DEPLOYMENT GUIDE

Complete step-by-step guide to deploy your NBA Betting Stats API to Railway.

---

## 🚀 DEPLOYMENT STEPS

### STEP 1: Create GitHub Repository

1. Go to [GitHub.com](https://github.com)
2. Click **"New repository"**
3. Name it: `nba-betting-api`
4. Make it **Private** (keep your betting data private!)
5. Don't initialize with README (we have files already)
6. Click **"Create repository"**

---

### STEP 2: Push Code to GitHub

Open terminal/command prompt in your project folder:

```bash
# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - NBA Betting API"

# Add your GitHub repo as remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/nba-betting-api.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Troubleshooting:**
- If you get authentication errors, use a GitHub Personal Access Token
- Go to GitHub Settings → Developer settings → Personal access tokens
- Generate new token with "repo" permissions
- Use token as password when pushing

---

### STEP 3: Deploy to Railway

1. Go to [Railway.app](https://railway.app)

2. **Sign up** (you can use GitHub login)

3. Click **"New Project"**

4. Select **"Deploy from GitHub repo"**

5. **Authorize Railway** to access your GitHub

6. **Select your repo:** `nba-betting-api`

7. Railway will **auto-detect** Flask and start deploying!

8. Wait 2-3 minutes for build to complete ⏳

---

### STEP 4: Get Your Railway URL

1. Once deployed, click on your project

2. Go to **"Settings"** tab

3. Click **"Generate Domain"**

4. You'll get a URL like:
   ```
   https://nba-betting-api-production-xxxx.up.railway.app
   ```

5. **Copy this URL** - you'll need it for Base44!

---

### STEP 5: Test Your Deployment

Test the API is working:

```bash
# Replace with your Railway URL
curl https://nba-betting-api-production-xxxx.up.railway.app/api/health
```

Should return:
```json
{
  "success": true,
  "status": "healthy",
  "service": "NBA Betting Stats API"
}
```

**Test player search:**
```bash
curl "https://nba-betting-api-production-xxxx.up.railway.app/api/players/search?q=jaden"
```

---

### STEP 6: Update Base44 with Railway URL

In your Base44 app's **Custom JavaScript**, find this line:

```javascript
const API_URL = 'http://localhost:5000/api';
```

**Change it to your Railway URL:**

```javascript
const API_URL = 'https://nba-betting-api-production-xxxx.up.railway.app/api';
```

**⚠️ Important:** Remove the `/api` at the end of the Railway URL, then add `/api` in the constant!

Example:
- Railway URL: `https://nba-betting-api-production-abc123.up.railway.app`
- Use in code: `https://nba-betting-api-production-abc123.up.railway.app/api`

---

## ✅ VERIFY EVERYTHING WORKS

### Test in Base44:

1. **Player Search:**
   - Type "Jaden" in player search
   - Should see dropdown with NBA players

2. **Create Bet:**
   - Fill out bet form
   - Click "Create Bet"
   - Should get confirmation

3. **Add Props:**
   - Search player, add prop
   - Should work seamlessly

4. **Mark Results:**
   - Go to results page
   - Mark a prop as miss
   - Should capture stats automatically

---

## 📊 RAILWAY DASHBOARD

Your Railway dashboard shows:

- **Deployments:** History of deploys
- **Logs:** Real-time API logs (great for debugging!)
- **Metrics:** CPU, memory, requests
- **Settings:** Environment variables, domains

**Pro tip:** Keep the logs tab open while testing!

---

## 💰 PRICING

**Free Tier:**
- $5 free credit per month
- 500 hours execution
- Perfect for this API!

**Hobby Plan ($5/month):**
- If you exceed free tier
- Unlimited execution time
- Still super cheap

**Your API is lightweight** - free tier should be plenty!

---

## 🔄 UPDATING YOUR API

When you make changes to the code:

```bash
# Make your changes to the code

# Commit changes
git add .
git commit -m "Updated feature X"

# Push to GitHub
git push

# Railway auto-deploys! 🎉
```

Railway automatically redeploys when you push to GitHub!

---

## 🔐 SECURITY NOTES

### Environment Variables (if needed later)

If you want to add API keys or secrets:

1. Go to Railway project
2. Click **"Variables"** tab
3. Add variable (e.g., `SECRET_KEY`)
4. Access in Python:
   ```python
   import os
   secret = os.environ.get('SECRET_KEY')
   ```

### Database Persistence

⚠️ **Important:** Railway's filesystem is ephemeral!

Your SQLite database will reset on each deploy.

**Solutions:**

**Option A: Railway PostgreSQL (Recommended)**
- Add PostgreSQL plugin in Railway
- Update code to use PostgreSQL instead of SQLite
- Database persists forever

**Option B: Railway Volumes**
- Mount a persistent volume
- Store SQLite there

**Option C: Keep SQLite for now**
- Fine for testing
- Migrate to PostgreSQL later when you have real data

**For now, SQLite is fine while you're testing!**

---

## 🐛 TROUBLESHOOTING

### Build Failed?

**Check Railway logs:**
1. Go to your project
2. Click **"Deployments"**
3. Click the failed deployment
4. Read the error logs

**Common issues:**
- Missing `requirements.txt`
- Wrong Python version
- Missing `Procfile`

All these files are included in your package!

### API Not Responding?

**Check logs in Railway dashboard:**
- Look for Python errors
- Check if gunicorn started
- Verify PORT environment variable is set

### CORS Errors in Base44?

If you see CORS errors in browser console:

The Flask app already has CORS enabled, but if issues persist:

```python
# In flask_api_base44.py, update CORS line:
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

### Database Issues?

Remember: SQLite resets on deploy!

If you need persistent data:
1. Add Railway PostgreSQL plugin
2. Update `nba_betting_stats_api.py` to use PostgreSQL
3. Or add Railway volume for SQLite

---

## 📱 MOBILE ACCESS

Since your API is now on Railway:

✅ Works on your phone
✅ Works on any device
✅ Works anywhere with internet
✅ Always running (no need to keep computer on!)

Your Base44 app now works from anywhere!

---

## 🎯 NEXT STEPS

Once deployed and working:

1. **Test everything** - Create bets, mark results, view analytics
2. **Let it run** - Start tracking 20-30 bets
3. **Check analytics** - See which players/matchups bust
4. **Migrate to PostgreSQL** - When you want permanent data storage

---

## 💡 PRO TIPS

**Use Railway CLI for easy deploys:**
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link project
railway link

# Deploy
railway up
```

**View logs in real-time:**
```bash
railway logs
```

**Custom domain (optional):**
- Go to Railway Settings
- Add custom domain
- Point your DNS to Railway
- Example: `api.jagbetting.com`

---

## 📞 NEED HELP?

**Railway Resources:**
- [Railway Docs](https://docs.railway.app)
- [Railway Discord](https://discord.gg/railway)
- Railway status: [status.railway.app](https://status.railway.app)

**Common Commands:**
```bash
# View logs
railway logs

# Restart service
railway restart

# Check status
railway status
```

---

## ✅ DEPLOYMENT CHECKLIST

- [ ] Created GitHub repo
- [ ] Pushed code to GitHub
- [ ] Connected Railway to GitHub
- [ ] Railway deployed successfully
- [ ] Generated Railway domain
- [ ] Tested `/api/health` endpoint
- [ ] Tested `/api/players/search`
- [ ] Updated Base44 with Railway URL
- [ ] Tested player search in Base44
- [ ] Created test bet
- [ ] Added test prop
- [ ] Marked result (captured stats)
- [ ] Viewed analytics

🎉 **You're live!**

---

**Questions? Let me know and I'll help debug!**

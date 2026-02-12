# Quick Deployment Guide - Railway.app (Fastest Method)

## Prerequisites
- GitHub account with code pushed to repository
- Railway account (sign up at https://railway.app - free tier available)
- OpenAI API key

## Step-by-Step Deployment

### 1. Push Code to GitHub (if not already done)
```bash
git add .
git commit -m "Prepare for production deployment"
git push origin main
```

### 2. Deploy Backend

1. Go to https://railway.app and sign in
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your repository
4. Railway will detect the backend folder automatically
5. Go to **Settings** → **Variables** and add:
   - `OPENAI_API_KEY` = (your OpenAI API key)
   - `ALLOWED_ORIGINS` = (leave empty for now, we'll update after frontend is deployed)
6. Railway will automatically build and deploy using the Dockerfile
7. Once deployed, copy the **Public Domain** URL (e.g., `your-backend.up.railway.app`)

### 3. Deploy Frontend

1. In the same Railway project, click **"New Service"** → **"GitHub Repo"**
2. Select the same repository
3. Set **Root Directory** to `frontend`
4. Go to **Settings** → **Variables** and add:
   - `VITE_API_URL` = `https://your-backend.up.railway.app` (use the backend URL from step 2)
5. Railway will build and deploy
6. Copy the **Public Domain** URL (e.g., `your-frontend.up.railway.app`)

### 4. Update CORS Settings

1. Go back to backend service → **Settings** → **Variables**
2. Update `ALLOWED_ORIGINS` to include your frontend URL:
   ```
   http://localhost:5173,http://localhost:3000,https://your-frontend.up.railway.app
   ```
3. Backend will automatically redeploy

### 5. Test Deployment

1. Visit your frontend URL: `https://your-frontend.up.railway.app`
2. Try uploading a video file
3. Check that transcription works

---

## Custom Domain Setup

### Option A: Use Railway Subdomain (Instant)
- Railway provides free subdomains: `your-app.up.railway.app`
- HTTPS is automatically enabled
- No DNS configuration needed

### Option B: Add Custom Domain (15-30 minutes)

1. **Purchase Domain** (if needed):
   - Namecheap, Google Domains, Cloudflare, etc.
   - Cost: ~$10-15/year

2. **Add Domain to Railway**:
   - Backend: Go to backend service → **Settings** → **Domains** → **Custom Domain**
   - Add: `api.yourdomain.com`
   - Frontend: Go to frontend service → **Settings** → **Domains** → **Custom Domain**
   - Add: `yourdomain.com` or `www.yourdomain.com`

3. **Configure DNS** (at your domain registrar):
   - Add CNAME record: `api.yourdomain.com` → `your-backend.up.railway.app`
   - Add CNAME record: `yourdomain.com` → `your-frontend.up.railway.app`
   - Add CNAME record: `www.yourdomain.com` → `your-frontend.up.railway.app`

4. **Wait for DNS Propagation**:
   - Usually 5-30 minutes
   - Check with: `dig api.yourdomain.com` or online DNS checker

5. **Update Environment Variables**:
   - Backend: Update `ALLOWED_ORIGINS` to include `https://yourdomain.com`
   - Frontend: Update `VITE_API_URL` to `https://api.yourdomain.com` (if using subdomain)

6. **Verify SSL**:
   - Railway automatically provisions SSL certificates
   - Check that HTTPS works: `https://yourdomain.com`

---

## Environment Variables Reference

### Backend Service
- `OPENAI_API_KEY` (required) - Your OpenAI API key
- `ALLOWED_ORIGINS` (optional) - Comma-separated list of allowed CORS origins
- `PORT` (auto-set) - Railway automatically sets this

### Frontend Service
- `VITE_API_URL` (required) - Full URL to backend API (e.g., `https://api.yourdomain.com` or `https://your-backend.up.railway.app`)

---

## Troubleshooting

### Backend won't start
- Check logs in Railway dashboard
- Verify `OPENAI_API_KEY` is set correctly
- Ensure Dockerfile is in `backend/` directory

### Frontend can't connect to backend
- Verify `VITE_API_URL` is set correctly (must be full URL with https://)
- Check CORS settings in backend (`ALLOWED_ORIGINS`)
- Check browser console for errors

### FFmpeg errors
- Dockerfile includes FFmpeg installation
- If issues persist, check Railway build logs

### File upload fails
- Check file size limits (default: 500MB)
- Verify backend has sufficient disk space
- Check Railway logs for errors

---

## Cost Estimate

**Railway Free Tier:**
- $5 credit/month
- 500 hours of usage
- Usually enough for small projects

**Paid Tier:**
- Starts at ~$5/month for always-on services
- Pay-as-you-go pricing

**Domain:**
- ~$10-15/year (optional)

**OpenAI API:**
- $0.006 per minute of audio
- Pay per use

---

## Next Steps

1. ✅ Deploy backend and frontend
2. ✅ Test basic functionality
3. ✅ Set up custom domain (optional)
4. ⏭️ Set up monitoring (optional)
5. ⏭️ Configure backups (optional)
6. ⏭️ Add analytics (optional)

---

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Check Railway dashboard logs for deployment issues

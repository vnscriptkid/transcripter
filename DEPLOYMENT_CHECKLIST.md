# Deployment Checklist

## Pre-Deployment

- [ ] Code is pushed to GitHub
- [ ] OpenAI API key is ready
- [ ] Domain purchased (if using custom domain)
- [ ] All environment variables documented

## Backend Deployment

- [ ] Create Railway account
- [ ] Create new project from GitHub repo
- [ ] Set root directory to `backend/`
- [ ] Add environment variable: `OPENAI_API_KEY`
- [ ] Verify Dockerfile exists in `backend/`
- [ ] Deploy backend service
- [ ] Copy backend public URL
- [ ] Test backend health endpoint: `https://your-backend.up.railway.app/health`

## Frontend Deployment

- [ ] Add new service in same Railway project
- [ ] Set root directory to `frontend/`
- [ ] Add environment variable: `VITE_API_URL` = backend URL
- [ ] Verify Dockerfile exists in `frontend/`
- [ ] Deploy frontend service
- [ ] Copy frontend public URL

## CORS Configuration

- [ ] Update backend `ALLOWED_ORIGINS` environment variable
- [ ] Include frontend URL in allowed origins
- [ ] Backend redeploys automatically

## Domain Setup (Optional)

- [ ] Add custom domain to backend service
- [ ] Add custom domain to frontend service
- [ ] Configure DNS records at domain registrar:
  - [ ] CNAME: `api.yourdomain.com` → backend Railway URL
  - [ ] CNAME: `yourdomain.com` → frontend Railway URL
  - [ ] CNAME: `www.yourdomain.com` → frontend Railway URL
- [ ] Wait for DNS propagation (5-30 minutes)
- [ ] Verify SSL certificates are issued
- [ ] Update `ALLOWED_ORIGINS` with custom domain
- [ ] Update `VITE_API_URL` with custom domain (if using subdomain)

## Testing

- [ ] Visit frontend URL
- [ ] Test video file upload
- [ ] Verify transcription completes successfully
- [ ] Check transcript display
- [ ] Test copy to clipboard functionality
- [ ] Test on mobile device (if applicable)
- [ ] Check browser console for errors
- [ ] Verify HTTPS is working

## Post-Deployment

- [ ] Monitor Railway logs for errors
- [ ] Set up error tracking (optional - Sentry, etc.)
- [ ] Configure backups for uploaded files (optional)
- [ ] Set up monitoring/alerts (optional)
- [ ] Document production URLs
- [ ] Share deployment info with team

## Security Checklist

- [ ] Environment variables are set (not hardcoded)
- [ ] `.env` file is in `.gitignore`
- [ ] CORS is properly configured
- [ ] File upload size limits are appropriate
- [ ] HTTPS is enabled
- [ ] API keys are secure

## Rollback Plan

- [ ] Know how to revert to previous deployment in Railway
- [ ] Have previous working version tagged in Git
- [ ] Document rollback procedure

---

## Quick Reference

### Railway Dashboard
- Backend URL: `https://your-backend.up.railway.app`
- Frontend URL: `https://your-frontend.up.railway.app`

### Environment Variables

**Backend:**
```
OPENAI_API_KEY=sk-...
ALLOWED_ORIGINS=http://localhost:5173,https://your-frontend.up.railway.app
```

**Frontend:**
```
VITE_API_URL=https://your-backend.up.railway.app
```

### DNS Records (Custom Domain)
```
Type: CNAME
Name: api
Value: your-backend.up.railway.app

Type: CNAME
Name: @ (or yourdomain.com)
Value: your-frontend.up.railway.app

Type: CNAME
Name: www
Value: your-frontend.up.railway.app
```

# Production Deployment Plan - Video Transcriber

## Quick Deployment Options (Fastest to Slowest)

### Option 1: Railway.app (Recommended - Fastest) ⚡
**Time: 15-30 minutes**
- Zero-config deployment
- Automatic HTTPS
- Built-in domain or custom domain support
- Free tier available

### Option 2: Render.com
**Time: 20-40 minutes**
- Easy setup with GitHub integration
- Free tier with limitations
- Automatic SSL certificates

### Option 3: Fly.io
**Time: 30-45 minutes**
- Global edge deployment
- Good for file uploads
- Free tier available

### Option 4: DigitalOcean App Platform
**Time: 30-60 minutes**
- Managed platform
- Auto-scaling
- $5/month minimum

### Option 5: VPS (DigitalOcean/Linode) + Docker
**Time: 1-2 hours**
- Full control
- Most cost-effective long-term
- Requires more setup

---

## Recommended: Railway.app Deployment (Fastest Path)

### Prerequisites
- GitHub account (code should be pushed to GitHub)
- Railway account (free at railway.app)
- Domain name (optional, can use Railway subdomain)

### Step 1: Prepare Code for Production

#### 1.1 Update CORS Settings
Update `backend/app/main.py` to allow production domain:
```python
allow_origins=["http://localhost:5173", "http://localhost:3000", "https://yourdomain.com"]
```

#### 1.2 Create Production Config
Create `backend/.env.production` template (don't commit secrets)

#### 1.3 Add Build Scripts
Create `backend/Dockerfile` and `frontend/Dockerfile` (or use Railway's auto-detection)

### Step 2: Add PostgreSQL Database to Railway

1. **In your Railway project**, click **"+ New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway will automatically create a PostgreSQL service
3. **Note the DATABASE_URL**: Railway automatically sets this as an environment variable
   - The `DATABASE_URL` will be in format: `postgresql://user:password@host:port/dbname`
   - Our app automatically converts this to `postgresql+asyncpg://` format for async operations

### Step 3: Deploy Backend to Railway

1. **Sign up/Login to Railway**: https://railway.app
2. **Create New Project** → "Deploy from GitHub repo"
3. **Select your repository**
4. **Add Backend Service**:
   - Click **"+ New"** → **"GitHub Repo"** → Select your repository
   - Root Directory: `backend`
   - Environment Variables:
     - `OPENAI_API_KEY` = (your OpenAI key)
     - `PORT` = (auto-set by Railway)
     - `DATABASE_URL` = (automatically set when you connect PostgreSQL service)
5. **Connect PostgreSQL to Backend**:
   - In your backend service settings, go to **"Variables"** tab
   - Railway should automatically detect and link the PostgreSQL service
   - The `DATABASE_URL` environment variable will be automatically populated
6. **Run Database Migrations**:
   - Option A: Add to startup command in Railway:
     ```bash
     alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - Option B: Use Railway CLI to run migrations:
     ```bash
     railway run alembic upgrade head
     ```
   - Option C: Add a one-time migration service (recommended for production):
     - Create a new service with command: `alembic upgrade head`
     - Run it once, then delete the service

### Step 4: Deploy Frontend to Railway

1. **Add New Service** → "GitHub Repo" (same repo)
2. **Configure Frontend Service**:
   - Root Directory: `frontend`
   - Environment Variables:
     - `VITE_API_URL` = (backend Railway URL + /api)
3. **Update Frontend API Client**:
   - Modify `frontend/src/api/client.js` to use `import.meta.env.VITE_API_URL || '/api'`

### Step 5: Domain Setup

#### Option A: Use Railway Subdomain (Instant)
- Railway provides: `your-app.up.railway.app`
- No DNS configuration needed
- HTTPS automatically enabled

#### Option B: Custom Domain (15-30 minutes)

1. **Purchase Domain** (if not owned):
   - Namecheap, Google Domains, Cloudflare, etc.
   - Cost: ~$10-15/year

2. **Add Domain to Railway**:
   - Go to your service → Settings → Domains
   - Add custom domain: `api.yourdomain.com` (backend)
   - Add custom domain: `yourdomain.com` or `www.yourdomain.com` (frontend)

3. **Configure DNS**:
   - Go to your domain registrar's DNS settings
   - Add CNAME records:
     ```
     api.yourdomain.com → your-backend-service.up.railway.app
     yourdomain.com → your-frontend-service.up.railway.app
     www.yourdomain.com → your-frontend-service.up.railway.app
     ```
   - Wait 5-30 minutes for DNS propagation

4. **Update CORS**:
   - Update backend CORS to include: `https://yourdomain.com`
   - Redeploy backend service

---

## PostgreSQL Database Setup

### Local Development with Docker Compose

The `docker-compose.yml` file includes a PostgreSQL service for local development:

1. **Start services**:
   ```bash
   docker-compose up -d
   ```

2. **Run database migrations**:
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

3. **Database connection**:
   - Host: `localhost`
   - Port: `5432`
   - Database: `transcripter`
   - User: `postgres`
   - Password: `postgres`
   - Connection string: `postgresql+asyncpg://postgres:postgres@localhost:5432/transcripter`

### Railway.app PostgreSQL Setup

Railway.app provides managed PostgreSQL databases:

1. **Add PostgreSQL Service**:
   - In your Railway project, click **"+ New"** → **"Database"** → **"Add PostgreSQL"**
   - Railway automatically creates a PostgreSQL instance

2. **Automatic Connection**:
   - Railway automatically sets the `DATABASE_URL` environment variable
   - The backend service will automatically connect to PostgreSQL when linked
   - To link services: Go to backend service → Settings → Variables → Connect PostgreSQL

3. **Database Migrations on Railway**:
   
   **Option A: Run migrations on startup** (Recommended for development):
   - Update Railway start command to:
     ```bash
     alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - This runs migrations every time the service starts
   
   **Option B: Use Railway CLI** (Recommended for production):
   ```bash
   # Install Railway CLI
   npm i -g @railway/cli
   
   # Login
   railway login
   
   # Link to your project
   railway link
   
   # Run migrations
   railway run alembic upgrade head
   ```
   
   **Option C: One-time migration service**:
   - Create a new service with command: `alembic upgrade head`
   - Run it once, then delete the service

4. **Database Management**:
   - Access Railway PostgreSQL via Railway dashboard → PostgreSQL service → "Data" tab
   - Or use Railway CLI: `railway connect postgres`
   - Or use external tools with connection string from Railway dashboard

5. **Environment Variables**:
   - `DATABASE_URL` is automatically set by Railway
   - Format: `postgresql://user:password@host:port/dbname`
   - Our app automatically converts to `postgresql+asyncpg://` format

### Database Schema

The application uses a single `transcripts` table with the following structure:
- `id` (String, Primary Key): Unique transcript identifier
- `filename` (String): Original video filename
- `relative_path` (String, Optional): Path relative to folder root (for folder uploads)
- `batch_id` (String, Optional): Groups transcripts from same folder upload
- `status` (String): Transcription status (pending, extracting_audio, transcribing, completed, failed)
- `error` (Text, Optional): Error message if transcription failed
- `duration` (Float, Optional): Video duration in seconds
- `language` (String, Optional): Detected language code
- `transcript_content` (JSONB): Full transcript content stored as JSON
- `created_at` (DateTime): Creation timestamp
- `updated_at` (DateTime): Last update timestamp

Indexes are created on:
- `batch_id` (for filtering by batch)
- `status` (for filtering by status)
- `created_at` (for sorting)

---

## Alternative: Render.com Deployment

### Backend Setup
1. Create new **Web Service** on Render
2. Connect GitHub repository
3. Settings:
   - Build Command: `cd backend && pip install -r requirements.txt`
   - Start Command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Environment: `OPENAI_API_KEY`
   - Add FFmpeg: Use Dockerfile or buildpack

### Frontend Setup
1. Create new **Static Site** on Render
2. Build Command: `cd frontend && npm install && npm run build`
   - Set `VITE_API_URL` environment variable
3. Publish Directory: `frontend/dist`

### Domain Setup
- Render provides free subdomain: `your-app.onrender.com`
- Custom domain: Add in Render dashboard → Custom Domain
- Update DNS with CNAME to Render's provided domain

---

## Alternative: Docker + VPS (Most Control)

### Docker Setup

#### Backend Dockerfile
```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend Dockerfile
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### docker-compose.yml
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/transcripts:/app/transcripts

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

### VPS Deployment Steps
1. **Provision VPS** (DigitalOcean Droplet, Linode, etc.)
2. **Install Docker**: `curl -fsSL https://get.docker.com | sh`
3. **Clone repository**: `git clone <your-repo>`
4. **Set environment variables**: Create `.env` file
5. **Run**: `docker-compose up -d`
6. **Setup Nginx reverse proxy** for domain
7. **Setup SSL** with Let's Encrypt (Certbot)

---

## Required Code Changes

### 1. Backend: Update CORS (`backend/app/main.py`)
```python
import os
from fastapi.middleware.cors import CORSMiddleware

# Get allowed origins from environment
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Frontend: Environment-based API URL (`frontend/src/api/client.js`)
```javascript
const API_BASE = import.meta.env.VITE_API_URL || '/api';
```

### 3. Frontend: Update Vite Config (`frontend/vite.config.js`)
```javascript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

### 4. Create Production Build Scripts

#### `backend/railway.json` (for Railway)
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "apt-get update && apt-get install -y ffmpeg && pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

## Domain Setup Checklist

- [ ] Purchase domain (if needed)
- [ ] Add domain to hosting platform (Railway/Render/etc.)
- [ ] Configure DNS records:
  - [ ] CNAME for frontend (e.g., `www` → platform domain)
  - [ ] CNAME for backend API (e.g., `api` → platform domain)
- [ ] Wait for DNS propagation (5-30 minutes)
- [ ] Verify SSL certificate is issued (automatic on most platforms)
- [ ] Update CORS settings with production domain
- [ ] Test API connectivity from frontend
- [ ] Update frontend environment variables

---

## Post-Deployment Checklist

- [ ] Test video upload functionality
- [ ] Verify transcription works end-to-end
- [ ] Check file storage (uploads/transcripts directories)
- [ ] Monitor error logs
- [ ] Set up monitoring/alerting (optional)
- [ ] Configure backup strategy for uploaded files
- [ ] Set up rate limiting (if needed)
- [ ] Review security settings
- [ ] Test on mobile devices
- [ ] Verify HTTPS is working

---

## Cost Estimates

### Railway.app
- Free tier: 500 hours/month, $5 credit
- Paid: ~$5-20/month depending on usage
- Domain: $10-15/year (if custom)

### Render.com
- Free tier: Spins down after inactivity
- Paid: $7/month for always-on backend
- Domain: $10-15/year (if custom)

### VPS (DigitalOcean)
- Droplet: $6-12/month
- Domain: $10-15/year
- Total: ~$16-27/month

### OpenAI API Costs
- $0.006 per minute of audio
- Example: 100 hours/month = $36/month

---

## Quick Start Commands

### Railway CLI (Optional)
```bash
npm i -g @railway/cli
railway login
railway init
railway up
```

### Render CLI (Optional)
```bash
npm i -g render-cli
render login
render deploy
```

---

## Troubleshooting

### FFmpeg Not Found
- Add to Dockerfile or build command
- Railway: Use nixpacks with custom config
- Render: Use Dockerfile

### CORS Errors
- Check `ALLOWED_ORIGINS` environment variable
- Verify frontend domain is in allowed list
- Check browser console for exact error

### File Upload Issues
- Verify file size limits
- Check storage directory permissions
- Ensure sufficient disk space

### API Connection Errors
- Verify `VITE_API_URL` is set correctly
- Check backend is running and accessible
- Verify CORS settings

---

## Next Steps After Deployment

1. **Monitoring**: Set up error tracking (Sentry, LogRocket)
2. **Analytics**: Add Google Analytics or similar
3. **Backup**: Configure automated backups for uploaded files
4. **CDN**: Use Cloudflare for static assets (if needed)
5. **Rate Limiting**: Implement to prevent abuse
6. **Database**: Consider moving transcripts to database (PostgreSQL)
7. **Queue System**: Add Celery/Redis for async transcription processing

---

## Fastest Path Summary (Railway)

1. **Push code to GitHub** (5 min)
2. **Deploy backend to Railway** (10 min)
   - Connect repo → Select backend folder → Add env vars → Deploy
3. **Deploy frontend to Railway** (10 min)
   - Add service → Select frontend folder → Set build command → Deploy
4. **Domain setup** (15-30 min)
   - Add custom domain in Railway → Update DNS → Wait for propagation
5. **Update CORS** (5 min)
   - Add production domain → Redeploy

**Total Time: ~45-60 minutes**

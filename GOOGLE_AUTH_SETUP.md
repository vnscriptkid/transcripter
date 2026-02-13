# Google OAuth Setup Guide

This guide walks you through setting up Google OAuth credentials for the Video Transcriber app.

---

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top → **New Project**
3. Enter a project name (e.g. "Video Transcriber") and click **Create**
4. Make sure your new project is selected in the dropdown

---

## Step 2: Configure the OAuth Consent Screen

1. In the left sidebar, go to **APIs & Services → OAuth consent screen**
2. Choose **External** user type → click **Create**
3. Fill in the required fields:
   - **App name**: Video Transcriber
   - **User support email**: your email
   - **Developer contact information**: your email
4. Click **Save and Continue**
5. On the **Scopes** page, click **Add or Remove Scopes** and add:
   - `openid`
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`
6. Click **Update** → **Save and Continue**
7. On the **Test users** page, add your Google account email (required while in "Testing" mode)
8. Click **Save and Continue** → **Back to Dashboard**

> **Note**: In "Testing" mode only added test users can sign in. To allow any Google user, you need to publish the app (click **Publish App** on the consent screen page). For a personal/team app, staying in testing mode is fine.

---

## Step 3: Create OAuth 2.0 Credentials

1. Go to **APIs & Services → Credentials**
2. Click **Create Credentials → OAuth client ID**
3. Select **Application type: Web application**
4. Name it (e.g. "Video Transcriber Web Client")
5. Under **Authorized JavaScript origins**, add:
   - `http://localhost:5173` (Vite dev server)
   - `http://localhost:3000` (alt dev port)
   - Your production domain (e.g. `https://yourdomain.com`)
6. Click **Create**
7. A dialog shows your **Client ID** and **Client Secret**. Copy the **Client ID** — it looks like:
   ```
   123456789-abcdefghijklmnop.apps.googleusercontent.com
   ```

> **Client Secret is NOT needed** for this app. We use the Google Identity Services library which only needs the Client ID.

---

## Step 4: Configure Environment Variables

### Local Development

Create/update `backend/.env`:
```
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
JWT_SECRET_KEY=your-random-secret-key-here
```

Create `frontend/.env.local`:
```
VITE_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
```

Generate a strong JWT secret:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Production (Railway / Docker)

Set these environment variables in your deployment platform:
- `GOOGLE_CLIENT_ID` — your Google Client ID
- `JWT_SECRET_KEY` — a strong random secret (at least 32 chars)
- `VITE_GOOGLE_CLIENT_ID` — same as `GOOGLE_CLIENT_ID` (used as a Docker build arg for the frontend)

### Docker Compose

Create a `.env` file at the project root:
```
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
JWT_SECRET_KEY=your-random-secret-key-here
OPENAI_API_KEY=your-openai-key-here
```

Then run:
```bash
docker compose up --build
```

---

## Step 5: Run the Database Migration

After setting up credentials, run the Alembic migration to create the `users` table:

```bash
cd backend
alembic upgrade head
```

Or with Docker Compose:
```bash
docker compose exec backend alembic upgrade head
```

---

## Troubleshooting

**"idpiframe_initialization_failed" error in browser**
- Make sure `http://localhost:5173` is listed in Authorized JavaScript Origins
- Clear browser cookies and try again

**"Token verification failed" from backend**
- Confirm `GOOGLE_CLIENT_ID` in the backend env exactly matches what's in Google Cloud Console
- Check that the clock on your server is accurate (JWT/token validation is time-sensitive)

**"This app isn't verified" popup from Google**
- This appears in Testing mode for non-test-users. Add yourself as a test user or publish the app.

**401 errors after login**
- JWT may have expired (default 7 days). Sign out and sign back in.
- Verify `JWT_SECRET_KEY` is set and consistent (not changed between restarts in production)

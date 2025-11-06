# TG Mono-Repo Setup Guide

This mono-repository contains both the backend (FastAPI) and frontend (SvelteKit) applications for the Telegram Paid Subscriber Service platform.

## Architecture Overview

```
tg-mono-repo/
├── backend/          # FastAPI backend with cookie-based auth
│   ├── app/         # Core application logic
│   ├── routers/     # API endpoints
│   ├── config/      # Configuration management
│   └── tests/       # Backend tests
│
└── frontend/        # SvelteKit frontend with Tailwind CSS
    ├── src/
    │   ├── lib/     # Shared components and services
    │   └── routes/  # SvelteKit pages
    └── static/      # Static assets
```

## Prerequisites

- **Backend:**
  - Python 3.11+
  - MongoDB 4.4+
  - Telegram Bot Token (from @BotFather)
  - Stripe Account (for payments)

- **Frontend:**
  - Node.js 18+ or Bun
  - npm, pnpm, yarn, or bun

## Backend Setup

### 1. Navigate to Backend Directory

```bash
cd backend
```

### 2. Install Dependencies

Using pip:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Using uv (recommended):
```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set your configuration:

```env
# Required Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_WEBHOOK_SECRET_PATH=random_secret_path
BASE_URL=https://your-domain.com
MONGODB_URI=mongodb://localhost:27017/telegram

# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# JWT Configuration (generate a strong secret)
JWT_SECRET_KEY=your-very-secure-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 4. Start MongoDB

```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or use your local MongoDB installation
```

### 5. Run Backend

Development:
```bash
uvicorn main:app --reload --port 8001
```

Production:
```bash
granian --interface asgi main:app --host 0.0.0.0 --port 8001 --workers 4
```

The backend will be available at `http://localhost:8001`

### Backend API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

## Frontend Setup

### 1. Navigate to Frontend Directory

```bash
cd frontend
```

### 2. Install Dependencies

```bash
npm install
# or
bun install
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Backend API URL
VITE_API_BASE_URL=http://localhost:8001

# For production
# VITE_API_BASE_URL=https://api.yourdomain.com
```

### 4. Run Frontend

Development:
```bash
npm run dev
# or
bun dev
```

The frontend will be available at `http://localhost:5173`

### 5. Build for Production

```bash
npm run build
npm run preview
```

## Authentication Flow

This application uses **cookie-based authentication** for enhanced security:

### How It Works

1. **Registration/Login:**
   - User submits credentials to `/api/sellers/register` or `/api/sellers/login`
   - Backend validates credentials and generates JWT tokens
   - Backend sets httpOnly cookies with access and refresh tokens
   - Frontend receives response (tokens also in response for backward compatibility)

2. **Authenticated Requests:**
   - Frontend automatically sends cookies with every request (credentials: 'include')
   - Backend checks cookies first, then Authorization header, then API key
   - No need to manually manage tokens in localStorage

3. **Logout:**
   - Frontend calls `/api/sellers/logout`
   - Backend clears the cookies
   - User is redirected to login page

### Security Features

- **httpOnly cookies:** Tokens cannot be accessed by JavaScript (XSS protection)
- **SameSite:** Set to 'lax' to prevent CSRF attacks
- **Secure flag:** Should be enabled in production with HTTPS
- **Token expiration:** Access tokens expire in 30 minutes, refresh in 7 days

## Development Workflow

### Running Both Applications

In separate terminals:

```bash
# Terminal 1 - Backend
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8001

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Code Quality

**Backend:**
```bash
cd backend

# Linting
ruff check .

# Auto-fix
ruff check --fix .

# Formatting
black app routers config tests main.py

# Tests
pytest
pytest --cov=app --cov=routers --cov=config
```

**Frontend:**
```bash
cd frontend

# Linting
npm run lint

# Type checking
npm run check

# Formatting
npm run format

# Tests
npm run test:unit
npm run test:e2e
```

## CORS Configuration

The backend is pre-configured to accept requests from:
- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000` (Alternative port)
- Production domains (update in `main.py`)

For production, update the `origins` list in `backend/main.py`:

```python
origins = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]
```

## Environment-Specific Configuration

### Development
- Backend: `http://localhost:8001`
- Frontend: `http://localhost:5173`
- MongoDB: `mongodb://localhost:27017/telegram`
- Cookies: `secure=False`

### Production
- Backend: `https://api.yourdomain.com`
- Frontend: `https://yourdomain.com`
- MongoDB: Use managed service (MongoDB Atlas, etc.)
- Cookies: `secure=True`
- Update `BASE_URL` in backend `.env`
- Update `VITE_API_BASE_URL` in frontend `.env`

## Deployment

### Backend Deployment

**Using Docker:**
```bash
cd backend
docker build -t tg-backend .
docker run -d -p 8001:8001 --env-file .env tg-backend
```

**Using Docker Compose:**
```bash
cd backend
docker-compose up -d
```

### Frontend Deployment

The frontend is built as a static site and can be deployed to:
- Vercel
- Netlify
- GitHub Pages
- Any static hosting service

```bash
cd frontend
npm run build
# Upload the 'build' folder to your hosting service
```

## Troubleshooting

### Backend Issues

**MongoDB Connection Failed:**
- Ensure MongoDB is running: `docker ps` or `systemctl status mongod`
- Check `MONGODB_URI` in `.env`
- Verify network connectivity

**JWT Token Errors:**
- Ensure `JWT_SECRET_KEY` is set in `.env`
- Check cookie settings if auth fails
- Verify `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` is valid

### Frontend Issues

**API Connection Failed:**
- Verify backend is running: `curl http://localhost:8001/health`
- Check `VITE_API_BASE_URL` in `.env`
- Check browser console for CORS errors

**Authentication Not Working:**
- Check browser cookies (DevTools > Application > Cookies)
- Verify backend is setting cookies (check response headers)
- Ensure `credentials: 'include'` is set in API client

**Build Errors:**
- Clear node_modules: `rm -rf node_modules && npm install`
- Clear .svelte-kit: `rm -rf .svelte-kit && npm run dev`

## Additional Resources

- Backend API Documentation: See `backend/README.md`
- Frontend Documentation: See `frontend/README.md`
- API Reference: `http://localhost:8001/docs` (when running)
- Telegram Bot API: https://core.telegram.org/bots/api
- SvelteKit Docs: https://kit.svelte.dev
- FastAPI Docs: https://fastapi.tiangolo.com

## Support

For issues and questions:
1. Check the documentation in `backend/docs/` and `frontend/README.md`
2. Review the troubleshooting section above
3. Check existing GitHub issues
4. Open a new issue with detailed information

## License

See LICENSE file for details.

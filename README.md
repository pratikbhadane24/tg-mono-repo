# TG Mono-Repo

Full-stack monorepo for the Telegram Paid Subscriber Service platform with secure cookie-based authentication.

## 🎯 Features

- **🔐 Secure Authentication:** Cookie-based JWT authentication with httpOnly cookies
- **📊 Dashboard:** Real-time statistics and analytics
- **📡 Channel Management:** Add and manage Telegram channels
- **👥 Member Management:** View and manage channel subscribers
- **💰 Payment Integration:** Stripe integration for subscription payments
- **🔔 Webhooks:** Event notification system
- **🎨 Modern UI:** Cyberpunk-themed interface with Tailwind CSS
- **🔒 Security:** httpOnly cookies, CORS protection, JWT tokens

## 📁 Repository Structure

```
tg-mono-repo/
├── backend/          # FastAPI backend application
│   ├── app/         # Core business logic
│   ├── routers/     # API route handlers
│   ├── config/      # Configuration files
│   └── tests/       # Backend tests
│
├── frontend/        # SvelteKit frontend application
│   ├── src/
│   │   ├── lib/     # Shared components and services
│   │   └── routes/  # SvelteKit pages
│   └── static/      # Static assets
│
└── SETUP.md        # Detailed setup guide
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ (for backend)
- Node.js 18+ or Bun (for frontend)
- MongoDB 4.4+
- Telegram Bot Token
- Stripe Account (optional, for payments)

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
uvicorn main:app --reload --port 8001
```

### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
# Edit .env with your backend URL
npm run dev
```

Visit:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

## 🔑 Authentication

This application uses **cookie-based authentication** for enhanced security:

- **httpOnly cookies:** Tokens are not accessible via JavaScript
- **Automatic cookie handling:** No manual token management needed
- **CORS support:** Pre-configured for local development
- **Secure by default:** Production-ready with proper security headers

## 📚 Documentation

- **[Setup Guide](SETUP.md)** - Detailed setup and configuration
- **[Backend README](backend/README.md)** - Backend API documentation
- **[Frontend README](frontend/README.md)** - Frontend documentation
- **[API Reference](http://localhost:8001/docs)** - Interactive API docs (when running)

## 🛠️ Technology Stack

### Backend
- **Framework:** FastAPI
- **Database:** MongoDB with Motor (async driver)
- **Authentication:** JWT with httpOnly cookies
- **Payments:** Stripe
- **Telegram:** Telegram Bot API
- **Server:** Uvicorn / Granian

### Frontend
- **Framework:** SvelteKit 5 (with Svelte 5 Runes)
- **Language:** TypeScript
- **Styling:** Tailwind CSS 4
- **Build Tool:** Vite 7
- **Testing:** Vitest + Playwright
- **Linting:** ESLint + Prettier

## 🔒 Security Features

- **httpOnly Cookies:** Prevents XSS attacks
- **CORS Protection:** Configured allowed origins
- **SameSite Cookies:** CSRF protection
- **JWT Tokens:** Short-lived access tokens
- **Password Hashing:** bcrypt for secure password storage
- **API Key Support:** Alternative authentication for programmatic access

## 🎨 UI Features

- **Cyberpunk 2077 Theme:** Modern, futuristic design
- **Responsive:** Mobile-friendly interface
- **Accessible:** ARIA labels and keyboard navigation
- **Loading States:** Visual feedback for async operations
- **Error Handling:** User-friendly error messages

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest
pytest --cov=app --cov=routers --cov=config
```

### Frontend Tests

```bash
cd frontend
npm run test:unit
npm run test:e2e
```

## 📦 Deployment

### Backend

```bash
cd backend
docker build -t tg-backend .
docker run -d -p 8001:8001 --env-file .env tg-backend
```

Or use Docker Compose:
```bash
docker-compose up -d
```

### Frontend

```bash
cd frontend
npm run build
# Deploy the 'build' folder to your hosting service
```

Recommended hosting:
- Vercel
- Netlify
- GitHub Pages
- Any static hosting service

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run linters and tests
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

See LICENSE file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [SvelteKit](https://kit.svelte.dev)
- [Tailwind CSS](https://tailwindcss.com/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Stripe](https://stripe.com/)

## 📧 Support

For issues and questions:
1. Check the [Setup Guide](SETUP.md)
2. Review the [API Documentation](http://localhost:8001/docs)
3. Open a GitHub issue

---

Built with ❤️ using FastAPI and SvelteKit

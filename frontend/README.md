# TG Seller Frontend

A cyberpunk-themed frontend application for the Telegram Paid Subscriber Service platform. Built with SvelteKit 5, TypeScript, and Tailwind CSS.

## Features

- 🎨 **Cyberpunk 2077 Themed UI** - Futuristic neon design with glowing effects
- 🔐 **Complete Authentication** - Login and registration with JWT token management
- 📊 **Dashboard** - Real-time statistics and quick actions
- 📡 **Channel Management** - Add, view, and manage Telegram channels
- 👥 **Member Management** - View, filter, and remove channel subscribers
- 💰 **Payment History** - Track revenue and payment transactions
- 🔑 **Grant Access** - Manually grant channel access to users
- ⚙️ **Settings** - Configure Stripe integration, webhooks, and profile

## Tech Stack

- **Framework**: SvelteKit 5 with Svelte 5 (Runes API)
- **Language**: TypeScript
- **Styling**: Tailwind CSS 4 with custom cyberpunk theme
- **Build Tool**: Vite 7
- **Linting**: ESLint with TypeScript support
- **Formatting**: Prettier
- **Testing**: Vitest + Playwright
- **Storybook**: Component development and documentation

## Prerequisites

- Node.js 18+ or Bun
- npm, pnpm, yarn, or bun

## Installation

1. Clone the repository:

```sh
git clone https://github.com/pratikbhadane24/tg-seller-frontend.git
cd tg-seller-frontend
```

2. Install dependencies:

```sh
npm install
```

3. Configure environment variables:

```sh
cp .env.example .env
```

Edit `.env` and set your backend API URL:

```env
VITE_API_BASE_URL=http://localhost:8001
```

## Development

Start the development server:

```sh
npm run dev

# or start the server and open the app in a new browser tab
npm run dev -- --open
```

The app will be available at `http://localhost:5173`.

## Building

To create a production build:

```sh
npm run build
```

Preview the production build locally:

```sh
npm run preview
```

## Code Quality

### Linting

```sh
npm run lint
```

### Formatting

```sh
npm run format
```

### Type Checking

```sh
npm run check
```

## Testing

### Unit Tests

```sh
npm run test:unit
```

### E2E Tests

```sh
npm run test:e2e
```

### All Tests

```sh
npm run test
```

## Storybook

Run Storybook for component development:

```sh
npm run storybook
```

Build Storybook:

```sh
npm run build-storybook
```

## Project Structure

```
src/
├── lib/
│   ├── components/       # Reusable UI components
│   │   ├── Button.svelte
│   │   ├── Input.svelte
│   │   ├── Loading.svelte
│   │   ├── Navigation.svelte
│   │   └── StatCard.svelte
│   ├── services/         # API service layer
│   │   ├── api.ts
│   │   ├── auth.service.ts
│   │   ├── channel.service.ts
│   │   ├── member.service.ts
│   │   ├── payment.service.ts
│   │   └── webhook.service.ts
│   ├── types/            # TypeScript type definitions
│   │   └── api.ts
│   └── utils/            # Utility functions
│       ├── format.ts
│       └── navigation.ts
├── routes/               # SvelteKit pages
│   ├── +page.svelte      # Home (redirects to dashboard/login)
│   ├── +layout.svelte    # Root layout
│   ├── login/            # Login page
│   ├── register/         # Registration page
│   ├── dashboard/        # Dashboard page
│   ├── channels/         # Channel management
│   ├── members/          # Member management
│   ├── payments/         # Payment history
│   ├── grant-access/     # Grant access page
│   └── settings/         # Settings page
└── app.css               # Global styles and cyberpunk theme
```

## API Integration

The frontend integrates with the Telegram Paid Subscriber Service backend API. See the `references/backend/docs/` directory for complete API documentation.

### Authentication

- JWT token-based authentication
- Automatic token refresh
- Protected routes with automatic redirect to login

### API Services

All API calls are handled through service modules:

- `authService` - Authentication and seller profile
- `channelService` - Channel management
- `memberService` - Member management and access granting
- `paymentService` - Payment history
- `webhookService` - Webhook configuration

### Standard Response Format

All API responses follow this format:

```typescript
{
  success: boolean;
  message: string;
  data: T | null;
  error?: {
    code: string;
    description: string;
  };
}
```

## Cyberpunk Theme

The application features a custom Cyberpunk 2077-inspired theme with:

- Neon colors (blue, pink, purple, yellow, green)
- Glowing effects and animations
- Scan line effects
- Custom scrollbars
- Smooth transitions
- Dark color scheme

### Theme Variables

```css
--cyber-yellow: #fcee0a --cyber-blue: #00f0ff --cyber-pink: #ff2a6d --cyber-purple: #b429f9
	--cyber-red: #ff003c --cyber-green: #05ffa1;
```

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Deployment

The app is configured with `@sveltejs/adapter-static` for static site deployment. You can deploy to:

- Vercel
- Netlify
- GitHub Pages
- Any static hosting service

### Build Configuration

The app uses a fallback `index.html` for client-side routing. This is configured in `svelte.config.js`:

```javascript
adapter: adapter({
	fallback: 'index.html'
});
```

## License

See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure all tests pass and code is formatted
5. Submit a pull request

## Support

For issues and questions, please open an issue on GitHub.

# Frontend Agent Instructions (React/Next.js/TypeScript)

## Must-Have Requirements

### 1. Project Structure (MANDATORY)

**ALL frontend applications MUST follow this structure:**

```
frontend/
├── src/
│   ├── app/                    # Next.js app directory (Next.js 13+)
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Home page
│   │   ├── api/                # API routes (if needed)
│   │   └── [feature]/          # Feature-based routes
│   │       ├── page.tsx
│   │       └── layout.tsx
│   ├── components/             # Reusable components
│   │   ├── ui/                 # Base UI components (REQUIRED)
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── card.tsx
│   │   │   └── ...
│   │   ├── layout/             # Layout components
│   │   │   ├── header.tsx
│   │   │   ├── footer.tsx
│   │   │   └── sidebar.tsx
│   │   └── [feature]/          # Feature-specific components
│   ├── lib/                    # Utility libraries (REQUIRED)
│   │   ├── api.ts              # API client
│   │   ├── utils.ts            # Utility functions
│   │   ├── validators.ts       # Input validation
│   │   └── constants.ts        # Constants
│   ├── hooks/                  # Custom React hooks
│   │   ├── useAuth.ts          # Authentication hook (if auth)
│   │   ├── useApi.ts           # API hook
│   │   └── use[Feature].ts     # Feature hooks
│   ├── services/               # API services (REQUIRED)
│   │   ├── auth.service.ts     # Auth service
│   │   └── [domain].service.ts # Domain services
│   ├── types/                  # TypeScript types (REQUIRED)
│   │   ├── api.types.ts        # API types
│   │   ├── models.types.ts     # Data models
│   │   └── common.types.ts     # Common types
│   ├── context/                # React Context providers
│   │   ├── AuthContext.tsx     # Auth context
│   │   └── ThemeContext.tsx    # Theme context
│   ├── styles/                 # Global styles
│   │   └── globals.css
│   └── config/                 # Configuration (REQUIRED)
│       ├── env.ts              # Environment config
│       └── constants.ts        # App constants
├── public/                     # Static assets
│   ├── images/
│   └── fonts/
├── tests/                      # Test files (REQUIRED)
│   ├── setup.ts                # Test setup
│   ├── components/             # Component tests
│   ├── hooks/                  # Hook tests
│   ├── integration/            # Integration tests
│   └── e2e/                    # E2E tests
├── .env.example                # Environment template (REQUIRED)
├── package.json                # Dependencies (REQUIRED)
├── tsconfig.json               # TypeScript config (REQUIRED)
├── next.config.js              # Next.js config
├── tailwind.config.js          # Tailwind config
├── jest.config.js              # Jest config (REQUIRED)
├── playwright.config.ts        # E2E config (if E2E tests)
└── README.md                   # Documentation (REQUIRED)
```

**If structure is missing, STOP and create it first.**

### 2. TypeScript Configuration (REQUIRED)

**ALL frontend apps MUST use TypeScript with strict mode:**

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["DOM", "DOM.Iterable", "ES2020"],
    "jsx": "preserve",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@/components/*": ["./src/components/*"],
      "@/lib/*": ["./src/lib/*"],
      "@/hooks/*": ["./src/hooks/*"],
      "@/types/*": ["./src/types/*"]
    }
  }
}
```

**No `any` types allowed. Use proper typing.**

### 3. Environment Configuration (REQUIRED)

```typescript
// src/config/env.ts
const requiredEnvVars = [
  'NEXT_PUBLIC_API_URL',
  'NEXT_PUBLIC_APP_NAME',
] as const;

// Validate environment variables
requiredEnvVars.forEach(key => {
  if (!process.env[key]) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
});

export const env = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL!,
  appName: process.env.NEXT_PUBLIC_APP_NAME!,
  isDevelopment: process.env.NODE_ENV === 'development',
  isProduction: process.env.NODE_ENV === 'production',
} as const;
```

**.env.example MUST include ALL variables:**

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=My App

# Optional
NEXT_PUBLIC_ENABLE_ANALYTICS=false
```

### 4. API Client (REQUIRED)

**ALL API calls MUST go through a centralized client:**

```typescript
// src/lib/api.ts
import { env } from '@/config/env';

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T | null;
  error?: {
    code: string;
    description: string;
  };
}

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  setToken(token: string) {
    this.token = token;
  }

  clearToken() {
    this.token = null;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Request failed');
      }

      return data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, body: unknown): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  async put<T>(endpoint: string, body: unknown): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const apiClient = new ApiClient(env.apiUrl);
```

### 5. Authentication (REQUIRED if app has auth)

```typescript
// src/hooks/useAuth.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { apiClient } from '@/lib/api';

interface User {
  id: string;
  username: string;
  email: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: async (username: string, password: string) => {
        const response = await apiClient.post('/auth/login', {
          username,
          password,
        });

        if (response.success && response.data) {
          const { user, token } = response.data;
          apiClient.setToken(token);
          set({ user, token, isAuthenticated: true });
        }
      },

      logout: () => {
        apiClient.clearToken();
        set({ user: null, token: null, isAuthenticated: false });
      },

      checkAuth: async () => {
        const { token } = get();
        if (!token) return;

        try {
          apiClient.setToken(token);
          const response = await apiClient.get('/auth/me');
          if (response.success && response.data) {
            set({ user: response.data, isAuthenticated: true });
          }
        } catch {
          get().logout();
        }
      },
    }),
    {
      name: 'auth-storage',
    }
  )
);
```

**Protected routes:**

```typescript
// src/components/ProtectedRoute.tsx
'use client';

import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
```

### 6. Component Standards (REQUIRED)

**ALL components MUST:**

1. Use TypeScript with proper types
2. Follow naming conventions
3. Have proper props interfaces
4. Handle loading/error states
5. Be tested

```typescript
// src/components/ui/button.tsx
import { ButtonHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'button',
          variant,
          size,
          className
        )}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? 'Loading...' : children}
      </button>
    );
  }
);

Button.displayName = 'Button';
```

### 7. Testing (CRITICAL - NON-NEGOTIABLE)

**Testing is MANDATORY. Minimum 80% coverage required.**

#### Test Structure:

```
tests/
├── setup.ts                 # Jest/Vitest setup
├── components/
│   ├── ui/
│   │   └── button.test.tsx  # Component tests
│   └── [feature]/
├── hooks/
│   └── useAuth.test.ts      # Hook tests
├── integration/
│   └── auth-flow.test.tsx   # Integration tests
└── e2e/
    └── login.spec.ts        # E2E tests (Playwright)
```

#### Component Tests (REQUIRED):

```typescript
// tests/components/ui/button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '@/components/ui/button';

describe('Button', () => {
  it('renders children correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('shows loading state', () => {
    render(<Button isLoading>Click me</Button>);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Click me</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

#### Hook Tests (REQUIRED):

```typescript
// tests/hooks/useAuth.test.ts
import { renderHook, act } from '@testing-library/react';
import { useAuth } from '@/hooks/useAuth';

describe('useAuth', () => {
  it('initializes with unauthenticated state', () => {
    const { result } = renderHook(() => useAuth());
    
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it('logs in user successfully', async () => {
    const { result } = renderHook(() => useAuth());
    
    await act(async () => {
      await result.current.login('testuser', 'password');
    });
    
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toBeDefined();
  });

  it('logs out user', async () => {
    const { result } = renderHook(() => useAuth());
    
    await act(async () => {
      await result.current.login('testuser', 'password');
      result.current.logout();
    });
    
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });
});
```

#### E2E Tests (REQUIRED for critical flows):

```typescript
// tests/e2e/login.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Login Flow', () => {
  test('should login successfully with valid credentials', async ({ page }) => {
    await page.goto('/login');
    
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    
    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByText('Welcome')).toBeVisible();
  });

  test('should show error with invalid credentials', async ({ page }) => {
    await page.goto('/login');
    
    await page.fill('input[name="username"]', 'wronguser');
    await page.fill('input[name="password"]', 'wrongpass');
    await page.click('button[type="submit"]');
    
    await expect(page.getByText('Invalid credentials')).toBeVisible();
  });
});
```

#### Test Configuration:

```javascript
// jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.tsx',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};
```

**Minimum Requirements:**
- ✅ 80%+ code coverage
- ✅ ALL components tested
- ✅ ALL hooks tested
- ✅ Critical user flows have E2E tests
- ✅ Error states tested
- ✅ Loading states tested

### 8. Error Handling (REQUIRED)

**ALL components MUST handle errors:**

```typescript
// src/components/DataComponent.tsx
'use client';

import { useEffect, useState } from 'react';

export function DataComponent() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get('/data');
      setData(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!data) return <div>No data available</div>;

  return <div>{/* Render data */}</div>;
}
```

### 9. Performance (REQUIRED)

**MUST implement:**

1. **Code Splitting**
```typescript
import dynamic from 'next/dynamic';

const HeavyComponent = dynamic(() => import('@/components/HeavyComponent'), {
  loading: () => <div>Loading...</div>,
});
```

2. **Image Optimization**
```typescript
import Image from 'next/image';

<Image
  src="/image.jpg"
  alt="Description"
  width={800}
  height={600}
  priority={false}
/>
```

3. **Memoization**
```typescript
import { useMemo, useCallback } from 'react';

const expensiveValue = useMemo(() => computeExpensive(data), [data]);
const handleClick = useCallback(() => doSomething(), []);
```

### 10. Accessibility (REQUIRED)

**ALL components MUST be accessible:**

```typescript
<button
  aria-label="Close dialog"
  aria-pressed={isOpen}
  onClick={handleClick}
>
  X
</button>

<input
  aria-describedby="error-message"
  aria-invalid={hasError}
/>

<div role="alert" id="error-message">
  {errorMessage}
</div>
```

## Checklist for Every Frontend Task

- [ ] Proper directory structure
- [ ] TypeScript strict mode enabled
- [ ] Environment configuration with .env.example
- [ ] Centralized API client
- [ ] Authentication (if needed)
- [ ] **ALL components tested (80%+ coverage)**
- [ ] **ALL hooks tested**
- [ ] **E2E tests for critical flows**
- [ ] Error handling on all data fetching
- [ ] Loading states
- [ ] Accessibility attributes
- [ ] Performance optimization
- [ ] Code splitting for heavy components
- [ ] ESLint passes
- [ ] TypeScript compiles without errors
- [ ] No console errors/warnings

## Common Mistakes to Avoid

❌ **NEVER:**
- Use JavaScript instead of TypeScript
- Use `any` type
- Skip component tests
- Have <80% test coverage
- Fetch data in components without error handling
- Skip loading states
- Ignore accessibility
- Use inline API calls (must use API client)
- Hardcode API URLs

✅ **ALWAYS:**
- Use TypeScript with strict mode
- Test components thoroughly
- Handle loading/error states
- Use centralized API client
- Follow accessibility guidelines
- Optimize performance
- Use proper TypeScript types
- Test critical user flows with E2E

## If Something is Missing

**STOP IMMEDIATELY and:**
1. Identify missing requirement
2. Inform user clearly
3. Add missing component
4. Test thoroughly
5. Update documentation
6. Verify checklist

**Quality and testing are non-negotiable.**

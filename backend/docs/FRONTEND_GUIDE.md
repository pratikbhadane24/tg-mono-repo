# Frontend Development Guide - Telegram Paid Subscriber Service

**Complete Framework-Agnostic Frontend Development Guide**

This guide provides everything a frontend developer needs to build a complete seller management interface for the Telegram Paid Subscriber Service platform.

## Table of Contents

- [Overview](#overview)
- [Authentication Flow](#authentication-flow)
- [API Integration](#api-integration)
- [UI Components Guide](#ui-components-guide)
- [Page Specifications](#page-specifications)
- [State Management](#state-management)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Testing Guidelines](#testing-guidelines)

---

## Overview

### What You're Building

A complete **seller dashboard** that allows sellers to:
1. Register and login to their account
2. Manage their Telegram channels
3. View statistics and analytics
4. Manage customer subscriptions
5. Handle payments (via Stripe)
6. Configure webhooks
7. View payment history

### Tech Stack Requirements

**Required:**
- Modern JavaScript/TypeScript
- HTTP client (fetch API, axios, etc.)
- State management solution of your choice
- Router for navigation
- Form handling library (optional but recommended)

**Recommended:**
- TypeScript for type safety
- Token storage solution (localStorage/sessionStorage)
- Toast/notification library
- Data table component
- Chart library for analytics

### API Base URL

All API calls should be made to:
```
Production: https://your-domain.com
Development: http://localhost:8001
```

---

## Authentication Flow

### Authentication Methods

The API supports TWO authentication methods:

#### 1. JWT Bearer Token (Recommended for Web UI)
```http
Authorization: Bearer eyJhbGci...
```

#### 2. API Key (For Server-Side/Automation)
```http
X-API-Key: sk_abc123...
```

### Complete Authentication Implementation

#### Step 1: Registration

**Endpoint:** `POST /api/sellers/register`

**Request:**
```json
{
  "email": "seller@example.com",
  "password": "SecurePassword123!",
  "company_name": "My Company"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Seller registered successfully",
  "data": {
    "seller_id": "507f1f77bcf86cd799439011",
    "email": "seller@example.com",
    "api_key": "sk_abc123xyz..."
  }
}
```

**Response (Error):**
```json
{
  "success": false,
  "message": "Email already registered",
  "data": null,
  "error": {
    "code": "REGISTRATION_FAILED",
    "description": "Email already registered"
  }
}
```

**Frontend Implementation:**
```javascript
async function registerSeller(email, password, companyName) {
  try {
    const response = await fetch('${API_BASE_URL}/api/sellers/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email,
        password,
        company_name: companyName
      })
    });
    
    const result = await response.json();
    
    if (result.success) {
      // Store API key securely
      localStorage.setItem('api_key', result.data.api_key);
      // Proceed to login or dashboard
      return { success: true, data: result.data };
    } else {
      // Handle error
      return { success: false, error: result.error };
    }
  } catch (error) {
    return { success: false, error: { message: 'Network error' } };
  }
}
```

#### Step 2: Login

**Endpoint:** `POST /api/sellers/login`

**Request:**
```json
{
  "email": "seller@example.com",
  "password": "SecurePassword123!"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "token_type": "bearer"
  }
}
```

**Frontend Implementation:**
```javascript
async function loginSeller(email, password) {
  try {
    const response = await fetch('${API_BASE_URL}/api/sellers/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email, password })
    });
    
    const result = await response.json();
    
    if (result.success) {
      // Store tokens securely
      localStorage.setItem('access_token', result.data.access_token);
      localStorage.setItem('refresh_token', result.data.refresh_token);
      localStorage.setItem('token_type', result.data.token_type);
      
      // Redirect to dashboard
      return { success: true };
    } else {
      return { success: false, error: result.error || result.message };
    }
  } catch (error) {
    return { success: false, error: 'Network error' };
  }
}
```

#### Step 3: Authenticated Requests

**All subsequent API calls must include authentication header:**

```javascript
function getAuthHeaders() {
  const token = localStorage.getItem('access_token');
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  };
}

// Example: Fetch seller profile
async function getSellerProfile() {
  const response = await fetch('${API_BASE_URL}/api/sellers/me', {
    headers: getAuthHeaders()
  });
  return await response.json();
}
```

#### Step 4: Token Management

**Handle Token Expiration:**
```javascript
async function makeAuthenticatedRequest(url, options = {}) {
  const headers = getAuthHeaders();
  
  const response = await fetch(url, {
    ...options,
    headers: { ...headers, ...options.headers }
  });
  
  // Handle 401 Unauthorized
  if (response.status === 401) {
    // Token expired - redirect to login
    localStorage.clear();
    window.location.href = '/login';
    return null;
  }
  
  return await response.json();
}
```

---

## API Integration

### Standard Response Format

**ALL API responses follow this format:**

```typescript
interface StandardResponse<T> {
  success: boolean;
  message: string;
  data: T | null;
  error?: {
    code: string;
    description: string;
  };
}
```

### Complete API Reference

#### Seller Management APIs

**1. Get Seller Profile**
```http
GET /api/sellers/me
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "message": "Seller information retrieved",
  "data": {
    "id": "507f1f77bcf86cd799439011",
    "email": "seller@example.com",
    "company_name": "My Company",
    "is_active": true,
    "is_verified": false,
    "subscription_status": "active",
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-15T10:30:00Z"
  }
}
```

**2. Update Stripe Keys**
```http
POST /api/sellers/stripe-keys
Authorization: Bearer {token}
Content-Type: application/json

{
  "publishable_key": "pk_live_...",
  "secret_key": "sk_live_..."
}
```

**3. Get Dashboard Statistics**
```http
GET /api/sellers/stats
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "message": "Statistics retrieved successfully",
  "data": {
    "total_channels": 3,
    "active_members": 142,
    "total_members": 150,
    "total_revenue_cents": 698600,
    "total_revenue_dollars": 6986.00
  }
}
```

#### Channel Management APIs

**1. Add Channel**
```http
POST /api/telegram/channels
Authorization: Bearer {token}
Content-Type: application/json

{
  "chat_id": -1001234567890,
  "name": "Premium Channel",
  "join_model": "invite_link"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Channel added successfully and linked to your account.",
  "data": {
    "chat_id": -1001234567890,
    "stored_chat_id": -1001234567890,
    "name": "Premium Channel",
    "join_model": "invite_link",
    "checks": {
      "bot_id": 123456789,
      "chat_found": true,
      "is_admin": true,
      "permissions": {
        "can_invite_users": true,
        "can_manage_chat": true,
        "can_restrict_members": true
      }
    }
  }
}
```

**2. List Channels**
```http
GET /api/sellers/channels
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "message": "Found 3 channel(s)",
  "data": [
    {
      "id": "507f1f77bcf86cd799439012",
      "chat_id": -1001234567890,
      "name": "Premium Channel",
      "description": "Trading signals",
      "price_per_month": 4900,
      "total_members": 150,
      "active_members": 142,
      "is_active": true
    }
  ]
}
```

**3. Update Channel**
```http
POST /api/sellers/channels
Authorization: Bearer {token}
Content-Type: application/json

{
  "chat_id": -1001234567890,
  "name": "Updated Name",
  "description": "New description",
  "price_per_month": 5900
}
```

#### Member Management APIs

**1. List Members**
```http
GET /api/sellers/members?chat_id=-1001234567890&status=active
Authorization: Bearer {token}
```

**Query Parameters:**
- `chat_id` (optional): Filter by specific channel
- `status` (optional): active | cancelled | expired

**Response:**
```json
{
  "success": true,
  "message": "Found 142 member(s)",
  "data": [
    {
      "membership": {
        "_id": "507f1f77bcf86cd799439013",
        "user_id": "507f1f77bcf86cd799439011",
        "chat_id": -1001234567890,
        "status": "active",
        "current_period_end": "2024-02-01T00:00:00Z",
        "created_at": "2024-01-01T00:00:00Z"
      },
      "user": {
        "_id": "507f1f77bcf86cd799439011",
        "ext_user_id": "user123",
        "telegram_user_id": 123456789,
        "telegram_username": "johndoe",
        "created_at": "2024-01-01T00:00:00Z"
      }
    }
  ]
}
```

**2. Force Remove Member**
```http
POST /api/telegram/force-remove
Authorization: Bearer {token}
Content-Type: application/json

{
  "ext_user_id": "user123",
  "chat_id": -1001234567890,
  "reason": "Policy violation",
  "dry_run": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "User removed from chat. Membership expired: true",
  "data": {
    "removed": true,
    "expired_membership": true,
    "details": {
      "telegram_user_id": 123456789,
      "membership_found": true
    }
  }
}
```

#### Payment APIs

**1. Create Checkout Session**
```http
POST /api/payments/checkout
Authorization: Bearer {token}
Content-Type: application/json

{
  "price_id": "price_1234567890",
  "success_url": "https://myapp.com/success",
  "cancel_url": "https://myapp.com/cancel",
  "customer_email": "customer@example.com",
  "metadata": {
    "channel_id": "507f1f77bcf86cd799439012"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Checkout session created",
  "data": {
    "session_id": "cs_test_...",
    "url": "https://checkout.stripe.com/c/pay/cs_test_..."
  }
}
```

**2. Get Payment History**
```http
GET /api/sellers/payments?limit=50
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "message": "Found 15 payment(s)",
  "data": [
    {
      "id": "507f1f77bcf86cd799439015",
      "amount": 4900,
      "currency": "usd",
      "status": "succeeded",
      "stripe_payment_intent_id": "pi_...",
      "used_seller_stripe": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Customer Access APIs

**1. Grant Access**
```http
POST /api/telegram/grant-access
Authorization: Bearer {token}
Content-Type: application/json

{
  "ext_user_id": "customer_12345",
  "chat_ids": [-1001234567890],
  "period_days": 30,
  "ref": "payment_abc123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Access granted until 2024-02-14 23:59:59 UTC",
  "data": {
    "user_id": "507f1f77bcf86cd799439011",
    "invites": {
      "-1001234567890": "https://t.me/+abc123xyz"
    },
    "period_end": "2024-02-14T23:59:59Z",
    "errors": null
  }
}
```

#### Webhook APIs

**1. Create Webhook**
```http
POST /api/sellers/webhooks
Authorization: Bearer {token}
Content-Type: application/json

{
  "url": "https://myapp.com/webhooks/telegram",
  "events": [
    "member.joined",
    "member.left",
    "payment.succeeded",
    "subscription.expired"
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Webhook created successfully",
  "data": {
    "webhook_id": "507f1f77bcf86cd799439014",
    "url": "https://myapp.com/webhooks/telegram",
    "secret": "whsec_abc123...",
    "events": ["member.joined", "member.left", "payment.succeeded", "subscription.expired"]
  }
}
```

**2. List Webhooks**
```http
GET /api/sellers/webhooks
Authorization: Bearer {token}
```

---

## UI Components Guide

### 1. Login/Register Forms

**Registration Form Fields:**
```javascript
{
  email: {
    type: 'email',
    required: true,
    validation: 'Valid email format'
  },
  password: {
    type: 'password',
    required: true,
    minLength: 8,
    validation: 'At least 8 characters'
  },
  company_name: {
    type: 'text',
    required: false
  }
}
```

**Login Form Fields:**
```javascript
{
  email: {
    type: 'email',
    required: true
  },
  password: {
    type: 'password',
    required: true
  }
}
```

### 2. Dashboard Components

**Stats Cards Component:**
```javascript
// Display these metrics prominently
const statsCards = [
  {
    title: 'Total Channels',
    value: stats.total_channels,
    icon: 'channel-icon',
    color: 'blue'
  },
  {
    title: 'Active Members',
    value: stats.active_members,
    icon: 'users-icon',
    color: 'green'
  },
  {
    title: 'Total Revenue',
    value: `$${stats.total_revenue_dollars.toFixed(2)}`,
    icon: 'dollar-icon',
    color: 'purple'
  },
  {
    title: 'All-Time Members',
    value: stats.total_members,
    icon: 'growth-icon',
    color: 'orange'
  }
];
```

### 3. Channel Management Components

**Channel List Table:**
```javascript
// Table columns
const channelColumns = [
  {
    key: 'name',
    title: 'Channel Name',
    sortable: true
  },
  {
    key: 'chat_id',
    title: 'Chat ID'
  },
  {
    key: 'active_members',
    title: 'Active Members',
    sortable: true,
    render: (value) => `${value} members`
  },
  {
    key: 'price_per_month',
    title: 'Monthly Price',
    render: (value) => value ? `$${(value / 100).toFixed(2)}` : 'Free'
  },
  {
    key: 'is_active',
    title: 'Status',
    render: (value) => value ? 'Active' : 'Inactive'
  },
  {
    key: 'actions',
    title: 'Actions',
    render: (_, channel) => [
      { label: 'View', action: () => viewChannel(channel) },
      { label: 'Edit', action: () => editChannel(channel) },
      { label: 'Delete', action: () => deleteChannel(channel) }
    ]
  }
];
```

**Add Channel Form:**
```javascript
const addChannelForm = {
  chat_id: {
    type: 'number',
    required: true,
    label: 'Telegram Chat ID',
    placeholder: '-1001234567890',
    help: 'Use @getidsbot to get your channel ID'
  },
  name: {
    type: 'text',
    required: true,
    label: 'Channel Name',
    placeholder: 'Premium Signals'
  },
  description: {
    type: 'textarea',
    required: false,
    label: 'Description'
  },
  price_per_month: {
    type: 'number',
    required: false,
    label: 'Monthly Price (USD)',
    step: 0.01,
    transform: (value) => value * 100 // Convert to cents
  }
};
```

### 4. Member Management Components

**Member List Table:**
```javascript
const memberColumns = [
  {
    key: 'telegram_username',
    title: 'Username',
    render: (username) => username ? `@${username}` : 'N/A'
  },
  {
    key: 'telegram_user_id',
    title: 'Telegram ID'
  },
  {
    key: 'status',
    title: 'Status',
    render: (status) => ({
      active: { label: 'Active', color: 'green' },
      cancelled: { label: 'Cancelled', color: 'orange' },
      expired: { label: 'Expired', color: 'red' }
    }[status])
  },
  {
    key: 'current_period_end',
    title: 'Expires',
    render: (date) => new Date(date).toLocaleDateString()
  },
  {
    key: 'actions',
    title: 'Actions',
    render: (_, member) => [
      { 
        label: 'Remove', 
        action: () => removeMember(member),
        confirm: 'Are you sure you want to remove this member?',
        color: 'red'
      }
    ]
  }
];
```

**Member Filters:**
```javascript
const memberFilters = {
  channel: {
    type: 'select',
    label: 'Filter by Channel',
    options: channels.map(ch => ({
      value: ch.chat_id,
      label: ch.name
    }))
  },
  status: {
    type: 'select',
    label: 'Filter by Status',
    options: [
      { value: 'all', label: 'All' },
      { value: 'active', label: 'Active' },
      { value: 'cancelled', label: 'Cancelled' },
      { value: 'expired', label: 'Expired' }
    ]
  }
};
```

### 5. Payment Components

**Payment History Table:**
```javascript
const paymentColumns = [
  {
    key: 'created_at',
    title: 'Date',
    render: (date) => new Date(date).toLocaleString()
  },
  {
    key: 'amount',
    title: 'Amount',
    render: (amount) => `$${(amount / 100).toFixed(2)}`
  },
  {
    key: 'currency',
    title: 'Currency',
    render: (curr) => curr.toUpperCase()
  },
  {
    key: 'status',
    title: 'Status',
    render: (status) => ({
      succeeded: { label: 'Succeeded', color: 'green' },
      pending: { label: 'Pending', color: 'orange' },
      failed: { label: 'Failed', color: 'red' },
      refunded: { label: 'Refunded', color: 'gray' }
    }[status])
  },
  {
    key: 'used_seller_stripe',
    title: 'Payment Method',
    render: (usedSellerStripe) => usedSellerStripe ? 'Your Stripe' : 'Platform'
  }
];
```

### 6. Settings Components

**Stripe Configuration Form:**
```javascript
const stripeConfigForm = {
  publishable_key: {
    type: 'text',
    required: true,
    label: 'Stripe Publishable Key',
    placeholder: 'pk_live_...',
    pattern: '^pk_(live|test)_[a-zA-Z0-9]+$'
  },
  secret_key: {
    type: 'password',
    required: true,
    label: 'Stripe Secret Key',
    placeholder: 'sk_live_...',
    pattern: '^sk_(live|test)_[a-zA-Z0-9]+$',
    help: 'Your secret key is encrypted and never shown'
  }
};
```

**Webhook Configuration Form:**
```javascript
const webhookConfigForm = {
  url: {
    type: 'url',
    required: true,
    label: 'Webhook URL',
    placeholder: 'https://myapp.com/webhooks/telegram',
    validation: 'Must be a valid HTTPS URL'
  },
  events: {
    type: 'checkbox-group',
    required: true,
    label: 'Events to Subscribe',
    options: [
      { value: 'member.joined', label: 'Member Joined' },
      { value: 'member.left', label: 'Member Left' },
      { value: 'payment.succeeded', label: 'Payment Succeeded' },
      { value: 'subscription.expired', label: 'Subscription Expired' }
    ]
  }
};
```

---

## Page Specifications

### 1. Login Page (`/login`)

**URL:** `/login`

**Purpose:** Seller authentication

**Components:**
- Login form (email + password)
- "Forgot password" link (future feature)
- "Register" link → `/register`
- Error message display

**API Calls:**
- `POST /api/sellers/login`

**Success Action:**
- Store tokens in localStorage
- Redirect to `/dashboard`

**Error Handling:**
- Display error message
- Clear password field
- Focus on email field

### 2. Register Page (`/register`)

**URL:** `/register`

**Purpose:** New seller onboarding

**Components:**
- Registration form (email + password + company_name)
- Password strength indicator
- Terms of service checkbox
- "Already have an account?" link → `/login`

**API Calls:**
- `POST /api/sellers/register`

**Success Action:**
- Store API key
- Show success message
- Auto-login or redirect to `/login`

**Validation:**
- Email format
- Password minimum 8 characters
- Company name optional

### 3. Dashboard Page (`/dashboard`)

**URL:** `/dashboard`

**Purpose:** Overview and statistics

**Components:**
- 4 stat cards (channels, members, revenue, total)
- Recent activity list
- Quick action buttons
- Revenue chart (optional)

**API Calls:**
- `GET /api/sellers/stats`
- `GET /api/sellers/me`

**Data Refresh:**
- On page load
- Every 60 seconds (auto-refresh)
- Manual refresh button

### 4. Channels Page (`/channels`)

**URL:** `/channels`

**Purpose:** Manage Telegram channels

**Components:**
- Channel list table
- "Add Channel" button
- Search/filter bar
- Sort options

**API Calls:**
- `GET /api/sellers/channels`
- `POST /api/telegram/channels` (add new)

**Actions:**
- Add channel (open modal)
- View channel details
- Edit channel
- Delete/deactivate channel

**Add Channel Modal:**
- Chat ID input (with help text)
- Channel name input
- Description textarea
- Price input (optional)
- Submit button
- Error display

### 5. Members Page (`/members`)

**URL:** `/members`

**Purpose:** View and manage subscribers

**Components:**
- Member list table
- Channel filter dropdown
- Status filter dropdown
- Search by username/ID
- Pagination

**API Calls:**
- `GET /api/sellers/members?chat_id={id}&status={status}`
- `POST /api/telegram/force-remove` (remove member)

**Actions:**
- Filter by channel
- Filter by status
- Search members
- Remove member (with confirmation)
- View member details

**Remove Member Confirmation:**
```
Title: Remove Member
Message: Are you sure you want to remove @username from {channel_name}?
Reason: [text input - optional]
Buttons: [Cancel] [Remove]
```

### 6. Payments Page (`/payments`)

**URL:** `/payments`

**Purpose:** View payment history and revenue

**Components:**
- Payment history table
- Revenue summary cards
- Date range filter
- Export button (CSV)
- Pagination

**API Calls:**
- `GET /api/sellers/payments?limit=100`

**Filters:**
- Date range picker
- Status filter
- Payment method filter

**Summary Cards:**
- Total revenue this month
- Total payments this month
- Average transaction value
- Success rate

### 7. Settings Page (`/settings`)

**URL:** `/settings`

**Purpose:** Account and integration settings

**Tabs:**
1. **Profile**
   - Email (read-only)
   - Company name (editable)
   - API key (show/hide)
   - Change password (future)

2. **Stripe Integration**
   - Stripe configuration form
   - Current status indicator
   - Test connection button

3. **Webhooks**
   - Webhook list table
   - Add webhook button
   - Test webhook button
   - Delete webhook

4. **Notifications**
   - Email notifications toggle
   - Webhook notifications toggle

**API Calls:**
- `GET /api/sellers/me`
- `POST /api/sellers/stripe-keys`
- `GET /api/sellers/webhooks`
- `POST /api/sellers/webhooks`

### 8. Grant Access Page (`/grant-access`)

**URL:** `/grant-access`

**Purpose:** Manually grant channel access

**Components:**
- Customer ID input
- Channel multi-select
- Duration input (days)
- Reference ID input (optional)
- Submit button

**API Calls:**
- `POST /api/telegram/grant-access`

**Success Action:**
- Show invite links
- Copy to clipboard buttons
- Email invite link option (future)

---

## State Management

### Global State Structure

```javascript
const globalState = {
  auth: {
    isAuthenticated: false,
    user: null,
    tokens: {
      access_token: null,
      refresh_token: null
    }
  },
  
  seller: {
    profile: null,
    stats: null,
    loading: false,
    error: null
  },
  
  channels: {
    list: [],
    selected: null,
    loading: false,
    error: null
  },
  
  members: {
    list: [],
    filters: {
      channel: null,
      status: 'all'
    },
    pagination: {
      page: 1,
      perPage: 20,
      total: 0
    },
    loading: false,
    error: null
  },
  
  payments: {
    list: [],
    loading: false,
    error: null
  },
  
  webhooks: {
    list: [],
    loading: false,
    error: null
  },
  
  ui: {
    sidebarOpen: true,
    theme: 'light',
    notifications: []
  }
};
```

### State Actions

```javascript
// Auth actions
const authActions = {
  login: (email, password) => {},
  register: (email, password, companyName) => {},
  logout: () => {},
  refreshToken: () => {}
};

// Seller actions
const sellerActions = {
  fetchProfile: () => {},
  fetchStats: () => {},
  updateProfile: (data) => {},
  updateStripeKeys: (publishable, secret) => {}
};

// Channel actions
const channelActions = {
  fetchChannels: () => {},
  addChannel: (chatId, name, description, price) => {},
  updateChannel: (id, data) => {},
  deleteChannel: (id) => {}
};

// Member actions
const memberActions = {
  fetchMembers: (filters) => {},
  removeMember: (extUserId, chatId, reason) => {},
  grantAccess: (extUserId, chatIds, days, ref) => {}
};

// Payment actions
const paymentActions = {
  fetchPayments: (limit) => {},
  createCheckout: (priceId, successUrl, cancelUrl) => {}
};

// Webhook actions
const webhookActions = {
  fetchWebhooks: () => {},
  createWebhook: (url, events) => {},
  deleteWebhook: (id) => {}
};
```

---

## Error Handling

### Error Types

```javascript
const ERROR_TYPES = {
  NETWORK_ERROR: 'network_error',
  AUTH_ERROR: 'auth_error',
  VALIDATION_ERROR: 'validation_error',
  API_ERROR: 'api_error',
  PERMISSION_ERROR: 'permission_error'
};
```

### Error Handler Function

```javascript
function handleApiError(error, response) {
  // Network error
  if (!response) {
    return {
      type: ERROR_TYPES.NETWORK_ERROR,
      message: 'Unable to connect to server. Please check your internet connection.',
      action: 'retry'
    };
  }
  
  // Authentication error
  if (response.status === 401) {
    // Clear tokens and redirect to login
    localStorage.clear();
    window.location.href = '/login';
    return {
      type: ERROR_TYPES.AUTH_ERROR,
      message: 'Session expired. Please login again.',
      action: 'login'
    };
  }
  
  // Permission error
  if (response.status === 403) {
    return {
      type: ERROR_TYPES.PERMISSION_ERROR,
      message: 'You don\'t have permission to perform this action.',
      action: 'none'
    };
  }
  
  // Validation error
  if (response.status === 422) {
    const result = await response.json();
    return {
      type: ERROR_TYPES.VALIDATION_ERROR,
      message: 'Please check your input and try again.',
      details: result.detail || [],
      action: 'fix'
    };
  }
  
  // API error
  const result = await response.json();
  return {
    type: ERROR_TYPES.API_ERROR,
    message: result.message || 'An error occurred',
    error: result.error,
    action: 'retry'
  };
}
```

### Error Display Component

```javascript
// Toast notification for errors
function showError(error) {
  const toast = {
    id: Date.now(),
    type: 'error',
    title: 'Error',
    message: error.message,
    duration: 5000,
    action: error.action === 'retry' ? {
      label: 'Retry',
      handler: () => retryLastAction()
    } : null
  };
  
  addToast(toast);
}

// Inline error display for forms
function FormError({ error }) {
  if (!error) return null;
  
  return (
    <div className="error-message">
      <span className="error-icon">⚠️</span>
      <span className="error-text">{error.message}</span>
      {error.details && (
        <ul className="error-details">
          {error.details.map((detail, i) => (
            <li key={i}>{detail.msg}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

---

## Best Practices

### 1. API Request Wrapper

```javascript
class ApiClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }
  
  getHeaders() {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
  }
  
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      ...options,
      headers: {
        ...this.getHeaders(),
        ...options.headers
      }
    };
    
    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const error = await handleApiError(null, response);
        throw error;
      }
      
      return await response.json();
    } catch (error) {
      if (error.type) throw error; // Already handled
      throw handleApiError(error, null); // Network error
    }
  }
  
  get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }
  
  post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
  
  put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }
  
  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
}

// Usage
const api = new ApiClient('https://api.example.com');

// Get seller profile
const profile = await api.get('/api/sellers/me');

// Add channel
const channel = await api.post('/api/telegram/channels', {
  chat_id: -1001234567890,
  name: 'My Channel'
});
```

### 2. Loading States

```javascript
// Loading state component
function LoadingSpinner({ size = 'medium' }) {
  return (
    <div className={`spinner spinner-${size}`}>
      <div className="spinner-icon"></div>
      <span className="spinner-text">Loading...</span>
    </div>
  );
}

// Page with loading
function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  
  useEffect(() => {
    async function loadStats() {
      setLoading(true);
      try {
        const result = await api.get('/api/sellers/stats');
        setStats(result.data);
      } catch (error) {
        showError(error);
      } finally {
        setLoading(false);
      }
    }
    
    loadStats();
  }, []);
  
  if (loading) {
    return <LoadingSpinner />;
  }
  
  return <StatsCards stats={stats} />;
}
```

### 3. Form Validation

```javascript
function validateChannelForm(data) {
  const errors = {};
  
  // Chat ID validation
  if (!data.chat_id) {
    errors.chat_id = 'Chat ID is required';
  } else if (data.chat_id > 0) {
    errors.chat_id = 'Use negative chat ID for channels (e.g., -1001234567890)';
  }
  
  // Name validation
  if (!data.name || data.name.trim().length === 0) {
    errors.name = 'Channel name is required';
  } else if (data.name.length > 100) {
    errors.name = 'Channel name must be less than 100 characters';
  }
  
  // Price validation
  if (data.price_per_month && data.price_per_month < 0) {
    errors.price_per_month = 'Price must be positive';
  }
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
}
```

### 4. Data Formatting

```javascript
// Format currency
function formatCurrency(cents, currency = 'USD') {
  const dollars = cents / 100;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency
  }).format(dollars);
}

// Format date
function formatDate(dateString) {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
}

// Format relative time
function formatRelativeTime(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now - date;
  
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${days}d ago`;
}
```

### 5. Pagination

```javascript
function PaginationComponent({ currentPage, totalPages, onPageChange }) {
  const pages = [];
  const maxVisible = 5;
  
  let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
  let endPage = Math.min(totalPages, startPage + maxVisible - 1);
  
  if (endPage - startPage < maxVisible - 1) {
    startPage = Math.max(1, endPage - maxVisible + 1);
  }
  
  for (let i = startPage; i <= endPage; i++) {
    pages.push(i);
  }
  
  return (
    <div className="pagination">
      <button 
        disabled={currentPage === 1}
        onClick={() => onPageChange(currentPage - 1)}
      >
        Previous
      </button>
      
      {startPage > 1 && (
        <>
          <button onClick={() => onPageChange(1)}>1</button>
          {startPage > 2 && <span>...</span>}
        </>
      )}
      
      {pages.map(page => (
        <button
          key={page}
          className={page === currentPage ? 'active' : ''}
          onClick={() => onPageChange(page)}
        >
          {page}
        </button>
      ))}
      
      {endPage < totalPages && (
        <>
          {endPage < totalPages - 1 && <span>...</span>}
          <button onClick={() => onPageChange(totalPages)}>{totalPages}</button>
        </>
      )}
      
      <button
        disabled={currentPage === totalPages}
        onClick={() => onPageChange(currentPage + 1)}
      >
        Next
      </button>
    </div>
  );
}
```

---

## Testing Guidelines

### Unit Tests

Test individual functions and components:

```javascript
// Test API client
test('ApiClient.get should fetch data', async () => {
  const api = new ApiClient('https://api.test.com');
  const data = await api.get('/api/sellers/me');
  expect(data.success).toBe(true);
});

// Test validation
test('validateChannelForm should reject invalid chat ID', () => {
  const result = validateChannelForm({ chat_id: 123 });
  expect(result.isValid).toBe(false);
  expect(result.errors.chat_id).toBeDefined();
});

// Test formatting
test('formatCurrency should format cents to dollars', () => {
  expect(formatCurrency(4900)).toBe('$49.00');
});
```

### Integration Tests

Test API integration:

```javascript
test('Login flow should authenticate and store tokens', async () => {
  const result = await loginSeller('test@example.com', 'password123');
  
  expect(result.success).toBe(true);
  expect(localStorage.getItem('access_token')).toBeDefined();
  expect(localStorage.getItem('refresh_token')).toBeDefined();
});

test('Fetch channels should return seller channels', async () => {
  const channels = await api.get('/api/sellers/channels');
  
  expect(channels.success).toBe(true);
  expect(Array.isArray(channels.data)).toBe(true);
});
```

### E2E Tests

Test complete user flows:

```javascript
test('Complete seller onboarding flow', async () => {
  // 1. Register
  await navigateTo('/register');
  await fillForm({
    email: 'newuser@test.com',
    password: 'Test123!',
    company_name: 'Test Co'
  });
  await clickButton('Register');
  
  // 2. Login
  await navigateTo('/login');
  await fillForm({
    email: 'newuser@test.com',
    password: 'Test123!'
  });
  await clickButton('Login');
  
  // 3. Verify dashboard loaded
  await waitForElement('.dashboard');
  expect(getCurrentUrl()).toBe('/dashboard');
});
```

---

## Security Considerations

### 1. Token Storage

**Best Practice:**
```javascript
// Use localStorage for web apps
localStorage.setItem('access_token', token);

// For sensitive apps, consider:
// - HttpOnly cookies (backend sets)
// - Session storage (cleared on tab close)
// - In-memory storage (lost on refresh)
```

### 2. XSS Prevention

```javascript
// Always sanitize user input before display
function sanitizeHTML(html) {
  const div = document.createElement('div');
  div.textContent = html;
  return div.innerHTML;
}

// Or use a library like DOMPurify
import DOMPurify from 'dompurify';
const clean = DOMPurify.sanitize(dirty);
```

### 3. CSRF Protection

The API uses token-based auth, which is inherently CSRF-resistant. No additional CSRF tokens needed.

### 4. Input Validation

Always validate on frontend AND backend:
```javascript
// Frontend validation
function validateInput(value, rules) {
  if (rules.required && !value) {
    return 'This field is required';
  }
  
  if (rules.minLength && value.length < rules.minLength) {
    return `Minimum length is ${rules.minLength}`;
  }
  
  if (rules.pattern && !rules.pattern.test(value)) {
    return 'Invalid format';
  }
  
  return null;
}
```

---

## Deployment Checklist

Before deploying to production:

- [ ] Replace API_BASE_URL with production URL
- [ ] Enable HTTPS only
- [ ] Set secure cookie flags (if using cookies)
- [ ] Implement proper error logging
- [ ] Set up analytics tracking
- [ ] Configure CORS properly
- [ ] Test on multiple browsers
- [ ] Test on mobile devices
- [ ] Optimize bundle size
- [ ] Enable production build optimizations
- [ ] Set up monitoring/error tracking
- [ ] Test all user flows
- [ ] Verify API rate limiting
- [ ] Check accessibility (WCAG)
- [ ] Review security headers

---

## Summary

This guide provides everything needed to build a complete seller management frontend. Key points:

1. **Use StandardResponse format** for all API interactions
2. **Implement proper authentication** with token management
3. **Follow the component specifications** for consistent UX
4. **Handle errors gracefully** with user-friendly messages
5. **Test thoroughly** at all levels
6. **Prioritize security** in implementation

For questions or clarification, refer to the [Complete API Documentation](MULTI_USER_API.md).

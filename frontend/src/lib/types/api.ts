// Standard API Response Format
export interface StandardResponse<T> {
	success: boolean;
	message: string;
	data: T | null;
	error?: {
		code: string;
		description: string;
	};
}

// Authentication
export interface LoginRequest {
	email: string;
	password: string;
}

export interface RegisterRequest {
	email: string;
	password: string;
	company_name?: string;
}

export interface AuthTokens {
	access_token: string;
	refresh_token: string;
	token_type: string;
}

export interface RegistrationData {
	seller_id: string;
	email: string;
	api_key: string;
}

// Seller
export interface Seller {
	id: string;
	email: string;
	company_name?: string;
	is_active: boolean;
	is_verified: boolean;
	subscription_status: string;
	created_at: string;
	last_login?: string;
}

export interface SellerStats {
	total_channels: number;
	active_members: number;
	total_members: number;
	total_revenue_cents: number;
	total_revenue_dollars: number;
}

export interface StripeKeysRequest {
	publishable_key: string;
	secret_key: string;
}

// Channel
export interface Channel {
	id: string;
	chat_id: number;
	name: string;
	description?: string;
	price_per_month?: number;
	total_members: number;
	active_members: number;
	is_active: boolean;
}

export interface AddChannelRequest {
	chat_id: number;
	name: string;
	join_model?: string;
	description?: string;
	price_per_month?: number;
}

export interface AddChannelResponse {
	chat_id: number;
	stored_chat_id: number;
	name: string;
	join_model: string;
	checks: {
		bot_id: number;
		chat_found: boolean;
		is_admin: boolean;
		permissions: {
			can_invite_users: boolean;
			can_manage_chat: boolean;
			can_restrict_members: boolean;
		};
	};
}

// Member
export interface User {
	_id: string;
	ext_user_id: string;
	telegram_user_id?: number;
	telegram_username?: string;
	created_at: string;
}

export interface Membership {
	_id: string;
	user_id: string;
	chat_id: number;
	status: 'active' | 'cancelled' | 'expired';
	current_period_end: string;
	created_at: string;
}

export interface MemberDetails {
	membership: Membership;
	user: User;
}

export interface RemoveMemberRequest {
	ext_user_id: string;
	chat_id: number;
	reason?: string;
	dry_run?: boolean;
}

// Payment
export interface Payment {
	id: string;
	amount: number;
	currency: string;
	status: 'succeeded' | 'pending' | 'failed' | 'refunded';
	stripe_payment_intent_id: string;
	used_seller_stripe: boolean;
	created_at: string;
}

export interface CreateCheckoutRequest {
	price_id: string;
	success_url: string;
	cancel_url: string;
	customer_email?: string;
	metadata?: Record<string, string>;
}

export interface CheckoutSessionResponse {
	session_id: string;
	url: string;
}

// Grant Access
export interface GrantAccessRequest {
	ext_user_id: string;
	chat_ids: number[];
	period_days: number;
	ref?: string;
}

export interface GrantAccessResponse {
	user_id: string;
	invites: Record<string, string>;
	period_end: string;
	errors: unknown;
}

// Webhook
export interface Webhook {
	webhook_id: string;
	url: string;
	secret: string;
	events: string[];
	is_active: boolean;
	created_at: string;
}

export interface CreateWebhookRequest {
	url: string;
	events: string[];
}

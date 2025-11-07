import { api } from './api';
import type {
	LoginRequest,
	RegisterRequest,
	AuthTokens,
	RegistrationData,
	Seller,
	SellerStats,
	StripeKeysRequest
} from '$lib/types/api';

import { goto } from '$lib/utils/navigation';

export const authService = {
	async register(data: RegisterRequest) {
		const response = await api.post<RegistrationData>('/api/sellers/register', data);
		if (response.success && response.data) {
			// Store API key for programmatic access (optional)
			// Cookies are automatically set by the backend
			if (response.data.api_key) {
				localStorage.setItem('api_key', response.data.api_key);
			}
		}
		return response;
	},

	async login(data: LoginRequest) {
		const response = await api.post<AuthTokens>('/api/sellers/login', data);
		// Cookies are automatically set by the backend with httpOnly flag
		// No need to store tokens in localStorage anymore
		return response;
	},

	async logout() {
		try {
			// Call logout endpoint to clear cookies on server
			await api.post('/api/sellers/logout');
		} catch (error) {
			console.error('Logout error:', error);
		} finally {
			// Clear any remaining local storage
			localStorage.removeItem('api_key');
			goto('/login');
		}
	},

	async checkAuth(): Promise<boolean> {
		// Try to get current user profile to verify authentication
		// If cookies are valid, this will succeed
		try {
			await api.get<Seller>('/api/sellers/me');
			return true;
		} catch {
			return false;
		}
	}
};

export const sellerService = {
	async getProfile() {
		return api.get<Seller>('/api/sellers/me');
	},

	async getStats() {
		return api.get<SellerStats>('/api/sellers/stats');
	},

	async updateStripeKeys(data: StripeKeysRequest) {
		return api.post('/api/sellers/stripe-keys', data);
	}
};

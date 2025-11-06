import type { StandardResponse } from '$lib/types/api';
import { goto } from '$lib/utils/navigation';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

export class ApiError extends Error {
	constructor(
		message: string,
		public code?: string,
		public status?: number
	) {
		super(message);
		this.name = 'ApiError';
	}
}

export class ApiClient {
	private baseUrl: string;

	constructor(baseUrl: string = API_BASE_URL) {
		this.baseUrl = baseUrl;
	}

	private getHeaders(): HeadersInit {
		const headers: HeadersInit = {
			'Content-Type': 'application/json'
		};

		// Note: Cookies are automatically sent with credentials: 'include'
		// We no longer need to manually add Authorization header for cookie-based auth
		// API key can still be added for programmatic access if needed
		const apiKey = this.getApiKey();
		if (apiKey) {
			headers['X-API-Key'] = apiKey;
		}

		return headers;
	}

	private getApiKey(): string | null {
		if (typeof window === 'undefined') return null;
		return localStorage.getItem('api_key');
	}

	async request<T>(endpoint: string, options: RequestInit = {}): Promise<StandardResponse<T>> {
		const url = `${this.baseUrl}${endpoint}`;
		const config: RequestInit = {
			...options,
			credentials: 'include', // Include cookies in requests
			headers: {
				...this.getHeaders(),
				...options.headers
			}
		};

		try {
			const response = await fetch(url, config);
			const result: StandardResponse<T> = await response.json();

			if (!response.ok) {
				// Handle 401 Unauthorized
				if (response.status === 401 && typeof window !== 'undefined') {
					// Clear any remaining local storage
					localStorage.removeItem('api_key');
					goto('/login');
				}

				throw new ApiError(
					result.message || 'An error occurred',
					result.error?.code,
					response.status
				);
			}

			return result;
		} catch (error) {
			if (error instanceof ApiError) {
				throw error;
			}
			throw new ApiError('Network error. Please check your connection.');
		}
	}

	async get<T>(endpoint: string): Promise<StandardResponse<T>> {
		return this.request<T>(endpoint, { method: 'GET' });
	}

	async post<T>(endpoint: string, data?: unknown): Promise<StandardResponse<T>> {
		return this.request<T>(endpoint, {
			method: 'POST',
			body: data ? JSON.stringify(data) : undefined
		});
	}

	async put<T>(endpoint: string, data?: unknown): Promise<StandardResponse<T>> {
		return this.request<T>(endpoint, {
			method: 'PUT',
			body: data ? JSON.stringify(data) : undefined
		});
	}

	async delete<T>(endpoint: string): Promise<StandardResponse<T>> {
		return this.request<T>(endpoint, { method: 'DELETE' });
	}
}

export const api = new ApiClient();

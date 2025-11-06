import { api } from './api';
import type { Payment, CreateCheckoutRequest, CheckoutSessionResponse } from '$lib/types/api';

export const paymentService = {
	async list(limit: number = 100) {
		return api.get<Payment[]>(`/api/sellers/payments?limit=${limit}`);
	},

	async createCheckout(data: CreateCheckoutRequest) {
		return api.post<CheckoutSessionResponse>('/api/payments/checkout', data);
	}
};

import { api } from './api';
import type { Webhook, CreateWebhookRequest } from '$lib/types/api';

export const webhookService = {
	async list() {
		return api.get<Webhook[]>('/api/sellers/webhooks');
	},

	async create(data: CreateWebhookRequest) {
		return api.post<Webhook>('/api/sellers/webhooks', data);
	},

	async delete(webhookId: string) {
		return api.delete<{ success: boolean }>(`/api/sellers/webhooks/${webhookId}`);
	}
};

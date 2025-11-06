import { api } from './api';
import type { Channel, AddChannelRequest, AddChannelResponse } from '$lib/types/api';

export const channelService = {
	async list() {
		return api.get<Channel[]>('/api/sellers/channels');
	},

	async add(data: AddChannelRequest) {
		return api.post<AddChannelResponse>('/api/telegram/channels', data);
	},

	async update(data: AddChannelRequest) {
		return api.post<AddChannelResponse>('/api/sellers/channels', data);
	}
};

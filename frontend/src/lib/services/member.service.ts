import { api } from './api';
import type {
	MemberDetails,
	RemoveMemberRequest,
	GrantAccessRequest,
	GrantAccessResponse
} from '$lib/types/api';

export const memberService = {
	async list(chatId?: number, status?: string) {
		const params = new URLSearchParams();
		if (chatId) params.append('chat_id', chatId.toString());
		if (status && status !== 'all') params.append('status', status);

		const query = params.toString() ? `?${params.toString()}` : '';
		return api.get<MemberDetails[]>(`/api/sellers/members${query}`);
	},

	async remove(data: RemoveMemberRequest) {
		return api.post('/api/telegram/force-remove', data);
	},

	async grantAccess(data: GrantAccessRequest) {
		return api.post<GrantAccessResponse>('/api/telegram/grant-access', data);
	}
};

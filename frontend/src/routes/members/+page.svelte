<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$lib/utils/navigation';
	import Navigation from '$lib/components/Navigation.svelte';
	import Loading from '$lib/components/Loading.svelte';
	import { memberService } from '$lib/services/member.service';
	import { channelService } from '$lib/services/channel.service';
	import { authService } from '$lib/services/auth.service';
	import { formatShortDate } from '$lib/utils/format';
	import type { MemberDetails, Channel } from '$lib/types/api';

	let loading = $state(true);
	let members: MemberDetails[] = $state([]);
	let channels: Channel[] = $state([]);
	let error = $state('');

	// Filters
	let selectedChannel = $state('');
	let selectedStatus = $state('all');

	// Remove member
	let removingMember: string | null = $state(null);

	onMount(async () => {
		if (!authService.isAuthenticated()) {
			goto('/login');
			return;
		}

		await Promise.all([loadChannels(), loadMembers()]);
	});

	async function loadChannels() {
		try {
			const response = await channelService.list();
			if (response.success && response.data) {
				channels = response.data;
			}
		} catch (err) {
			console.error('Failed to load channels:', err);
		}
	}

	async function loadMembers() {
		loading = true;
		error = '';

		try {
			const chatId = selectedChannel ? parseInt(selectedChannel) : undefined;
			const status = selectedStatus === 'all' ? undefined : selectedStatus;

			const response = await memberService.list(chatId, status);
			if (response.success && response.data) {
				members = response.data;
			}
		} catch (err: unknown) {
			error = (err as Error).message || 'Failed to load members';
		} finally {
			loading = false;
		}
	}

	async function handleRemoveMember(member: MemberDetails) {
		if (
			!confirm(
				`Are you sure you want to remove ${member.user.telegram_username || member.user.ext_user_id}?`
			)
		) {
			return;
		}

		removingMember = member.membership._id;

		try {
			const response = await memberService.remove({
				ext_user_id: member.user.ext_user_id,
				chat_id: member.membership.chat_id,
				reason: 'Removed by seller'
			});

			if (response.success) {
				await loadMembers();
			}
		} catch (err: unknown) {
			alert((err as Error).message || 'Failed to remove member');
		} finally {
			removingMember = null;
		}
	}

	function handleFilterChange() {
		loadMembers();
	}

	function getStatusBadgeClass(status: string) {
		switch (status) {
			case 'active':
				return 'badge-success';
			case 'cancelled':
				return 'badge-warning';
			case 'expired':
				return 'badge-error';
			default:
				return 'badge-info';
		}
	}
</script>

<svelte:head>
	<title>Members - TG Seller Platform</title>
</svelte:head>

<div class="min-h-screen bg-[var(--bg-primary)]">
	<Navigation />

	<main class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
		<!-- Header -->
		<div class="mb-8">
			<h1 class="cyber-text-glow mb-2 text-4xl font-bold" style="color: var(--cyber-blue)">
				MEMBERS
			</h1>
			<p class="text-gray-400">Manage your channel subscribers</p>
		</div>

		<!-- Filters -->
		<div class="cyber-card mb-6">
			<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
				<div>
					<label for="channelFilter" class="mb-2 block text-sm font-medium text-gray-300">
						Filter by Channel
					</label>
					<select
						id="channelFilter"
						bind:value={selectedChannel}
						onchange={handleFilterChange}
						class="cyber-input"
					>
						<option value="">All Channels</option>
						{#each channels as channel (channel.id)}
							<option value={channel.chat_id}>{channel.name}</option>
						{/each}
					</select>
				</div>

				<div>
					<label for="statusFilter" class="mb-2 block text-sm font-medium text-gray-300">
						Filter by Status
					</label>
					<select
						id="statusFilter"
						bind:value={selectedStatus}
						onchange={handleFilterChange}
						class="cyber-input"
					>
						<option value="all">All Statuses</option>
						<option value="active">Active</option>
						<option value="cancelled">Cancelled</option>
						<option value="expired">Expired</option>
					</select>
				</div>
			</div>
		</div>

		{#if loading}
			<Loading loading={true} />
		{:else if error}
			<div class="bg-opacity-20 rounded border border-[var(--cyber-red)] bg-[var(--cyber-red)] p-4">
				<p class="font-semibold">Error loading members</p>
				<p class="mt-1 text-sm">{error}</p>
				<button
					onclick={loadMembers}
					class="mt-2 rounded bg-[var(--cyber-red)] px-4 py-2 text-sm font-semibold hover:opacity-80"
				>
					Retry
				</button>
			</div>
		{:else if members.length === 0}
			<div class="cyber-card py-12 text-center">
				<div class="mb-4 text-6xl">👥</div>
				<h3 class="mb-2 text-xl font-semibold">No Members Found</h3>
				<p class="text-gray-400">
					{selectedChannel || selectedStatus !== 'all'
						? 'Try changing your filters'
						: 'No members yet'}
				</p>
			</div>
		{:else}
			<!-- Members Table -->
			<div class="cyber-card overflow-x-auto">
				<div class="mb-4 text-sm text-gray-400">
					Showing {members.length} member{members.length !== 1 ? 's' : ''}
				</div>
				<table class="w-full">
					<thead>
						<tr class="border-b border-[var(--border-color)]">
							<th class="px-4 py-3 text-left font-semibold text-[var(--cyber-blue)]">Username</th>
							<th class="px-4 py-3 text-left font-semibold text-[var(--cyber-blue)]">Telegram ID</th
							>
							<th class="px-4 py-3 text-left font-semibold text-[var(--cyber-blue)]">Status</th>
							<th class="px-4 py-3 text-left font-semibold text-[var(--cyber-blue)]">Expires</th>
							<th class="px-4 py-3 text-left font-semibold text-[var(--cyber-blue)]">Actions</th>
						</tr>
					</thead>
					<tbody>
						{#each members as member (member.membership._id)}
							<tr class="border-b border-[var(--border-color)] hover:bg-[var(--bg-tertiary)]">
								<td class="px-4 py-3">
									{#if member.user.telegram_username}
										<span class="font-medium">@{member.user.telegram_username}</span>
									{:else}
										<span class="text-gray-400">No username</span>
									{/if}
									<div class="text-xs text-gray-500">{member.user.ext_user_id}</div>
								</td>
								<td class="px-4 py-3 text-gray-300">
									{member.user.telegram_user_id || 'N/A'}
								</td>
								<td class="px-4 py-3">
									<span class="badge {getStatusBadgeClass(member.membership.status)}">
										{member.membership.status}
									</span>
								</td>
								<td class="px-4 py-3 text-gray-300">
									{formatShortDate(member.membership.current_period_end)}
								</td>
								<td class="px-4 py-3">
									<button
										onclick={() => handleRemoveMember(member)}
										disabled={removingMember === member.membership._id}
										class="hover:bg-opacity-20 rounded border border-[var(--cyber-red)] px-3 py-1 text-sm text-[var(--cyber-red)] transition-all hover:bg-[var(--cyber-red)] disabled:opacity-50"
									>
										{removingMember === member.membership._id ? 'Removing...' : 'Remove'}
									</button>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</main>
</div>

<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$lib/utils/navigation';
	import Navigation from '$lib/components/Navigation.svelte';
	import Loading from '$lib/components/Loading.svelte';
	import Button from '$lib/components/Button.svelte';
	import Input from '$lib/components/Input.svelte';
	import { channelService } from '$lib/services/channel.service';
	import { authService } from '$lib/services/auth.service';
	import { formatCurrency } from '$lib/utils/format';
	import type { Channel } from '$lib/types/api';

	let loading = $state(true);
	let channels: Channel[] = $state([]);
	let error = $state('');
	let showAddModal = $state(false);
	let addingChannel = $state(false);

	// Form fields
	let chatId = $state('');
	let channelName = $state('');
	let description = $state('');
	let pricePerMonth = $state('');
	let formError = $state('');

	onMount(async () => {
		if (!authService.isAuthenticated()) {
			goto('/login');
			return;
		}

		await loadChannels();
	});

	async function loadChannels() {
		loading = true;
		error = '';

		try {
			const response = await channelService.list();
			if (response.success && response.data) {
				channels = response.data;
			}
		} catch (err: unknown) {
			error = (err as Error).message || 'Failed to load channels';
		} finally {
			loading = false;
		}
	}

	async function handleAddChannel(e: Event) {
		e.preventDefault();

		if (!chatId || !channelName) {
			formError = 'Chat ID and Channel Name are required';
			return;
		}

		addingChannel = true;
		formError = '';

		try {
			const data = {
				chat_id: parseInt(chatId),
				name: channelName,
				description: description || undefined,
				price_per_month: pricePerMonth ? parseFloat(pricePerMonth) * 100 : undefined
			};

			const response = await channelService.add(data);
			if (response.success) {
				// Reset form
				chatId = '';
				channelName = '';
				description = '';
				pricePerMonth = '';
				showAddModal = false;

				// Reload channels
				await loadChannels();
			}
		} catch (err: unknown) {
			formError = (err as Error).message || 'Failed to add channel';
		} finally {
			addingChannel = false;
		}
	}

	function openAddModal() {
		showAddModal = true;
		formError = '';
	}

	function closeAddModal() {
		showAddModal = false;
		chatId = '';
		channelName = '';
		description = '';
		pricePerMonth = '';
		formError = '';
	}
</script>

<svelte:head>
	<title>Channels - TG Seller Platform</title>
</svelte:head>

<div class="min-h-screen bg-[var(--bg-primary)]">
	<Navigation />

	<main class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
		<!-- Header -->
		<div class="mb-8 flex items-center justify-between">
			<div>
				<h1 class="cyber-text-glow mb-2 text-4xl font-bold" style="color: var(--cyber-blue)">
					CHANNELS
				</h1>
				<p class="text-gray-400">Manage your Telegram channels</p>
			</div>
			<Button onclick={openAddModal} variant="primary">
				<span class="flex items-center gap-2">
					<span>➕</span>
					Add Channel
				</span>
			</Button>
		</div>

		{#if loading}
			<Loading loading={true} />
		{:else if error}
			<div class="bg-opacity-20 rounded border border-[var(--cyber-red)] bg-[var(--cyber-red)] p-4">
				<p class="font-semibold">Error loading channels</p>
				<p class="mt-1 text-sm">{error}</p>
				<button
					onclick={loadChannels}
					class="mt-2 rounded bg-[var(--cyber-red)] px-4 py-2 text-sm font-semibold hover:opacity-80"
				>
					Retry
				</button>
			</div>
		{:else if channels.length === 0}
			<div class="cyber-card py-12 text-center">
				<div class="mb-4 text-6xl">📡</div>
				<h3 class="mb-2 text-xl font-semibold">No Channels Yet</h3>
				<p class="mb-6 text-gray-400">Add your first Telegram channel to get started</p>
				<Button onclick={openAddModal} variant="primary">Add Your First Channel</Button>
			</div>
		{:else}
			<!-- Channels Table -->
			<div class="cyber-card overflow-x-auto">
				<table class="w-full">
					<thead>
						<tr class="border-b border-[var(--border-color)]">
							<th class="px-4 py-3 text-left font-semibold text-[var(--cyber-blue)]"
								>Channel Name</th
							>
							<th class="px-4 py-3 text-left font-semibold text-[var(--cyber-blue)]">Chat ID</th>
							<th class="px-4 py-3 text-left font-semibold text-[var(--cyber-blue)]">Members</th>
							<th class="px-4 py-3 text-left font-semibold text-[var(--cyber-blue)]">Price</th>
							<th class="px-4 py-3 text-left font-semibold text-[var(--cyber-blue)]">Status</th>
						</tr>
					</thead>
					<tbody>
						{#each channels as channel (channel.id)}
							<tr class="border-b border-[var(--border-color)] hover:bg-[var(--bg-tertiary)]">
								<td class="px-4 py-3">
									<div class="font-semibold">{channel.name}</div>
									{#if channel.description}
										<div class="text-sm text-gray-400">{channel.description}</div>
									{/if}
								</td>
								<td class="px-4 py-3 text-gray-300">{channel.chat_id}</td>
								<td class="px-4 py-3">
									<div class="text-[var(--cyber-green)]">{channel.active_members} active</div>
									<div class="text-sm text-gray-400">{channel.total_members} total</div>
								</td>
								<td class="px-4 py-3">
									{#if channel.price_per_month}
										{formatCurrency(channel.price_per_month)}/mo
									{:else}
										<span class="text-gray-400">Free</span>
									{/if}
								</td>
								<td class="px-4 py-3">
									{#if channel.is_active}
										<span class="badge badge-success">Active</span>
									{:else}
										<span class="badge badge-error">Inactive</span>
									{/if}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</main>
</div>

<!-- Add Channel Modal -->
{#if showAddModal}
	<div
		class="bg-opacity-75 fixed inset-0 z-50 flex items-center justify-center bg-black p-4"
		role="dialog"
		aria-modal="true"
		aria-labelledby="modal-title"
		onclick={closeAddModal}
		onkeydown={(e) => e.key === 'Escape' && closeAddModal()}
	>
		<div
			class="cyber-card neon-border w-full max-w-lg"
			role="document"
			onclick={(e) => e.stopPropagation()}
			onkeydown={(e) => e.stopPropagation()}
		>
			<div class="mb-6 flex items-center justify-between">
				<h2 id="modal-title" class="text-2xl font-bold" style="color: var(--cyber-blue)">
					Add New Channel
				</h2>
				<button
					onclick={closeAddModal}
					class="text-2xl text-gray-400 transition-colors hover:text-white"
				>
					×
				</button>
			</div>

			<form onsubmit={handleAddChannel}>
				<Input
					label="Telegram Chat ID"
					id="chatId"
					type="number"
					bind:value={chatId}
					placeholder="-1001234567890"
					required
				/>
				<p class="-mt-3 mb-4 text-xs text-gray-400">
					Use @getidsbot in Telegram to get your channel ID
				</p>

				<Input
					label="Channel Name"
					id="channelName"
					type="text"
					bind:value={channelName}
					placeholder="Premium Signals"
					required
				/>

				<div class="mb-4">
					<label
						for="description"
						class="mb-2 block text-sm font-medium tracking-wide text-gray-300 uppercase"
					>
						Description
					</label>
					<textarea
						id="description"
						bind:value={description}
						placeholder="Optional channel description"
						class="cyber-input min-h-[80px]"
					></textarea>
				</div>

				<Input
					label="Monthly Price (USD)"
					id="pricePerMonth"
					type="number"
					bind:value={pricePerMonth}
					placeholder="49.00"
				/>

				{#if formError}
					<div
						class="bg-opacity-20 mb-4 rounded border border-[var(--cyber-red)] bg-[var(--cyber-red)] p-3 text-sm"
					>
						{formError}
					</div>
				{/if}

				<div class="flex gap-4">
					<Button type="submit" loading={addingChannel} variant="primary">
						{#if addingChannel}
							Adding...
						{:else}
							Add Channel
						{/if}
					</Button>
					<Button type="button" onclick={closeAddModal} variant="secondary">Cancel</Button>
				</div>
			</form>
		</div>
	</div>
{/if}

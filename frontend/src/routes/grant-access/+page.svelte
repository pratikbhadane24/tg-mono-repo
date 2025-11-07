<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$lib/utils/navigation';
	import Navigation from '$lib/components/Navigation.svelte';
	import Button from '$lib/components/Button.svelte';
	import Input from '$lib/components/Input.svelte';
	import { memberService } from '$lib/services/member.service';
	import { channelService } from '$lib/services/channel.service';
	import { authService } from '$lib/services/auth.service';
	import type { Channel } from '$lib/types/api';

	let loading = $state(false);
	let channels: Channel[] = $state([]);
	let error = $state('');
	let success = $state(false);
	let inviteLinks: Record<string, string> = $state({});

	// Form fields
	let extUserId = $state('');
	let selectedChannels = $state<number[]>([]);
	let periodDays = $state('30');
	let reference = $state('');

	onMount(async () => {
		const isAuth = await authService.checkAuth();
		if (!isAuth) {
			goto('/login');
			return;
		}

		await loadChannels();
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

	async function handleGrantAccess(e: Event) {
		e.preventDefault();

		if (!extUserId || selectedChannels.length === 0 || !periodDays) {
			error = 'Please fill in all required fields and select at least one channel';
			return;
		}

		loading = true;
		error = '';
		success = false;

		try {
			const response = await memberService.grantAccess({
				ext_user_id: extUserId,
				chat_ids: selectedChannels,
				period_days: parseInt(periodDays),
				ref: reference || undefined
			});

			if (response.success && response.data) {
				success = true;
				inviteLinks = response.data.invites;
			}
		} catch (err: unknown) {
			error = (err as Error).message || 'Failed to grant access';
		} finally {
			loading = false;
		}
	}

	function toggleChannel(chatId: number) {
		if (selectedChannels.includes(chatId)) {
			selectedChannels = selectedChannels.filter((id) => id !== chatId);
		} else {
			selectedChannels = [...selectedChannels, chatId];
		}
	}

	function copyToClipboard(text: string) {
		navigator.clipboard.writeText(text);
		alert('Copied to clipboard!');
	}

	function resetForm() {
		extUserId = '';
		selectedChannels = [];
		periodDays = '30';
		reference = '';
		success = false;
		inviteLinks = {};
		error = '';
	}
</script>

<svelte:head>
	<title>Grant Access - TG Seller Platform</title>
</svelte:head>

<div class="min-h-screen bg-[var(--bg-primary)]">
	<Navigation />

	<main class="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
		<!-- Header -->
		<div class="mb-8">
			<h1 class="cyber-text-glow mb-2 text-4xl font-bold" style="color: var(--cyber-blue)">
				GRANT ACCESS
			</h1>
			<p class="text-gray-400">Manually grant channel access to users</p>
		</div>

		{#if success}
			<!-- Success State -->
			<div
				class="cyber-card bg-opacity-10 mb-6 border border-[var(--cyber-green)] bg-[var(--cyber-green)]"
			>
				<h3 class="mb-4 text-xl font-bold" style="color: var(--cyber-green)">
					✓ Access Granted Successfully!
				</h3>
				<p class="mb-4 text-gray-300">Share these invite links with the user:</p>

				<div class="space-y-3">
					{#each Object.entries(inviteLinks) as [chatId, link] (chatId)}
						{@const channel = channels.find((c) => c.chat_id.toString() === chatId)}
						<div class="flex items-center gap-3 rounded bg-[var(--bg-tertiary)] p-3">
							<div class="flex-1">
								<div class="font-semibold">{channel?.name || `Channel ${chatId}`}</div>
								<div class="font-mono text-sm break-all text-gray-400">{link}</div>
							</div>
							<button
								onclick={() => copyToClipboard(link)}
								class="rounded bg-[var(--cyber-blue)] px-4 py-2 text-sm font-semibold whitespace-nowrap hover:opacity-80"
							>
								Copy Link
							</button>
						</div>
					{/each}
				</div>

				<div class="mt-6">
					<Button onclick={resetForm} variant="primary">Grant Access to Another User</Button>
				</div>
			</div>
		{:else}
			<!-- Grant Access Form -->
			<div class="cyber-card">
				<form onsubmit={handleGrantAccess}>
					<Input
						label="Customer ID"
						id="extUserId"
						type="text"
						bind:value={extUserId}
						placeholder="customer_12345"
						required
					/>
					<p class="-mt-3 mb-4 text-xs text-gray-400">
						Unique identifier for the customer (ext_user_id)
					</p>

					<!-- Channel Selection -->
					<div class="mb-4">
						<span class="mb-2 block text-sm font-medium tracking-wide text-gray-300 uppercase">
							Select Channels
							<span class="text-[var(--cyber-pink)]">*</span>
						</span>
						<div class="max-h-60 space-y-2 overflow-y-auto rounded bg-[var(--bg-tertiary)] p-4">
							{#each channels as channel (channel.id)}
								<label
									class="flex cursor-pointer items-center gap-3 rounded p-2 transition-colors hover:bg-[var(--bg-secondary)]"
								>
									<input
										type="checkbox"
										checked={selectedChannels.includes(channel.chat_id)}
										onchange={() => toggleChannel(channel.chat_id)}
										class="h-5 w-5 rounded border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--cyber-blue)] focus:ring-[var(--cyber-blue)]"
									/>
									<div class="flex-1">
										<div class="font-semibold">{channel.name}</div>
										<div class="text-sm text-gray-400">
											{channel.active_members} members • Chat ID: {channel.chat_id}
										</div>
									</div>
								</label>
							{/each}
						</div>
						{#if channels.length === 0}
							<p class="mt-2 text-sm text-gray-400">
								No channels available. Please add channels first.
							</p>
						{/if}
					</div>

					<Input
						label="Access Period (Days)"
						id="periodDays"
						type="number"
						bind:value={periodDays}
						placeholder="30"
						required
					/>

					<Input
						label="Reference (Optional)"
						id="reference"
						type="text"
						bind:value={reference}
						placeholder="payment_abc123"
					/>
					<p class="-mt-3 mb-4 text-xs text-gray-400">
						Optional reference ID for tracking (e.g., payment ID, order ID)
					</p>

					{#if error}
						<div
							class="bg-opacity-20 mb-4 rounded border border-[var(--cyber-red)] bg-[var(--cyber-red)] p-3 text-sm"
						>
							{error}
						</div>
					{/if}

					<Button type="submit" {loading} variant="primary">
						{#if loading}
							Granting Access...
						{:else}
							Grant Access
						{/if}
					</Button>
				</form>
			</div>
		{/if}
	</main>
</div>

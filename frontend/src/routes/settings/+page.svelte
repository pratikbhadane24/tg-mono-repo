<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$lib/utils/navigation';
	import Navigation from '$lib/components/Navigation.svelte';
	import Button from '$lib/components/Button.svelte';
	import Input from '$lib/components/Input.svelte';
	import Loading from '$lib/components/Loading.svelte';
	import { sellerService } from '$lib/services/auth.service';
	import { webhookService } from '$lib/services/webhook.service';
	import { authService } from '$lib/services/auth.service';
	import { formatDate } from '$lib/utils/format';
	import type { Seller, Webhook } from '$lib/types/api';

	let loading = $state(true);
	let profile: Seller | null = $state(null);
	let webhooks: Webhook[] = $state([]);
	let activeTab = $state<'profile' | 'stripe' | 'webhooks'>('profile');
	let error = $state('');

	// Stripe form
	let stripePublishableKey = $state('');
	let stripeSecretKey = $state('');
	let stripeSaving = $state(false);
	let stripeSuccess = $state(false);

	// Webhook form
	let showWebhookModal = $state(false);
	let webhookUrl = $state('');
	let webhookEvents = $state<string[]>([]);
	let webhookSaving = $state(false);
	let webhookError = $state('');

	const availableEvents = [
		'member.joined',
		'member.left',
		'payment.succeeded',
		'subscription.expired'
	];

	onMount(async () => {
		if (!authService.isAuthenticated()) {
			goto('/login');
			return;
		}

		await Promise.all([loadProfile(), loadWebhooks()]);
		loading = false;
	});

	async function loadProfile() {
		try {
			const response = await sellerService.getProfile();
			if (response.success && response.data) {
				profile = response.data;
			}
		} catch (err: unknown) {
			error = (err as Error).message || 'Failed to load profile';
		}
	}

	async function loadWebhooks() {
		try {
			const response = await webhookService.list();
			if (response.success && response.data) {
				webhooks = response.data;
			}
		} catch (err) {
			console.error('Failed to load webhooks:', err);
		}
	}

	async function handleSaveStripeKeys(e: Event) {
		e.preventDefault();

		if (!stripePublishableKey || !stripeSecretKey) {
			error = 'Both Stripe keys are required';
			return;
		}

		stripeSaving = true;
		error = '';
		stripeSuccess = false;

		try {
			const response = await sellerService.updateStripeKeys({
				publishable_key: stripePublishableKey,
				secret_key: stripeSecretKey
			});

			if (response.success) {
				stripeSuccess = true;
				stripePublishableKey = '';
				stripeSecretKey = '';
				setTimeout(() => {
					stripeSuccess = false;
				}, 3000);
			}
		} catch (err: unknown) {
			error = (err as Error).message || 'Failed to save Stripe keys';
		} finally {
			stripeSaving = false;
		}
	}

	async function handleCreateWebhook(e: Event) {
		e.preventDefault();

		if (!webhookUrl || webhookEvents.length === 0) {
			webhookError = 'URL and at least one event are required';
			return;
		}

		webhookSaving = true;
		webhookError = '';

		try {
			const response = await webhookService.create({
				url: webhookUrl,
				events: webhookEvents
			});

			if (response.success) {
				webhookUrl = '';
				webhookEvents = [];
				showWebhookModal = false;
				await loadWebhooks();
			}
		} catch (err: unknown) {
			webhookError = (err as Error).message || 'Failed to create webhook';
		} finally {
			webhookSaving = false;
		}
	}

	async function handleDeleteWebhook(webhookId: string) {
		if (!confirm('Are you sure you want to delete this webhook?')) {
			return;
		}

		try {
			await webhookService.delete(webhookId);
			await loadWebhooks();
		} catch (err: unknown) {
			alert((err as Error).message || 'Failed to delete webhook');
		}
	}

	function toggleWebhookEvent(event: string) {
		if (webhookEvents.includes(event)) {
			webhookEvents = webhookEvents.filter((e) => e !== event);
		} else {
			webhookEvents = [...webhookEvents, event];
		}
	}
</script>

<svelte:head>
	<title>Settings - TG Seller Platform</title>
</svelte:head>

<div class="min-h-screen bg-[var(--bg-primary)]">
	<Navigation />

	<main class="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
		<!-- Header -->
		<div class="mb-8">
			<h1 class="cyber-text-glow mb-2 text-4xl font-bold" style="color: var(--cyber-blue)">
				SETTINGS
			</h1>
			<p class="text-gray-400">Manage your account and integrations</p>
		</div>

		{#if loading}
			<Loading loading={true} />
		{:else}
			<!-- Tabs -->
			<div class="cyber-card mb-6">
				<div class="flex gap-4 border-b border-[var(--border-color)]">
					<button
						onclick={() => (activeTab = 'profile')}
						class="px-4 py-2 font-semibold transition-all {activeTab === 'profile'
							? 'border-b-2 border-[var(--cyber-blue)] text-[var(--cyber-blue)]'
							: 'text-gray-400 hover:text-white'}"
					>
						Profile
					</button>
					<button
						onclick={() => (activeTab = 'stripe')}
						class="px-4 py-2 font-semibold transition-all {activeTab === 'stripe'
							? 'border-b-2 border-[var(--cyber-blue)] text-[var(--cyber-blue)]'
							: 'text-gray-400 hover:text-white'}"
					>
						Stripe Integration
					</button>
					<button
						onclick={() => (activeTab = 'webhooks')}
						class="px-4 py-2 font-semibold transition-all {activeTab === 'webhooks'
							? 'border-b-2 border-[var(--cyber-blue)] text-[var(--cyber-blue)]'
							: 'text-gray-400 hover:text-white'}"
					>
						Webhooks
					</button>
				</div>
			</div>

			<!-- Tab Content -->
			{#if activeTab === 'profile'}
				<!-- Profile Tab -->
				<div class="cyber-card">
					<h2 class="mb-6 text-2xl font-bold" style="color: var(--cyber-blue)">
						Profile Information
					</h2>
					{#if profile}
						<div class="space-y-4">
							<div>
								<label class="text-sm text-gray-400 uppercase">Email</label>
								<p class="text-lg font-semibold">{profile.email}</p>
							</div>
							<div>
								<label class="text-sm text-gray-400 uppercase">Company Name</label>
								<p class="text-lg font-semibold">{profile.company_name || 'Not set'}</p>
							</div>
							<div>
								<label class="text-sm text-gray-400 uppercase">Account Status</label>
								<p>
									{#if profile.is_active}
										<span class="badge badge-success">Active</span>
									{:else}
										<span class="badge badge-error">Inactive</span>
									{/if}
									{#if profile.is_verified}
										<span class="badge badge-success ml-2">Verified</span>
									{/if}
								</p>
							</div>
							<div>
								<label class="text-sm text-gray-400 uppercase">Member Since</label>
								<p class="text-lg">{formatDate(profile.created_at)}</p>
							</div>
							{#if profile.last_login}
								<div>
									<label class="text-sm text-gray-400 uppercase">Last Login</label>
									<p class="text-lg">{formatDate(profile.last_login)}</p>
								</div>
							{/if}
						</div>
					{/if}
				</div>
			{:else if activeTab === 'stripe'}
				<!-- Stripe Tab -->
				<div class="cyber-card">
					<h2 class="mb-6 text-2xl font-bold" style="color: var(--cyber-blue)">
						Stripe Integration
					</h2>
					<p class="mb-6 text-gray-400">
						Configure your own Stripe account to receive payments directly. Leave empty to use the
						platform's Stripe account.
					</p>

					{#if stripeSuccess}
						<div
							class="bg-opacity-20 mb-4 rounded border border-[var(--cyber-green)] bg-[var(--cyber-green)] p-3"
						>
							Stripe keys saved successfully!
						</div>
					{/if}

					<form onsubmit={handleSaveStripeKeys}>
						<Input
							label="Stripe Publishable Key"
							id="stripePublishableKey"
							type="text"
							bind:value={stripePublishableKey}
							placeholder="pk_live_..."
							required
						/>

						<Input
							label="Stripe Secret Key"
							id="stripeSecretKey"
							type="password"
							bind:value={stripeSecretKey}
							placeholder="sk_live_..."
							required
						/>

						{#if error}
							<div
								class="bg-opacity-20 mb-4 rounded border border-[var(--cyber-red)] bg-[var(--cyber-red)] p-3 text-sm"
							>
								{error}
							</div>
						{/if}

						<Button type="submit" loading={stripeSaving} variant="primary">
							{#if stripeSaving}
								Saving...
							{:else}
								Save Stripe Keys
							{/if}
						</Button>
					</form>
				</div>
			{:else if activeTab === 'webhooks'}
				<!-- Webhooks Tab -->
				<div class="cyber-card mb-6">
					<div class="mb-6 flex items-center justify-between">
						<h2 class="text-2xl font-bold" style="color: var(--cyber-blue)">Webhooks</h2>
						<Button onclick={() => (showWebhookModal = true)} variant="primary">Add Webhook</Button>
					</div>

					{#if webhooks.length === 0}
						<div class="py-12 text-center">
							<div aria-hidden="true" class="mb-4 text-6xl">🔔</div>
							<h3 class="mb-2 text-xl font-semibold">No Webhooks Configured</h3>
							<p class="mb-6 text-gray-400">
								Add a webhook to receive real-time event notifications
							</p>
						</div>
					{:else}
						<div class="space-y-4">
							{#each webhooks as webhook (webhook.webhook_id)}
								<div
									class="rounded border border-[var(--border-color)] bg-[var(--bg-tertiary)] p-4"
								>
									<div class="mb-2 flex items-start justify-between">
										<div class="flex-1">
											<div class="font-semibold break-all">{webhook.url}</div>
											<div class="mt-1 text-sm text-gray-400">
												Created: {formatDate(webhook.created_at)}
											</div>
										</div>
										<button
											onclick={() => handleDeleteWebhook(webhook.webhook_id)}
											class="hover:bg-opacity-20 ml-4 rounded border border-[var(--cyber-red)] px-3 py-1 text-sm text-[var(--cyber-red)] hover:bg-[var(--cyber-red)]"
										>
											Delete
										</button>
									</div>
									<div class="mt-3 flex flex-wrap gap-2">
										{#each webhook.events as event (event)}
											<span class="badge badge-info text-xs">{event}</span>
										{/each}
									</div>
								</div>
							{/each}
						</div>
					{/if}
				</div>
			{/if}
		{/if}
	</main>
</div>

<!-- Add Webhook Modal -->
{#if showWebhookModal}
	<div
		class="bg-opacity-75 fixed inset-0 z-50 flex items-center justify-center bg-black p-4"
		role="dialog"
		aria-modal="true"
		aria-labelledby="webhook-modal-title"
		tabindex="-1"
		onclick={() => (showWebhookModal = false)}
		onkeydown={(e) => e.key === 'Escape' && (showWebhookModal = false)}
	>
		<div
			class="cyber-card neon-border w-full max-w-lg"
			role="document"
			onclick={(e) => e.stopPropagation()}
			onkeydown={(e) => e.stopPropagation()}
		>
			<div class="mb-6 flex items-center justify-between">
				<h2 id="webhook-modal-title" class="text-2xl font-bold" style="color: var(--cyber-blue)">
					Add Webhook
				</h2>
				<button
					onclick={() => (showWebhookModal = false)}
					class="text-2xl text-gray-400 transition-colors hover:text-white"
				>
					×
				</button>
			</div>

			<form onsubmit={handleCreateWebhook}>
				<Input
					label="Webhook URL"
					id="webhookUrl"
					type="url"
					bind:value={webhookUrl}
					placeholder="https://yourapp.com/webhooks"
					required
				/>

				<div class="mb-4">
					<label class="mb-2 block text-sm font-medium tracking-wide text-gray-300 uppercase">
						Events to Subscribe
						<span class="text-[var(--cyber-pink)]">*</span>
					</label>
					<div class="space-y-2 rounded bg-[var(--bg-tertiary)] p-4">
						{#each availableEvents as event (event)}
							<label
								class="flex cursor-pointer items-center gap-3 rounded p-2 hover:bg-[var(--bg-secondary)]"
							>
								<input
									type="checkbox"
									checked={webhookEvents.includes(event)}
									onchange={() => toggleWebhookEvent(event)}
									class="h-5 w-5 rounded border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--cyber-blue)]"
								/>
								<span>{event}</span>
							</label>
						{/each}
					</div>
				</div>

				{#if webhookError}
					<div
						class="bg-opacity-20 mb-4 rounded border border-[var(--cyber-red)] bg-[var(--cyber-red)] p-3 text-sm"
					>
						{webhookError}
					</div>
				{/if}

				<div class="flex gap-4">
					<Button type="submit" loading={webhookSaving} variant="primary">
						{#if webhookSaving}
							Creating...
						{:else}
							Create Webhook
						{/if}
					</Button>
					<Button type="button" onclick={() => (showWebhookModal = false)} variant="secondary">
						Cancel
					</Button>
				</div>
			</form>
		</div>
	</div>
{/if}

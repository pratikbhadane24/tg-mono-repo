<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$lib/utils/navigation';
	import { resolve } from '$app/paths';
	import Navigation from '$lib/components/Navigation.svelte';
	import Loading from '$lib/components/Loading.svelte';
	import StatCard from '$lib/components/StatCard.svelte';
	import { sellerService } from '$lib/services/auth.service';
	import { authService } from '$lib/services/auth.service';
	import { formatCurrency } from '$lib/utils/format';
	import type { SellerStats } from '$lib/types/api';

	let loading = $state(true);
	let stats: SellerStats | null = $state(null);
	let error = $state('');

	onMount(async () => {
		const isAuth = await authService.checkAuth();
		if (!isAuth) {
			goto('/login');
			return;
		}

		await loadStats();
	});

	async function loadStats() {
		loading = true;
		error = '';

		try {
			const response = await sellerService.getStats();
			if (response.success && response.data) {
				stats = response.data;
			}
		} catch (err: unknown) {
			error = (err as Error).message || 'Failed to load statistics';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Dashboard - TG Seller Platform</title>
</svelte:head>

<div class="min-h-screen bg-[var(--bg-primary)]">
	<Navigation />

	<main class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
		<!-- Header -->
		<div class="mb-8">
			<h1 class="cyber-text-glow mb-2 text-4xl font-bold" style="color: var(--cyber-blue)">
				DASHBOARD
			</h1>
			<p class="text-gray-400">Welcome back to your seller dashboard</p>
		</div>

		{#if loading}
			<Loading loading={true} />
		{:else if error}
			<div class="bg-opacity-20 rounded border border-[var(--cyber-red)] bg-[var(--cyber-red)] p-4">
				<p class="font-semibold">Error loading dashboard</p>
				<p class="mt-1 text-sm">{error}</p>
				<button
					onclick={loadStats}
					class="mt-2 rounded bg-[var(--cyber-red)] px-4 py-2 text-sm font-semibold hover:opacity-80"
				>
					Retry
				</button>
			</div>
		{:else if stats}
			<!-- Stats Grid -->
			<div class="mb-8 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
				<StatCard title="Total Channels" value={stats.total_channels} icon="📡" color="blue" />
				<StatCard title="Active Members" value={stats.active_members} icon="👥" color="green" />
				<StatCard
					title="Total Revenue"
					value={formatCurrency(stats.total_revenue_cents)}
					icon="💰"
					color="purple"
				/>
				<StatCard title="All Members" value={stats.total_members} icon="📈" color="yellow" />
			</div>

			<!-- Quick Actions -->
			<div class="cyber-card">
				<h2 class="mb-4 text-2xl font-bold" style="color: var(--cyber-blue)">Quick Actions</h2>
				<div class="grid grid-cols-1 gap-4 md:grid-cols-3">
					<a
						href={resolve('/channels')}
						class="rounded border border-[var(--border-color)] bg-[var(--bg-tertiary)] p-4 text-center transition-all hover:border-[var(--cyber-blue)]"
					>
						<div class="mb-2 text-3xl">📡</div>
						<div class="font-semibold">Manage Channels</div>
						<div class="text-sm text-gray-400">Add or edit your channels</div>
					</a>
					<a
						href={resolve('/members')}
						class="rounded border border-[var(--border-color)] bg-[var(--bg-tertiary)] p-4 text-center transition-all hover:border-[var(--cyber-blue)]"
					>
						<div class="mb-2 text-3xl">👥</div>
						<div class="font-semibold">View Members</div>
						<div class="text-sm text-gray-400">Manage your subscribers</div>
					</a>
					<a
						href={resolve('/grant-access')}
						class="rounded border border-[var(--border-color)] bg-[var(--bg-tertiary)] p-4 text-center transition-all hover:border-[var(--cyber-blue)]"
					>
						<div class="mb-2 text-3xl">🔑</div>
						<div class="font-semibold">Grant Access</div>
						<div class="text-sm text-gray-400">Give channel access</div>
					</a>
				</div>
			</div>
		{/if}
	</main>
</div>

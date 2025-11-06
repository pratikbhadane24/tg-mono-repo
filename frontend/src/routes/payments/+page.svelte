<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$lib/utils/navigation';
	import Navigation from '$lib/components/Navigation.svelte';
	import Loading from '$lib/components/Loading.svelte';
	import { paymentService } from '$lib/services/payment.service';
	import { authService } from '$lib/services/auth.service';
	import { formatCurrency, formatDate } from '$lib/utils/format';
	import type { Payment } from '$lib/types/api';

	let loading = $state(true);
	let payments: Payment[] = $state([]);
	let error = $state('');

	onMount(async () => {
		if (!authService.isAuthenticated()) {
			goto('/login');
			return;
		}

		await loadPayments();
	});

	async function loadPayments() {
		loading = true;
		error = '';

		try {
			const response = await paymentService.list(100);
			if (response.success && response.data) {
				payments = response.data;
			}
		} catch (err: unknown) {
			error = (err as Error).message || 'Failed to load payments';
		} finally {
			loading = false;
		}
	}

	function getStatusBadgeClass(status: string) {
		switch (status) {
			case 'succeeded':
				return 'badge-success';
			case 'pending':
				return 'badge-warning';
			case 'failed':
				return 'badge-error';
			case 'refunded':
				return 'badge-info';
			default:
				return 'badge-info';
		}
	}
</script>

<svelte:head>
	<title>Payments - TG Seller Platform</title>
</svelte:head>

<div class="min-h-screen bg-[var(--bg-primary)]">
	<Navigation />

	<main class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
		<!-- Header -->
		<div class="mb-8">
			<h1 class="cyber-text-glow mb-2 text-4xl font-bold" style="color: var(--cyber-blue)">
				PAYMENTS
			</h1>
			<p class="text-gray-400">View your payment history and revenue</p>
		</div>

		{#if loading}
			<Loading loading={true} />
		{:else if error}
			<div class="bg-opacity-20 rounded border border-[var(--cyber-red)] bg-[var(--cyber-red)] p-4">
				<p class="font-semibold">Error loading payments</p>
				<p class="mt-1 text-sm">{error}</p>
				<button
					onclick={loadPayments}
					class="mt-2 rounded bg-[var(--cyber-red)] px-4 py-2 text-sm font-semibold hover:opacity-80"
				>
					Retry
				</button>
			</div>
		{:else if payments.length === 0}
			<div class="cyber-card py-12 text-center">
				<div class="mb-4 text-6xl">💰</div>
				<h3 class="mb-2 text-xl font-semibold">No Payments Yet</h3>
				<p class="text-gray-400">Your payment history will appear here</p>
			</div>
		{:else}
			<!-- Summary Cards -->
			<div class="mb-8 grid grid-cols-1 gap-6 md:grid-cols-3">
				<div class="cyber-card">
					<p class="text-sm text-gray-400 uppercase">Total Revenue</p>
					<p class="mt-2 text-3xl font-bold" style="color: var(--cyber-green)">
						{formatCurrency(payments.reduce((sum, p) => sum + p.amount, 0))}
					</p>
				</div>
				<div class="cyber-card">
					<p class="text-sm text-gray-400 uppercase">Total Payments</p>
					<p class="mt-2 text-3xl font-bold" style="color: var(--cyber-blue)">
						{payments.length}
					</p>
				</div>
				<div class="cyber-card">
					<p class="text-sm text-gray-400 uppercase">Success Rate</p>
					<p class="mt-2 text-3xl font-bold" style="color: var(--cyber-purple)">
						{Math.round(
							(payments.filter((p) => p.status === 'succeeded').length / payments.length) * 100
						)}%
					</p>
				</div>
			</div>

			<!-- Payments Table -->
			<div class="cyber-card overflow-x-auto">
				<div class="mb-4 text-sm text-gray-400">
					Showing {payments.length} payment{payments.length !== 1 ? 's' : ''}
				</div>
				<table class="w-full">
					<thead>
						<tr class="border-b border-[var(--border-color)]">
							<th class="px-4 py-3 text-left font-semibold text-[var(--cyber-blue)]">Date</th>
							<th class="px-4 py-3 text-left font-semibold text-[var(--cyber-blue)]">Amount</th>
							<th class="px-4 py-3 text-left font-semibold text-[var(--cyber-blue)]">Currency</th>
							<th class="px-4 py-3 text-left font-semibold text-[var(--cyber-blue)]">Status</th>
							<th class="px-4 py-3 text-left font-semibold text-[var(--cyber-blue)]">Method</th>
							<th class="px-4 py-3 text-left font-semibold text-[var(--cyber-blue)]">Intent ID</th>
						</tr>
					</thead>
					<tbody>
						{#each payments as payment (payment.id)}
							<tr class="border-b border-[var(--border-color)] hover:bg-[var(--bg-tertiary)]">
								<td class="px-4 py-3 text-gray-300">
									{formatDate(payment.created_at)}
								</td>
								<td class="px-4 py-3 font-semibold" style="color: var(--cyber-green)">
									{formatCurrency(payment.amount, payment.currency)}
								</td>
								<td class="px-4 py-3 text-gray-300 uppercase">
									{payment.currency}
								</td>
								<td class="px-4 py-3">
									<span class="badge {getStatusBadgeClass(payment.status)}">
										{payment.status}
									</span>
								</td>
								<td class="px-4 py-3 text-gray-300">
									{payment.used_seller_stripe ? 'Your Stripe' : 'Platform'}
								</td>
								<td class="px-4 py-3 font-mono text-xs text-gray-400">
									{payment.stripe_payment_intent_id}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</main>
</div>

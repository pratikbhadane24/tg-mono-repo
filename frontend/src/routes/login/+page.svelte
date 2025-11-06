<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$lib/utils/navigation';
	import { resolve } from '$app/paths';
	import Button from '$lib/components/Button.svelte';
	import Input from '$lib/components/Input.svelte';
	import { authService } from '$lib/services/auth.service';

	let email = $state('');
	let password = $state('');
	let loading = $state(false);
	let error = $state('');

	onMount(() => {
		if (authService.isAuthenticated()) {
			goto('/dashboard');
		}
	});

	async function handleLogin(e: Event) {
		e.preventDefault();

		if (!email || !password) {
			error = 'Please fill in all fields';
			return;
		}

		loading = true;
		error = '';

		try {
			const response = await authService.login({ email, password });
			if (response.success) {
				goto('/dashboard');
			}
		} catch (err: unknown) {
			error = (err as Error).message || 'Login failed. Please check your credentials.';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Login - TG Seller Platform</title>
</svelte:head>

<div class="relative flex min-h-screen items-center justify-center overflow-hidden p-4">
	<!-- Background Effects -->
	<div class="scan-lines absolute inset-0 opacity-30"></div>
	<div
		class="absolute top-0 left-0 h-96 w-96 animate-pulse rounded-full bg-[var(--cyber-blue)] opacity-20 blur-[150px] filter"
	></div>
	<div
		class="absolute right-0 bottom-0 h-96 w-96 animate-pulse rounded-full bg-[var(--cyber-purple)] opacity-20 blur-[150px] filter"
		style="animation-delay: 1s;"
	></div>

	<!-- Login Card -->
	<div class="cyber-card neon-border relative z-10 w-full max-w-md">
		<div class="mb-8 text-center">
			<h1 class="cyber-text-glow mb-2 text-4xl font-bold" style="color: var(--cyber-blue)">
				SELLER LOGIN
			</h1>
			<p class="text-gray-400">Access your Telegram Seller Dashboard</p>
		</div>

		<form onsubmit={handleLogin}>
			<Input
				label="Email"
				id="email"
				type="email"
				bind:value={email}
				placeholder="seller@example.com"
				required
			/>

			<Input
				label="Password"
				id="password"
				type="password"
				bind:value={password}
				placeholder="••••••••"
				required
			/>

			{#if error}
				<div
					class="bg-opacity-20 mb-4 rounded border border-[var(--cyber-red)] bg-[var(--cyber-red)] p-3 text-sm"
				>
					{error}
				</div>
			{/if}

			<Button type="submit" {loading} variant="primary">
				{#if loading}
					Logging in...
				{:else}
					Login
				{/if}
			</Button>
		</form>

		<div class="mt-6 text-center">
			<p class="text-gray-400">
				Don't have an account?
				<a
					href={resolve('/register')}
					class="font-semibold text-[var(--cyber-blue)] hover:underline"
				>
					Register
				</a>
			</p>
		</div>
	</div>
</div>

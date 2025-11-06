<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$lib/utils/navigation';
	import { resolve } from '$app/paths';
	import Button from '$lib/components/Button.svelte';
	import Input from '$lib/components/Input.svelte';
	import { authService } from '$lib/services/auth.service';

	let email = $state('');
	let password = $state('');
	let companyName = $state('');
	let loading = $state(false);
	let error = $state('');
	let success = $state(false);

	onMount(() => {
		if (authService.isAuthenticated()) {
			goto('/dashboard');
		}
	});

	async function handleRegister(e: Event) {
		e.preventDefault();

		if (!email || !password) {
			error = 'Please fill in all required fields';
			return;
		}

		if (password.length < 8) {
			error = 'Password must be at least 8 characters';
			return;
		}

		loading = true;
		error = '';

		try {
			const response = await authService.register({
				email,
				password,
				company_name: companyName || undefined
			});

			if (response.success) {
				success = true;
				setTimeout(() => {
					goto('/login');
				}, 2000);
			}
		} catch (err: unknown) {
			error = (err as Error).message || 'Registration failed. Please try again.';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Register - TG Seller Platform</title>
</svelte:head>

<div class="relative flex min-h-screen items-center justify-center overflow-hidden p-4">
	<!-- Background Effects -->
	<div class="scan-lines absolute inset-0 opacity-30"></div>
	<div
		class="absolute top-0 right-0 h-96 w-96 animate-pulse rounded-full bg-[var(--cyber-pink)] opacity-20 blur-[150px] filter"
	></div>
	<div
		class="absolute bottom-0 left-0 h-96 w-96 animate-pulse rounded-full bg-[var(--cyber-yellow)] opacity-20 blur-[150px] filter"
		style="animation-delay: 1s;"
	></div>

	<!-- Register Card -->
	<div class="cyber-card neon-border relative z-10 w-full max-w-md">
		<div class="mb-8 text-center">
			<h1 class="cyber-text-glow mb-2 text-4xl font-bold" style="color: var(--cyber-pink)">
				SELLER REGISTRATION
			</h1>
			<p class="text-gray-400">Create your Telegram Seller Account</p>
		</div>

		{#if success}
			<div
				class="bg-opacity-20 mb-4 rounded border border-[var(--cyber-green)] bg-[var(--cyber-green)] p-4 text-center"
			>
				<p class="font-semibold">Registration successful!</p>
				<p class="mt-1 text-sm">Redirecting to login...</p>
			</div>
		{:else}
			<form onsubmit={handleRegister}>
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
					placeholder="At least 8 characters"
					required
				/>

				<Input
					label="Company Name"
					id="companyName"
					type="text"
					bind:value={companyName}
					placeholder="Optional"
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
						Creating Account...
					{:else}
						Register
					{/if}
				</Button>
			</form>

			<div class="mt-6 text-center">
				<p class="text-gray-400">
					Already have an account?
					<a
						href={resolve('/login')}
						class="font-semibold text-[var(--cyber-blue)] hover:underline"
					>
						Login
					</a>
				</p>
			</div>
		{/if}
	</div>
</div>

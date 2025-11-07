<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$lib/utils/navigation';
	import { authService } from '$lib/services/auth.service';

	onMount(async () => {
		const isAuth = await authService.checkAuth();
		if (isAuth) {
			goto('/dashboard');
		} else {
			goto('/login');
		}
	});
</script>

<svelte:head>
	<title>TG Seller Platform</title>
</svelte:head>

<div class="flex min-h-screen items-center justify-center">
	<div class="spinner"></div>
</div>

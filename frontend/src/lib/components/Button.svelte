<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		type?: 'button' | 'submit' | 'reset';
		variant?: 'primary' | 'secondary' | 'danger';
		disabled?: boolean;
		loading?: boolean;
		onclick?: () => void;
		children?: Snippet;
	}

	let {
		type = 'button',
		variant = 'primary',
		disabled = false,
		loading = false,
		onclick,
		children
	}: Props = $props();

	const variantClasses = {
		primary:
			'bg-gradient-to-r from-[var(--cyber-blue)] to-[var(--cyber-purple)] hover:shadow-[0_0_20px_var(--cyber-blue)]',
		secondary:
			'bg-transparent border-2 border-[var(--cyber-blue)] text-[var(--cyber-blue)] hover:bg-[var(--cyber-blue)] hover:text-[var(--bg-primary)]',
		danger:
			'bg-gradient-to-r from-[var(--cyber-red)] to-[var(--cyber-pink)] hover:shadow-[0_0_20px_var(--cyber-red)]'
	};
</script>

<button
	{type}
	class="cyber-button {variantClasses[variant]} {disabled || loading
		? 'cursor-not-allowed opacity-50'
		: ''}"
	{disabled}
	{onclick}
>
	{#if loading}
		<span class="flex items-center gap-2">
			<div class="spinner h-4 w-4 border-2"></div>
			Loading...
		</span>
	{:else if children}
		{@render children()}
	{/if}
</button>

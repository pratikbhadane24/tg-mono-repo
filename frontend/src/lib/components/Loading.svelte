<script lang="ts">
	interface Props {
		loading?: boolean;
		size?: 'small' | 'medium' | 'large';
	}

	let { loading = false, size = 'medium' }: Props = $props();

	const sizeClasses = {
		small: 'w-6 h-6',
		medium: 'w-10 h-10',
		large: 'w-16 h-16'
	};
</script>

{#if loading}
	<div class="flex items-center justify-center p-8">
		<div class="spinner {sizeClasses[size]}"></div>
	</div>
{/if}

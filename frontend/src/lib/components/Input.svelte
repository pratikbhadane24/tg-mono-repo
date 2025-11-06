<script lang="ts">
	interface Props {
		label: string;
		id: string;
		type?: string;
		value?: string | number;
		placeholder?: string;
		required?: boolean;
		disabled?: boolean;
		error?: string;
		onchange?: (value: string) => void;
	}

	let {
		label,
		id,
		type = 'text',
		value = $bindable(''),
		placeholder = '',
		required = false,
		disabled = false,
		error = '',
		onchange
	}: Props = $props();

	function handleChange(e: Event) {
		const target = e.target as HTMLInputElement;
		value = target.value;
		if (onchange) {
			onchange(target.value);
		}
	}
</script>

<div class="mb-4">
	<label for={id} class="mb-2 block text-sm font-medium tracking-wide text-gray-300 uppercase">
		{label}
		{#if required}
			<span class="text-[var(--cyber-pink)]">*</span>
		{/if}
	</label>
	<input
		{id}
		{type}
		{placeholder}
		{required}
		{disabled}
		bind:value
		oninput={handleChange}
		class="cyber-input {error ? 'border-[var(--cyber-red)]' : ''}"
	/>
	{#if error}
		<p class="mt-1 text-sm text-[var(--cyber-red)]">{error}</p>
	{/if}
</div>

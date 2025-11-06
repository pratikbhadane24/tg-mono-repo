<script lang="ts">
	interface Props {
		title: string;
		value: string | number;
		icon?: string;
		color?: 'blue' | 'green' | 'purple' | 'yellow' | 'pink';
	}

	let { title, value, icon = '📊', color = 'blue' }: Props = $props();

	const colorClasses = {
		blue: 'border-cyber-blue shadow-[0_0_20px_rgba(0,240,255,0.2)]',
		green: 'border-cyber-green shadow-[0_0_20px_rgba(5,255,161,0.2)]',
		purple: 'border-cyber-purple shadow-[0_0_20px_rgba(180,41,249,0.2)]',
		yellow: 'border-cyber-yellow shadow-[0_0_20px_rgba(252,238,10,0.2)]',
		pink: 'border-cyber-pink shadow-[0_0_20px_rgba(255,42,109,0.2)]'
	};
</script>

<div class="cyber-card {colorClasses[color]} relative overflow-hidden">
	<div class="flex items-center justify-between">
		<div>
			<p class="text-sm tracking-wider text-gray-400 uppercase">{title}</p>
			<p class="cyber-text-glow mt-2 text-3xl font-bold">{value}</p>
		</div>
		<div class="text-4xl opacity-50">{icon}</div>
	</div>
</div>

<style>
	.border-cyber-blue {
		border-color: var(--cyber-blue);
	}
	.border-cyber-green {
		border-color: var(--cyber-green);
	}
	.border-cyber-purple {
		border-color: var(--cyber-purple);
	}
	.border-cyber-yellow {
		border-color: var(--cyber-yellow);
	}
	.border-cyber-pink {
		border-color: var(--cyber-pink);
	}
</style>

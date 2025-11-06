<script lang="ts">
	import { page } from '$app/stores';
	import { resolve } from '$app/paths';
	import { authService } from '$lib/services/auth.service';

	const navItems = [
		{ path: '/dashboard', label: 'Dashboard', icon: '📊' },
		{ path: '/channels', label: 'Channels', icon: '📡' },
		{ path: '/members', label: 'Members', icon: '👥' },
		{ path: '/payments', label: 'Payments', icon: '💰' },
		{ path: '/grant-access', label: 'Grant Access', icon: '🔑' },
		{ path: '/settings', label: 'Settings', icon: '⚙️' }
	];

	function handleLogout() {
		if (confirm('Are you sure you want to logout?')) {
			authService.logout();
		}
	}
</script>

<nav class="sticky top-0 z-50 border-b border-[var(--border-color)] bg-[var(--bg-card)]">
	<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
		<div class="flex h-16 items-center justify-between">
			<!-- Logo -->
			<div class="flex-shrink-0">
				<a href={resolve('/dashboard')} class="flex items-center gap-2">
					<span class="cyber-text-glow text-2xl font-bold" style="color: var(--cyber-blue)">
						TG SELLER
					</span>
				</a>
			</div>

			<!-- Navigation Links -->
			<div class="hidden items-center space-x-4 md:flex">
				{#each navItems as item (item.path)}
					<a
						href={resolve(item.path)}
						class="rounded-md px-3 py-2 text-sm font-medium transition-all {$page.url.pathname ===
						item.path
							? 'bg-opacity-20 border border-[var(--cyber-blue)] bg-[var(--cyber-blue)] text-[var(--cyber-blue)]'
							: 'text-gray-300 hover:bg-[var(--bg-tertiary)] hover:text-white'}"
					>
						<span class="mr-1">{item.icon}</span>
						{item.label}
					</a>
				{/each}
			</div>

			<!-- Logout Button -->
			<div>
				<button
					onclick={handleLogout}
					class="hover:bg-opacity-20 rounded border border-[var(--cyber-red)] px-4 py-2 text-sm font-medium text-[var(--cyber-red)] transition-all hover:bg-[var(--cyber-red)]"
				>
					Logout
				</button>
			</div>
		</div>
	</div>

	<!-- Mobile Menu -->
	<div class="border-t border-[var(--border-color)] md:hidden">
		<div class="space-y-1 px-2 pt-2 pb-3">
			{#each navItems as item (item.path)}
				<a
					href={resolve(item.path)}
					class="block rounded-md px-3 py-2 text-base font-medium {$page.url.pathname === item.path
						? 'bg-opacity-20 bg-[var(--cyber-blue)] text-[var(--cyber-blue)]'
						: 'text-gray-300 hover:bg-[var(--bg-tertiary)] hover:text-white'}"
				>
					<span class="mr-2">{item.icon}</span>
					{item.label}
				</a>
			{/each}
		</div>
	</div>
</nav>

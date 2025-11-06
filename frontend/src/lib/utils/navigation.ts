import { goto as svelteGoto } from '$app/navigation';
import { resolve } from '$app/paths';

export function goto(path: string) {
	// Use type assertion to bypass strict type checking for dynamic paths
	return svelteGoto(resolve(path) as any);
}

import { goto as svelteGoto } from '$app/navigation';
import { resolve } from '$app/paths';

export function goto(path: string) {
	return svelteGoto(resolve(path));
}

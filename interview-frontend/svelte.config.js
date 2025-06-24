import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://svelte.dev/docs/kit/integrations
	// for more information about preprocessors
	preprocess: vitePreprocess(),

	kit: {
		adapter: adapter(),
		alias: {
		// import 'something' from '$i18n/…'
		$loc: 'src/paraglide',
		'$loc/*': 'src/paraglide/*'   // make sub-paths work too
		}
	}
};

export default config;

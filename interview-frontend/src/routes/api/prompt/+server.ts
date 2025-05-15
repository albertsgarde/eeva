import { BACKEND_ORIGIN } from '$lib/base';

async function reroute(
	{ params, request }: { params: { api_slug: string }; request: Request },
	method: string
) {
	const requestUrl = new URL(request.url);
	const apiUrl = `${BACKEND_ORIGIN}prompt?${requestUrl.searchParams.toString()}`;
	const newRequest = new Request(apiUrl, {
		method: method,
		headers: request.headers,
		body: request.body,
	});
	return fetch(newRequest);
}

export async function GET({ params, request }: { params: { api_slug: string }; request: Request }) {
	return reroute({ params, request }, 'GET');
}
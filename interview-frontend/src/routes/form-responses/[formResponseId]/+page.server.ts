import { BACKEND_ORIGIN, FormResponseId, type FormResponse } from "$lib/base";
import { error } from '@sveltejs/kit';


export interface Data {
    formResponseId: FormResponseId;
    formResponse: FormResponse;
    maxExampleAnswers: number | null;
    showEmail: boolean;
}

export async function load({ params, url, cookies }: { params: { formResponseId: FormResponseId }, url: URL, cookies: any}): Promise<Data> {
    const backendURL = `${BACKEND_ORIGIN}api/form-responses/${params.formResponseId}`;
    const maxExampleAnswersString = url.searchParams.get('maxExampleAnswers');
    const maxExampleAnswers = maxExampleAnswersString === null ? null : parseInt(maxExampleAnswersString);
    
    if (maxExampleAnswers !== null && (maxExampleAnswers < 0 || isNaN(maxExampleAnswers))) {
        throw error(400, "Interview index must be a non-negative integer");
    }

    const response = await fetch(backendURL);
    if (!response.ok) {
        throw error(500, await response.text());
    }

    let showEmail = false;
    if (url.searchParams.has('newFormResponse')) {
        showEmail = true;
        cookies.set("newFormResponse", "true", {
            path: '/',
            httpOnly: true,
            secure: false,
        }
        )
    }

    cookies.set("formResponseId", params.formResponseId.toString(), {
        path: '/',
        httpOnly: true,
        secure: false,
    })

    return { formResponseId: params.formResponseId, formResponse: await response.json(), maxExampleAnswers, showEmail};
}
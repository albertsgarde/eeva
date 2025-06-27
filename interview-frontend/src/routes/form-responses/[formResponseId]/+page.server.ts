import { BACKEND_ORIGIN, FormResponseId, type FormResponse } from "$lib/base";
import { error } from '@sveltejs/kit';


export interface Data {
    formResponseId: FormResponseId;
    formResponse: FormResponse;
    maxExampleAnswers: number | null;
    showEmail: boolean;
}

export async function load({ params, url, cookies }: { params: { formResponseId: FormResponseId }, url: URL, cookies: any}): Promise<Data> {
    const formResponseId = params.formResponseId;
    const backendURL = `${BACKEND_ORIGIN}api/form-responses/${formResponseId}`;
    const maxExampleAnswersString = url.searchParams.get('maxExampleAnswers');
    const maxExampleAnswers = maxExampleAnswersString === null ? null : parseInt(maxExampleAnswersString);
    
    if (maxExampleAnswers !== null && (maxExampleAnswers < 0 || isNaN(maxExampleAnswers))) {
        throw error(400, "Interview index must be a non-negative integer");
    }

    const response = await fetch(backendURL);
    if (!response.ok) {
        throw error(500, await response.text());
    }

    if (url.searchParams.has('newFormResponse') ) {
        cookies.set(`showEmail${formResponseId}`, "true", {
            path: '/',
            httpOnly: true,
            secure: false,
            maxAge: 60 * 60 * 24 * 30 // 30 days
        }
        )
    }

    const showEmail = cookies.get(`showEmail${formResponseId}`) === "true";

    cookies.set("formResponseId", formResponseId.toString(), {
        path: '/',
        httpOnly: true,
        secure: false,
        maxAge: 60 * 60 * 24 * 30 // 30 days
    })

    return { formResponseId, formResponse: await response.json(), maxExampleAnswers, showEmail};
}
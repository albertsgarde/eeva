import { BACKEND_ORIGIN, expect, FormResponseId, ID_PATTERN, QuestionId, type FormResponse, type Question } from "$lib/base";
import { error } from '@sveltejs/kit';


export interface Data {
    formResponseId: FormResponseId;
    formResponse: FormResponse;
    maxExampleAnswers: number | null;
}

export async function load({ params, url }: { params: { formResponseId: FormResponseId }, url: URL}): Promise<Data> {
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

    return { formResponseId: params.formResponseId, formResponse: await response.json(), maxExampleAnswers};
}
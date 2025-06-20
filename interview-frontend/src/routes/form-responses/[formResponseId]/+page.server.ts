import { BACKEND_ORIGIN, expect, FormResponseId, ID_PATTERN, QuestionId, type FormResponse, type Question } from "$lib/base";
import { error } from '@sveltejs/kit';


export interface Data {
    formResponseId: FormResponseId;
    formResponse: FormResponse;
}

export async function load({ params }: { params: { formResponseId: FormResponseId } }): Promise<Data> {
    const url = `${BACKEND_ORIGIN}api/form-responses/${params.formResponseId}`;
    const response = await fetch(url);
    if (!response.ok) {
        throw error(500, await response.text());
    }

    return { formResponseId: params.formResponseId, formResponse: await response.json() };
}
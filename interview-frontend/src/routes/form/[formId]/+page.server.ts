import { BACKEND_ORIGIN, expect, ID_PATTERN, QuestionId, type Question } from "$lib/base";
import { error } from '@sveltejs/kit';


export interface Data {
    questions: { id: QuestionId, question: Question }[];
}

export async function load({ params }: { params: { formId: string } }): Promise<Data> {

    const formId: string = params.formId;
    if (!formId) {
        throw error(404, "Form ID must be a non-empty string");
    }
    if (!ID_PATTERN.test(formId)) {
        throw error(404, `Form ID '${formId}' does not match the required pattern`);
    }

    const url = `${BACKEND_ORIGIN}api/question`;
    const response = await fetch(url);
    if (!response.ok) {
        throw error(500, await response.text());
    }

    return { questions: await response.json() }
}
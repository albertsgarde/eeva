import { expect, PromptId, type CreateInterviewRequest, type FormResponseId, type InterviewId, type Message, type FormId } from "$lib/base";
import { redirect } from "@sveltejs/kit";

async function createFormResponse(
    formId: FormId,
    fetch: (input: RequestInfo, init?: RequestInit) => Promise<Response>
): Promise<{ id: FormResponseId }> {
    const createFormResponseRequest = {
        formId: formId
    };

    const response: { id: FormResponseId } = await fetch(
        `/api/form-responses/create-from-form`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(createFormResponseRequest)
        }
    ).then(async (response) => {
        if (response.status !== 200) {
            const responseText = await response.text();
            throw new Error('Failed to create form response: ' + responseText);
        }
        return response.json();
    });
    return response;
}


export async function load({ fetch, params }: { fetch: any, params: {formId: FormId} }): Promise<void> {
    const {formId} = params;    

    const { id: formResponseId } = await createFormResponse(formId, fetch);
    redirect(303, `/form-responses/${formResponseId}`);
}
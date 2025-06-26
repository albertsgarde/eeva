import type { FormId, FormResponseId } from "$lib/base";

export async function createFormResponse(formId: FormId, fetch: any): Promise<FormResponseId> {
    const createFormResponseRequest = {
        formId,
        subjectName: ''
    };
    const { id: formResponseId }: { id: FormResponseId } = await fetch(
        `/api/form-responses/create-from-form`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(createFormResponseRequest)
        }
    ).then(async (response: any) => {
        if (response.status !== 200) {
            const responseText = await response.text();
            throw new Error('Failed to create form response: ' + responseText);
        }
        return response.json();
    });
    return formResponseId;
}
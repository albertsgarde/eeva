import { FormResponseId, type FormId } from "$lib/base";
import { error, redirect } from "@sveltejs/kit";
import { createFormResponse } from "./utils";

export interface Data {
    formId: FormId;
    formResponseId: FormResponseId;
}

export async function load({ fetch, params, cookies }: { fetch: any, params: {formId: FormId}, cookies: any }): Promise<Data> {
    const {formId} = params;

    const response = await fetch(`/api/forms/${formId}`);
    if (!response.ok) {
        error(404, 'Form not found');
    }

    const prevFormResponseId = cookies.get("formResponseId");
    if (prevFormResponseId) {
        const formResponseId: FormResponseId = parseInt(prevFormResponseId, 10) as unknown as FormResponseId;
        return { formId, formResponseId };
    } else {
        const newFormResponseId: FormResponseId = await createFormResponse(formId, fetch);
        redirect(303, `/form-responses/${newFormResponseId}`);
    }
}

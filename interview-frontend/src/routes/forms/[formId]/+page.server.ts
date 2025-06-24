import { type FormId } from "$lib/base";
import { error } from "@sveltejs/kit";

export interface Data {
    formId: FormId;
}

export async function load({ fetch, params }: { fetch: any, params: {formId: FormId} }): Promise<Data> {
    const {formId} = params;

    const response = await fetch(`/api/forms/${formId}`);
    if (!response.ok) {
        error(404, 'Form not found');
    }

    return { formId };
}

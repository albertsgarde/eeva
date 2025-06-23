import { expect, PromptId, type CreateInterviewRequest, type FormResponseId, type InterviewId, type Message, type FormId } from "$lib/base";

export interface Data {
    formId: FormId;
}

export async function load({ fetch, params }: { fetch: any, params: {formId: FormId} }): Promise<Data> {
    const {formId} = params;    

    return { formId };
}

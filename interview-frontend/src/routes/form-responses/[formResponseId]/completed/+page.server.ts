import { BACKEND_ORIGIN, expect, FormResponseId, ID_PATTERN, QuestionId, type FormResponse, type Question } from "$lib/base";
import { error } from '@sveltejs/kit';


export interface Data {
    formResponseId: FormResponseId;
}

export async function load({ params, url }: { params: { formResponseId: FormResponseId }, url: URL}): Promise<Data> {


    return { formResponseId: params.formResponseId};
}
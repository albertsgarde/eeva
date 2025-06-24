import { FormResponseId } from "$lib/base";


export interface Data {
    formResponseId: FormResponseId;
}

export async function load({ params, url }: { params: { formResponseId: FormResponseId }, url: URL}): Promise<Data> {


    return { formResponseId: params.formResponseId};
}
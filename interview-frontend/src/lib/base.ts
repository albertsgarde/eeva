import { env } from '$env/dynamic/public';
import { z } from 'zod/v4'

export const BACKEND_ORIGIN: URL = new URL(env.PUBLIC_BACKEND_ORIGIN || 'http://localhost:8000');

export function expect<T>(value: T | null, message: string): T {
    if (value === null || value === undefined) {
        throw new Error(message);
    }
    return value;
}

export const InterviewId = z.preprocess((val) => {
    if (typeof val === "number") {
        return {id: val}
    }
    return val
},z.object({
    id: z.int().gt(0)
}).readonly());

export type InterviewId = z.infer<typeof InterviewId>

export const ID_PATTERN = /^[a-zA-Z0-9\-]+$/;

export const PromptId = z.preprocess((val) => {
    if (typeof val ==="string") {
        return {id: val}
    }
    return val
}, z.object({
    id: z.string().regex(ID_PATTERN)
}).readonly());

export type PromptId = z.infer<typeof PromptId>

export interface Message {
    interviewer: boolean;
    content: string;
}


export interface CreateInterviewRequest {
    startMessageId: PromptId;
    interviewerSystemPromptId: PromptId;
    subjectName: string;
}

export const QuestionId = z.preprocess((val) => {
    if (typeof val === "string") {
        return {id: val}
    }
    return val
}, z.object({
    id: z.string().regex(ID_PATTERN)
}).readonly());

export type QuestionId = z.infer<typeof QuestionId>

export interface Question {
    question: string;
    exampleAnswers: string[];
}

export const FormId = z.preprocess((val) => {
    if (typeof val === "string") {
        return {id: val}
    }
    return val
}, z.object({
    id: z.string().regex(ID_PATTERN)
}).readonly());

export type FormId = z.infer<typeof FormId>

export const FormResponseId = z.preprocess((val) => {
    if (typeof val === "number") {
        return {id: val}
    }       
    return val
}, z.object({
    id: z.number().int().gte(0)
}).readonly());

export type FormResponseId = z.infer<typeof FormResponseId>

export interface QuestionResponse {
    questionId: QuestionId;
    question: Question;
    response: string;
}

export interface FormResponse {
    formId: FormId;
    responses: QuestionResponse[];
    subjectName: string;
}
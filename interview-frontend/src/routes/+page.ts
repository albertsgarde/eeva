export async function load({ url, fetch }) {
    const startMessageId = url.searchParams.get('startMessageId');
    const interviewerPromptId = url.searchParams.get('interviewerPromptId');

    const startMessage = await fetch(`/api/prompt?promptId=${startMessageId}`, { method: 'GET' }).then((response) => { return response.json() })
    const interviewerPrompt = await fetch(`/api/prompt?promptId=${interviewerPromptId}`, { method: 'GET' }).then((response) => { return response.json() })

    return {
        startMessage: startMessage,
        interviewerPrompt: interviewerPrompt
    };
};
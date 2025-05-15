export async function load({ url, fetch }) {
    const startMessageId = url.searchParams.get('startMessageId');
    const interviewerPromptId = url.searchParams.get('interviewerPromptId');

    const startMessage = await fetch(`/api/prompt?id=${startMessageId}`, { method: 'GET' }).then((response) => { return response.json() })
    const interviewerPrompt = await fetch(`/api/prompt?id=${interviewerPromptId}`, { method: 'GET' }).then((response) => { return response.json() })

    console.log('startMessage', startMessage);
    console.log('interviewerPrompt', interviewerPrompt);

    return {
        startMessage: startMessage,
        interviewerPrompt: interviewerPrompt
    };
};
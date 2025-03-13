<script lang="ts">
    import Message from "./Message.svelte";
    import MessageInput from "./MessageInput.svelte";
    import type { ChatMessage } from "../types/chat";

    let messages: ChatMessage[] = [];

    async function handleSendMessage(event: CustomEvent<string>) {
        const message = event.detail;

        messages = [...messages, { text: message, isUser: true }];

        try {
            const response = await fetch("/api/v1/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: message, // Wrap the message in an object
                    lesson_id: null, // Optional: Add if you want to filter by lesson
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            // converting ChatResponse into ChatMessage
            console.log(data);
            messages = [
                ...messages,
                { text: data.response, isUser: false },
                {
                    text: data.sources,
                    isUser: false,
                    isSources: true,
                },
            ];
            console.log(messages);
        } catch (error) {
            messages = [
                ...messages,
                {
                    text: "Error al procesar el mensaje",
                    isUser: false,
                    isError: true,
                },
            ];
        }
    }
</script>

<div class="container mx-auto p-4 h-full flex flex-col">
    <h1 class="text-2xl font-bold mb-4">Educational RAG Chat</h1>

    <div class="flex-1 bg-white rounded-lg shadow-md p-4 mb-6 overflow-y-auto">
        {#each messages as message}
            <Message {message} />
        {/each}
    </div>

    <MessageInput on:sendMessage={handleSendMessage} />
</div>

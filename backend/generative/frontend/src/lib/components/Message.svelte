<script lang="ts">
    import type { ChatMessage } from "../types/chat";

    export let message: ChatMessage;
</script>

<div
    class="p-3 rounded-lg mb-2 {message.isUser
        ? 'bg-blue-100 ml-auto'
        : message.isSources
          ? 'text-sm text-gray-600'
          : message.isError
            ? 'bg-red-100'
            : 'bg-gray-100'} max-w-[80%]"
>
    {#if Array.isArray(message.text)}
        <ul class="list-disc pl-4 space-y-1">
            {#each message.text as item}
                <li class="break-words">{item}</li>
            {/each}
        </ul>
    {:else}
        <p class="break-words">{message.text}</p>
    {/if}
</div>

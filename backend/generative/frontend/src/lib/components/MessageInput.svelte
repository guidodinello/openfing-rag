<script lang="ts">
    import { createEventDispatcher } from "svelte";

    const dispatch = createEventDispatcher<{ sendMessage: string }>();
    let messageText = "";

    function handleSubmit() {
        if (messageText.trim()) {
            dispatch("sendMessage", messageText);
            messageText = "";
        }
    }
</script>

<form on:submit|preventDefault={handleSubmit} class="flex gap-2">
    <input
        bind:value={messageText}
        class="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
        placeholder="Escribe tu pregunta aquí..."
    />
    <button
        type="submit"
        class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600"
    >
        Enviar
    </button>
</form>

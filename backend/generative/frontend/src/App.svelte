<script lang="ts">
    import Header from "./lib/Header.svelte";
    import Footer from "./lib/Footer.svelte";
    import Chat from "./lib/components/Chat.svelte";
    let name = "Student";
</script>

<main class="min-h-screen flex flex-col bg-blue-950">
    <Header />

    <div class="flex-1 w-full max-w-4xl mx-auto px-4 py-8">
        <div class="bg-blue-50 rounded-lg shadow-lg h-[800px] flex flex-col">
            <div class="p-4 border-b">
                <h2 class="text-xl font-semibold">Welcome, {name}</h2>
            </div>

            <div class="flex-1 overflow-y-auto p-4">
                <Chat />
            </div>
        </div>
    </div>

    <Footer />
</main>

<style>
</style>

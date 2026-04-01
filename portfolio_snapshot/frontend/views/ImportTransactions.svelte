<script>
    import Button from "@components/Button.svelte";
    import { Toast } from "@utils/toast";

    // State for the selected file and UI feedback
    let fileInput = $state(null);
    let fileName = $state("");
    let isUploading = $state(false);

    function handleFileChange(e) {
        const file = e.target.files[0];
        if (file) {
            fileName = file.name;
        }
    }

    async function handleSubmit(e) {
        e.preventDefault();
        if (!fileInput.files[0]) return alert("Please select a file first.");

        isUploading = true;

        const formData = new FormData();
        formData.append("file", fileInput.files[0]);

        try {
            // Replace with your actual API endpoint
            const response = await fetch(
                "/api/portfolio_snapshot/import_transactions/",
                {
                    method: "POST",
                    body: formData,
                    headers: {
                        "X-CSRFToken": window.csrfToken,
                    },
                },
            );

            if (response.ok) {
                const data = await response.json();
                console.log(data)
                Toast.fire({
                    icon: "success",
                    title: data.message,
                });
                e.target.reset();
            } else {
                alert("Upload failed.");
            }
        } catch (error) {
            console.error("Error:", error);
        } finally {
            isUploading = false;
        }
    }
</script>

<div class="container-fluid py-3">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h3 class="fw-bold mb-0">Import Daily Transactions</h3>
    </div>

    <div class="card border-0 shadow-sm" style="max-width: 600px;">
        <div class="card-body p-4">
            <form onsubmit={handleSubmit}>
                <div class="mb-4">
                    <label for="file-upload" class="form-label fw-medium">
                        Transaction File
                    </label>

                    <input
                        bind:this={fileInput}
                        onchange={handleFileChange}
                        type="file"
                        id="file-upload"
                        class="form-control"
                        accept=".csv, .xlsx"
                        disabled={isUploading}
                    />

                    <div class="form-text">
                        Upload a .csv or .xlsx file containing daily transaction
                        records.
                    </div>
                </div>

                <div class="d-flex justify-content-end">
                    <button
                        type="submit"
                        class="btn btn-primary d-flex align-items-center"
                        disabled={isUploading || !fileName}
                    >
                        {#if isUploading}
                            <span class="spinner-border spinner-border-sm me-2"
                            ></span>
                            Uploading...
                        {:else}
                            <i class="bi bi-cloud-arrow-up me-2"></i> Import Data
                        {/if}
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

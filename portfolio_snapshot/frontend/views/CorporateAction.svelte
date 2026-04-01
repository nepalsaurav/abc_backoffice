<script>
    import Swal from "sweetalert2";
    import { api } from "@utils/api";
    import { Toast } from "@utils/toast";
    import { formatDate } from "@utils/date";
    import Loading from "@components/Loading.svelte";

    // Reactive state for the search term
    let symbolSearchTerm = $state("");

    async function handleSyncCorporateAction(e) {
        e.target.disabled = true;
        Swal.fire({
            title: "Syncing Data",
            html: "Please wait while we fetch corporate actions from ShareSansar...",
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            },
        });

        try {
            const response = await api.get(
                "/api/portfolio_snapshot/sync_corporate_actions/",
            );

            if (response.data.status === "success") {
                Swal.close();
                await Toast.fire({
                    icon: "success",
                    title:
                        response.data.message ||
                        "Successfully synced corporate actions",
                });
            } else {
                throw new Error(response.data.error);
            }
        } catch (error) {
            Swal.close();
            await Toast.fire({
                icon: "error",
                title:
                    error.response?.data?.error ||
                    error.message ||
                    "Sync failed",
            });
        }
        e.target.disabled = false;
    }

    async function getCorporateActions() {
        const data = api.get("/api/portfolio_snapshot/corporate_actions/");
        return data;
    }
</script>

<div class="d-flex flex-row-reverse mb-3">
    <button class="btn btn-primary" onclick={handleSyncCorporateAction}>
        Sync corporate actions
    </button>
</div>

{#await getCorporateActions()}
    <Loading />
{:then value}
    <div class="row mt-4">
        <div class="col-8">
            {@render corporateActionHistory(value.data.corporate_actions)}
        </div>
        <div class="col-4">
            {@render SyncHistory(value.data.sync_history)}
        </div>
    </div>
{:catch error}
    <p class="text-danger">Something went wrong: {error.message}</p>
{/await}

{#snippet corporateActionHistory(records)}
    <div class="card">
        <div class="card-body">
            <input
                type="text"
                class="form-control mb-3"
                placeholder="Filter by Symbol..."
                bind:value={symbolSearchTerm}
            />
            <div class="table-responsive" style="height: 400px;">
                <table class="table table-hover align-middle">
                    <thead class="table-light">
                        <tr>
                            <th>Symbol</th>
                            <th>Type</th>
                            <th>Book Close</th>
                            <th>Listing Date</th>
                            <th class="text-end">Value (%)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each records.filter((item) => item.symbol
                                .toLowerCase()
                                .includes(symbolSearchTerm.toLowerCase())) as item}
                            <tr>
                                <td><strong>{item.symbol}</strong></td>
                                <td>
                                    {item.corporate_action_type}
                                </td>
                                <td>{item.book_close_date}</td>
                                <td>
                                    {item.listing_date}
                                </td>
                                <td class="text-end fw-bold">
                                    {#if item.corporate_action_type === "bonus"}
                                        {parseFloat(item.bonus_pct).toFixed(2)}%
                                    {:else if item.corporate_action_type === "cash_dividend"}
                                        {parseFloat(
                                            item.cash_dividend_pct,
                                        ).toFixed(2)}%
                                    {:else}
                                        {parseFloat(
                                            item.right_share_pct,
                                        ).toFixed(2)}%
                                    {/if}
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
{/snippet}

{#snippet SyncHistory(records)}
    <div class="card">
        <div class="card-body">
            <p class="text-muted fw-bold">Corporate sync history</p>
            <div class="table-responsive" style="height: 400px;">
                <table class="table table-striped align-middle">
                    <thead class="table-light">
                        <tr>
                            <th>Last Fetch Date</th>
                            <th>Status</th>
                            <th>Error</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each records as item}
                            <tr>
                                <td>{formatDate(item.last_fetch_date)}</td>
                                <td>
                                    {#if item.status === "Success"}
                                        <span class="badge text-bg-success"
                                            >Success</span
                                        >
                                    {:else if item.status === "Pending"}
                                        <span class="badge text-bg-warning"
                                            >Pending</span
                                        >
                                    {:else if item.status === "Failed"}
                                        <span class="badge text-bg-danger"
                                            >Failed</span
                                        >
                                    {/if}
                                </td>
                                <td
                                    class="text-truncate"
                                    style="max-width: 150px;"
                                    title={item.error_log}
                                >
                                    {item.error_log || "-"}
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
{/snippet}

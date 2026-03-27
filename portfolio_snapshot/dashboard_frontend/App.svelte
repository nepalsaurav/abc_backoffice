<script>
    import CustomerSelect from "./components/CustomerSelect.svelte";
    import Overview from "./tabs/Overview.svelte";
    import CurrentHolding from "./tabs/CurrentHolding.svelte";
    import SectorDistribution from "./tabs/SectorDistribution.svelte";
    import PnL from "./tabs/PnL.svelte";

    let activeTab = "overview";
    let isLoading = false;

    function setActiveTab(tab) {
        activeTab = tab;
    }

    function handleCustomerSelect(event) {
        isLoading = true;

        // Fake API call delay (1.5 seconds)
        setTimeout(() => {
            isLoading = false;
        }, 1500);
    }
</script>

<div class="container-fluid py-4">
    <!-- Header with Title and Customer Select -->
    <div class="d-flex justify-content-between align-items-center mb-4">
        <!-- Render CustomerSelect and bind selection event -->
        <div class="ms-auto">
            <CustomerSelect on:select={handleCustomerSelect} />
        </div>
    </div>

    <!-- Tabs Navigation -->
    <ul class="nav nav-tabs mb-4">
        <li class="nav-item">
            <button
                class="nav-link {activeTab === 'overview'
                    ? 'active fw-bold'
                    : ''}"
                on:click={() => setActiveTab("overview")}
            >
                Overview
            </button>
        </li>
        <li class="nav-item">
            <button
                class="nav-link {activeTab === 'holdings'
                    ? 'active fw-bold'
                    : ''}"
                on:click={() => setActiveTab("holdings")}
            >
                Current Holding
            </button>
        </li>
        <li class="nav-item">
            <button
                class="nav-link {activeTab === 'sector'
                    ? 'active fw-bold'
                    : ''}"
                on:click={() => setActiveTab("sector")}
            >
                Sector Distribution
            </button>
        </li>
        <li class="nav-item">
            <button
                class="nav-link {activeTab === 'pnl' ? 'active fw-bold' : ''}"
                on:click={() => setActiveTab("pnl")}
            >
                P&L
            </button>
        </li>
    </ul>

    <!-- Tab Content Area -->
    <div class="tab-content position-relative" style="min-height: 400px;">
        {#if isLoading}
            <div
                class="position-absolute w-100 h-100 d-flex flex-column justify-content-center align-items-center bg-white rounded-3 shadow-sm"
                style="z-index: 10; opacity: 0.95;"
            >
                <div
                    class="spinner-border text-primary ms-auto me-auto mb-3"
                    role="status"
                    style="width: 3rem; height: 3rem;"
                >
                    <span class="visually-hidden">Loading...</span>
                </div>
                <h5 class="text-muted fw-bold">
                    Fetching Portfolio Profile...
                </h5>
            </div>
        {/if}

        <div
            style={isLoading
                ? "opacity: 0.3; pointer-events: none; transition: opacity 0.3s;"
                : "transition: opacity 0.3s;"}
        >
            {#if activeTab === "overview"}
                <Overview />
            {:else if activeTab === "holdings"}
                <CurrentHolding />
            {:else if activeTab === "sector"}
                <SectorDistribution />
            {:else if activeTab === "pnl"}
                <PnL />
            {/if}
        </div>
    </div>
</div>

<style>
    .nav-tabs .nav-link {
        color: #495057;
        cursor: pointer;
        border: none;
        border-bottom: 2px solid transparent;
        padding: 0.75rem 1rem;
    }
    .nav-tabs .nav-link:hover {
        border-color: transparent;
        border-bottom: 2px solid #dee2e6;
    }
    .nav-tabs .nav-link.active {
        color: #0d6efd;
        background-color: transparent;
        border-bottom: 2px solid #0d6efd;
    }
</style>

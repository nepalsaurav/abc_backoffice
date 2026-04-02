<script>
  import { onMount } from "svelte";
  import { api } from "@utils/api";
  import Loading from "@components/Loading.svelte";
  import TransactionsHistory from "../components/TransactionsHistory.svelte";
  import SectorDistribution from "../components/SectorDistribution.svelte";
  import Overview from "../components/Overview.svelte";
    import ProfitAndLoss from "../components/ProfitAndLoss.svelte";

  // State for the Client Dropdown
  let client_name = $state("");
  let clientList = $state([]);
  let isClientsLoading = $state(true);

  // State for the Dashboard
  let portfolioDetails = $state(null);
  let error = $state(null);
  let activeTab = $state("overview");

  // Fetch the list of customers exactly once when the component loads
  onMount(() => {
    api
      .get("/api/portfolio_snapshot/customer_list/")
      .then((res) => {
        clientList = res.data.resp;
        // Removed the auto-select logic so the user must choose manually
      })
      .catch((err) => {
        console.error("Failed to load customer list:", err);
      })
      .finally(() => {
        isClientsLoading = false;
      });
  });

  function setActiveTab(tab) {
    activeTab = tab;
  }

  // Reactively fetch dashboard data whenever `client_name` changes
  $effect(() => {
    // Prevent API call if client_name is empty (waiting for user selection)
    if (!client_name) return;

    // Reset states before fetching new client data
    portfolioDetails = null;
    error = null;

    api
      .get(`/api/portfolio_snapshot/dashboard?client_name=${client_name}`)
      .then((value) => {
        portfolioDetails = value.data.result;
      })
      .catch((err) => {
        error = err;
      });
  });

  function calculatePortfolioValue(portfolioHistory) {
    const activeHoldings = Object.entries(portfolioHistory).filter(([key, val]) => val.length > 0);

    const currentHoldings = activeHoldings.map(([company, transactions]) => {
      const totals = transactions.reduce(
        (acc, transaction) => {
          acc.totalQty += transaction.qty;
          acc.totalCost += transaction.cost_of_buying;
          return acc;
        },
        { totalQty: 0, totalCost: 0 },
      );

      const averageCost = totals.totalQty > 0 ? totals.totalCost / totals.totalQty : 0;
      return [
        company,
        {
          qty: totals.totalQty,
          average_cost: Number(averageCost.toFixed(4)),
        },
      ];
    });
    return currentHoldings;
  }
</script>

<div class="mb-4 d-flex gap-4 align-items-center">
  <label for="clientSelect" class="form-label fw-bold mb-0">Select Client</label>

  {#if isClientsLoading}
    <select class="form-select" disabled style="width: 20rem;">
      <option>Loading clients...</option>
    </select>
  {:else if clientList.length === 0}
    <select class="form-select" disabled style="width: 20rem;">
      <option>No clients found</option>
    </select>
  {:else}
    <select id="clientSelect" class="form-select" style="width: 20rem;" bind:value={client_name}>
      <option value="" disabled selected>-- Select a Client --</option>
      {#each clientList as client}
        <option value={client}>{client}</option>
      {/each}
    </select>
  {/if}
</div>

{#if error}
  <div class="alert alert-danger">Error: {error.message || error}</div>
{:else if !client_name}
  <div class="alert alert-info">Please select a client from the dropdown above to view their portfolio dashboard.</div>
{:else if !portfolioDetails}
  <Loading />
{:else}
  <ul class="nav nav-tabs mb-4">
    <li class="nav-item">
      <button
        class="nav-link {activeTab === 'overview' ? 'active fw-bold' : ''}"
        onclick={() => setActiveTab("overview")}>
        Overview
      </button>
    </li>
  
    <li class="nav-item">
      <button class="nav-link {activeTab === 'sector' ? 'active fw-bold' : ''}" onclick={() => setActiveTab("sector")}>
        Sector Distribution
      </button>
    </li>
    <li class="nav-item">
      <button
        class="nav-link {activeTab === 'transaction_history' ? 'active fw-bold' : ''}"
        onclick={() => setActiveTab("transaction_history")}>
        Transaction History
      </button>
    </li>
    <li class="nav-item">
      <button class="nav-link {activeTab === 'pnl' ? 'active fw-bold' : ''}" onclick={() => setActiveTab("pnl")}>
        P&L
      </button>
    </li>
  </ul>

  {#if activeTab === "overview"}
    <Overview holdings={portfolioDetails.current_balance} />
  {/if}

  {#if activeTab === "sector"}
    <SectorDistribution holdings={portfolioDetails.current_balance} />
  {/if}

  {#if activeTab === "transaction_history"}
    <TransactionsHistory history={portfolioDetails.client_ledger} />
  {/if}

  {#if activeTab === "pnl"}
    <ProfitAndLoss ledger={portfolioDetails.client_ledger} />
  {/if}
{/if}

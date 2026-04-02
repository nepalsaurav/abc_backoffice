<script>
  import { api } from "@utils/api";
  import Loading from "@components/Loading.svelte";
  import TransactionsHistory from "../components/TransactionsHistory.svelte";
  import CurrentHolding from "../components/CurrentHolding.svelte";
  import SectorDistribution from "../components/SectorDistribution.svelte";
  import Overview from "../components/Overview.svelte";

  let client_name = $state("LATA CHAUDHARY (LC456959)");
  let portfolioDetails = $state(null);
  let error = $state(null);
  let activeTab = $state("overview");

  function setActiveTab(tab) {
    activeTab = tab;
  }

  $effect(() => {
    // Reset states before fetching
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

{#if error}
  <p style="color: red;">Error: {error.message || error}</p>
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
      <button
        class="nav-link {activeTab === 'holdings' ? 'active fw-bold' : ''}"
        onclick={() => setActiveTab("holdings")}>
        Current Holding
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

  {#if activeTab === "holdings"}
    <!-- <CurrentHolding holdings={portfolioDetails.portfolio_history} /> -->
  {/if}

  {#if activeTab === "sector"}
    <SectorDistribution holdings={calculatePortfolioValue(portfolioDetails.portfolio_history)} />
  {/if}

  {#if activeTab === "transaction_history"}
    <TransactionsHistory history={portfolioDetails.client_ledger} />
  {/if}
{/if}

<script>
  import { onMount } from "svelte";
  import { api } from "@utils/api";
  import { Chart } from "chart.js/auto";
  import Loading from "@components/Loading.svelte";

  let { holdings } = $props();

  // Tab State
  let activeTab = $state("sector"); // can be "sector" or "symbol"

  // We only need ONE canvas and ONE chart instance now
  let chartCanvas = $state(null);
  let chartInstance = null;

  // Data states
  let sectorMap = $state({});
  let isLoading = $state(true);
  let error = $state(null);
  let unknownSymbols = $derived.by(() => {
    if (!holdings) return [];
    const tempUnknownSymbols = [];
    holdings.forEach((h) => {
      const symbol = h.symbol;
      const sector = sectorMap[symbol] || "Unknown / Merged Stock";
      if (sector === "Unknown / Merged Stock" && !tempUnknownSymbols.includes(symbol)) {
        tempUnknownSymbols.push(symbol);
      }
    });
    return tempUnknownSymbols;
  });

  // 1. Fetch Sector Data on Mount
  onMount(() => {
    api
      .get("/api/portfolio_snapshot/nepse_sector/")
      .then((res) => {
        const map = {};
        res.data.resp.forEach((item) => {
          map[item.ticker] = item.sector;
        });
        sectorMap = map;
      })
      .catch((err) => {
        error = err;
        console.error("Failed to fetch sector data:", err);
      })
      .finally(() => {
        isLoading = false;
      });
  });

  // 2. Reactively Draw Chart when data or activeTab changes
  $effect(() => {
    // Wait until loading is done, holdings exist, and canvas is in the DOM
    if (isLoading || !holdings || !chartCanvas) return;

    const sectorTotals = {};
    const symbolTotals = {};

    // Group the data
    holdings.forEach((h) => {
      const value = h.total_investment_amount ?? h.qty * h.wacc;
      const symbol = h.symbol;
      const sector = sectorMap[symbol] || "Unknown / Merged Stock";

      symbolTotals[symbol] = (symbolTotals[symbol] || 0) + value;
      sectorTotals[sector] = (sectorTotals[sector] || 0) + value;
    });

    // Determine which data to use based on the currently active tab
    const chartData = activeTab === "sector" ? sectorTotals : symbolTotals;

    // Destroy the previous chart before drawing the new one to prevent overlap
    if (chartInstance) chartInstance.destroy();

    const generateColors = (count) => {
      return Array.from({ length: count }, (_, i) => `hsl(${(i * 360) / count}, 70%, 55%)`);
    };

    const tooltipOptions = {
      callbacks: {
        label: function (context) {
          let label = context.label || "";
          if (label) label += ": ";
          const value = context.parsed;
          const total = context.dataset.data.reduce((acc, val) => acc + val, 0);
          const percentage = ((value / total) * 100).toFixed(2) + '%';
          label += "Rs. " + value.toLocaleString("en-IN", { minimumFractionDigits: 2 }) + ` (${percentage})`;
          return label;
        },
      },
    };

    // Draw the active chart
    chartInstance = new Chart(chartCanvas, {
      type: "pie",
      data: {
        labels: Object.keys(chartData),
        datasets: [
          {
            data: Object.values(chartData),
            backgroundColor: generateColors(Object.keys(chartData).length),
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: "bottom" },
          tooltip: tooltipOptions,
        },
      },
    });

    // Cleanup: Destroys the chart if the component is unmounted or if the effect re-runs
    return () => {
      if (chartInstance) chartInstance.destroy();
    };
  });
</script>

{#if isLoading}
  <Loading />
{:else if error}
  <div class="alert alert-danger">Error loading sector mapping: {error.message}</div>
{:else}
  <div class="card shadow-sm mt-4" style="max-width: {unknownSymbols.length > 0 && activeTab === 'sector' ? '900px' : '600px'};">
    <div class="card-header bg-white pb-0 border-bottom-0">
      <ul class="nav nav-tabs">
        <li class="nav-item">
          <button
            class="nav-link {activeTab === 'sector' ? 'active fw-bold' : 'text-muted'}"
            onclick={() => (activeTab = "sector")}>
            Sector Distribution
          </button>
        </li>
        <li class="nav-item">
          <button
            class="nav-link {activeTab === 'symbol' ? 'active fw-bold' : 'text-muted'}"
            onclick={() => (activeTab = "symbol")}>
            Symbol Distribution
          </button>
        </li>
      </ul>
    </div>

    <div class="card-body pt-4">
      <div class="row align-items-center">
        <!-- Chart Column -->
        <div class="{unknownSymbols.length > 0 && activeTab === 'sector' ? 'col-md-7 border-end' : 'col-12'} d-flex flex-column align-items-center">
          <div style="position: relative; width: 100%; max-width: 400px;">
            <canvas bind:this={chartCanvas}></canvas>
          </div>
        </div>
        
        <!-- Unknown Symbols Column -->
        {#if unknownSymbols.length > 0 && activeTab === "sector"}
          <div class="col-md-5 mt-4 mt-md-0">
            <div class="p-4 bg-light rounded-3 h-100 shadow-sm border-0 position-relative overflow-hidden">
              <div class="position-absolute top-0 start-0 w-100 h-100" style="background-color: #d97706; opacity: 0.05;"></div>
              <div class="position-absolute top-0 start-0 h-100" style="width: 4px; background-color: #d97706;"></div>
              
              <div class="position-relative z-1">
                <h6 class="fw-bold mb-3 d-flex align-items-center" style="color: #d97706;">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-info-circle-fill me-2" viewBox="0 0 16 16">
                    <path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm.93-9.412-1 4.705c-.07.34.029.533.304.533.194 0 .487-.07.686-.246l-.088.416c-.287.346-.92.598-1.465.598-.703 0-1.002-.422-.808-1.319l.738-3.468c.064-.293.006-.399-.287-.47l-.451-.081.082-.381 2.29-.287zM8 5.5a1 1 0 1 1 0-2 1 1 0 0 1 0 2z"/>
                  </svg>
                  Unknown / Merged
                </h6>
                <p class="text-muted small mb-3" style="line-height: 1.5;">
                  The following symbols could not be matched to a sector. They typically belong to companies that have recently merged, changed their ticker symbol, or been delisted.
                </p>
                <div class="d-flex flex-wrap gap-2">
                  {#each unknownSymbols as sym}
                    <span class="badge bg-white text-dark border shadow-sm px-2 py-1" style="font-size: 0.8rem;">{sym}</span>
                  {/each}
                </div>
              </div>
            </div>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

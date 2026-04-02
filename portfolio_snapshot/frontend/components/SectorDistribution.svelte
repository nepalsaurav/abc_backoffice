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

  // 1. Fetch Sector Data on Mount
  onMount(() => {
    api
      .get("/api/portfolio_snapshot/nepse_sector/")
      .then((res) => {
        const map = {};
        res.data.resp.forEach((item) => {
          map[item.symbol] = item.sectorName;
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
      const sector = sectorMap[symbol] || "Unknown Sector";

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
          label += "Rs. " + context.parsed.toLocaleString("en-IN", { minimumFractionDigits: 2 });
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
  <div class="card shadow-sm mt-4" style="max-width: 600px;">
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

    <div class="card-body d-flex flex-column align-items-center pt-4">
      <div style="position: relative; width: 100%; max-width: 400px;">
        <canvas bind:this={chartCanvas}></canvas>
      </div>
    </div>
  </div>
{/if}

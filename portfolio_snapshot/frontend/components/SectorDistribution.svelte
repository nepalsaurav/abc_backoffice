<script>
  import { Chart } from "chart.js/auto";

  let { holdings } = $props();

  let canvasRef = $state(null);
  let chartInstance = null;
  let activeTab = $state("company");

  const DEMO_SECTORS = ["Technology", "Finance", "Healthcare", "Energy", "Consumer Goods"];

  $effect(() => {
    if (!canvasRef || !holdings || holdings.length === 0) return;

    let labels = [];
    let data = [];
    let quantities = [];

    if (activeTab === "company") {
      labels = holdings.map((item) => item[0]);
      data = holdings.map((item) => item[1].qty * item[1].average_cost);
      quantities = holdings.map((item) => item[1].qty);
    } else if (activeTab === "sector") {
      const sectorAggregation = {};

      holdings.forEach((item, index) => {
        const sector = DEMO_SECTORS[index % DEMO_SECTORS.length];
        const value = item[1].qty * item[1].average_cost;
        const qty = item[1].qty;

        if (!sectorAggregation[sector]) {
          sectorAggregation[sector] = { value: 0, qty: 0 };
        }

        sectorAggregation[sector].value += value;
        sectorAggregation[sector].qty += qty;
      });

      labels = Object.keys(sectorAggregation);
      data = Object.values(sectorAggregation).map((s) => s.value);
      quantities = Object.values(sectorAggregation).map((s) => s.qty);
    }

    if (chartInstance) {
      chartInstance.destroy();
    }

    chartInstance = new Chart(canvasRef, {
      type: "pie",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Total Value",
            data: data,
            customQuantities: quantities,
            backgroundColor: [
              "#FF6384",
              "#36A2EB",
              "#FFCE56",
              "#4BC0C0",
              "#9966FF",
              "#FF9F40",
              "#C9CBCF",
              "#FFCD56",
              "#4BC0C0",
              "#36A2EB",
            ],
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          tooltip: {
            callbacks: {
              label: function (context) {
                let label = context.label || "";
                if (label) {
                  label += ": ";
                }
                const value = context.parsed;
                label += new Intl.NumberFormat().format(value);
                const qty = context.dataset.customQuantities[context.dataIndex];
                label += ` (Qty: ${qty})`;
                return label;
              },
            },
          },
        },
      },
    });

    return () => {
      if (chartInstance) {
        chartInstance.destroy();
      }
    };
  });
</script>

<div style="display: flex;">
  <div style="position: relative; height: 350px; width: 100%;">
    {#if activeTab === "company"}
      <p class="text-center fw-bold">Company Wise Distribution</p>
    {:else}
      <p class="text-center fw-bold">Sector Wise Distribution</p>
    {/if}
    <canvas bind:this={canvasRef}></canvas>
  </div>

  <div style="display: flex; flex-direction: column; justify-content: center;">
    <button
      onclick={() => (activeTab = "company")}
      class="btn {activeTab === 'company' ? 'btn-primary' : 'btn-secondary'}">
      Company
    </button>

    <button
      onclick={() => (activeTab = "sector")}
      class="btn mt-2 {activeTab === 'sector' ? 'btn-primary' : 'btn-secondary'}">
      Sector
    </button>
  </div>
</div>

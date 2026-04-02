<script>
  import { api } from "@utils/api";
  import Loading from "@components/Loading.svelte";

  const props = $props();

  function getPrice() {
    return api.get("/api/portfolio_snapshot/price");
  }

  function calculatePortfolioValue(holdings, price) {
    const priceMap = price.reduce((acc, e) => {
      acc[e.symbol] = e;
      return acc;
    }, {});

    const h = holdings.map((element) => {
      // Safely grab prices, fallback to 0 if something is completely missing
      const currentPrice = priceMap[element.symbol]?.closePrice ?? priceMap[element.symbol]?.lastTradedPrice ?? 0;
      const prevPrice = priceMap[element.symbol]?.previousClose ?? 0;

      // Extract quantities based on your provided JSON structure
      const actualQty = element.qty || 0;
      const provQty = element.provisional_qty || 0;
      const totalQty = actualQty + provQty;

      // Calculate the segmented values
      const actualValue = actualQty * currentPrice;
      const provisionalValue = provQty * currentPrice;
      const totalValue = totalQty * currentPrice;

      const previousTotalValue = totalQty * prevPrice;
      const holdingDayChange = totalValue - previousTotalValue;

      return {
        symbol: element.symbol,
        wacc: element.wacc,
        qty: actualQty,
        provisionalQty: provQty,
        totalQty: totalQty,
        currentPrice: currentPrice,
        actualValue: actualValue,
        provisionalValue: provisionalValue,
        totalValue: totalValue,
        dayChange: holdingDayChange,
      };
    });

    const currentPortfolioValue = h.reduce((total, e) => total + e.totalValue, 0);
    const totalDayChange = h.reduce((total, e) => total + e.dayChange, 0);

    // Return the totals AND the array of individual holdings
    return {
      currentPortfolioValue,
      totalDayChange,
      individualHoldings: h,
    };
  }
</script>

{#await getPrice()}
  <Loading />
{:then value}
  {@const data = calculatePortfolioValue(props.holdings, value.data.resp)}

  <div class="card shadow-sm mb-5" style="max-width: 400px;">
    <div class="card-body">
      <h6 class="card-subtitle mb-2 text-muted">Current Portfolio Value</h6>

      <h2 class="card-title mb-1">
        Rs. {data.currentPortfolioValue.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </h2>

      <div class="d-flex align-items-center mt-3">
        <span class="me-2 text-muted">Day Change:</span>
        <span class="fw-bold {data.totalDayChange >= 0 ? 'text-success' : 'text-danger'}">
          {data.totalDayChange >= 0 ? "+" : ""}{data.totalDayChange.toLocaleString("en-IN", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}
        </span>
      </div>

      <small class="text-muted mt-2 d-block">* Includes provisional shares</small>
    </div>
  </div>

  <div class="table-responsive">
    <h5 class="mb-3 fw-bold">Holdings Breakdown</h5>
    <table class="table table-hover table-bordered align-middle">
      <thead class="table-light">
        <tr>
          <th>Symbol</th>
          <th class="text-end">Actual Qty</th>
          <th class="text-end">Prov. Qty</th>
          <th class="text-end">WACC</th>
          <th class="text-end">LTP</th>
          <th class="text-end">Actual Value</th>
          <th class="text-end">Prov. Value</th>
          <th class="text-end text-primary">Total Value</th>
          <th class="text-end">Day Change</th>
        </tr>
      </thead>
      <tbody>
        {#each data.individualHoldings as item}
          <tr>
            <td class="fw-bold">{item.symbol}</td>
            <td class="text-end">{item.qty.toLocaleString("en-IN")}</td>
            
            <td class="text-end {item.provisionalQty > 0 ? 'text-success fw-bold' : 'text-muted'}">
              {item.provisionalQty > 0 ? item.provisionalQty.toLocaleString("en-IN") : "-"}
            </td>
            
            <td class="text-end"
              >{item.wacc.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
            <td class="text-end"
              >{item.currentPrice.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
            <td class="text-end"
              >{item.actualValue.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
            <td class="text-end"
              >{item.provisionalValue.toLocaleString("en-IN", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}</td>
            <td class="text-end fw-bold text-primary"
              >{item.totalValue.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
            <td class="text-end fw-bold {item.dayChange >= 0 ? 'text-success' : 'text-danger'}">
              {item.dayChange >= 0 ? "+" : ""}{item.dayChange.toLocaleString("en-IN", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </td>
          </tr>
        {:else}
          <tr>
            <td colspan="9" class="text-center py-4 text-muted">No holdings available.</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{:catch error}
  <div class="alert alert-danger">
    <p class="mb-0">Failed to load prices: {error.message}</p>
  </div>
{/await}
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
      // Safely grab prices, fallback to 100 if something is completely missing (e.g., merged/halted companies)
      const currentPrice = priceMap[element.symbol]?.closePrice ?? priceMap[element.symbol]?.lastTradedPrice ?? 100;
      const prevPrice = priceMap[element.symbol]?.previousClose ?? 100;

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

      // Calculate Unrealized Gain/Loss
      const wacc = element.wacc || 0;
      const totalInvestment = totalQty * wacc;
      const unrealizedGain = totalValue - totalInvestment;

      return {
        symbol: element.symbol,
        wacc: wacc,
        qty: actualQty,
        provisionalQty: provQty,
        totalQty: totalQty,
        currentPrice: currentPrice,
        actualValue: actualValue,
        provisionalValue: provisionalValue,
        totalValue: totalValue,
        dayChange: holdingDayChange,
        totalInvestment: totalInvestment,
        unrealizedGain: unrealizedGain,
      };
    });

    const currentPortfolioValue = h.reduce((total, e) => total + e.totalValue, 0);
    const totalDayChange = h.reduce((total, e) => total + e.dayChange, 0);
    const totalUnrealizedGain = h.reduce((total, e) => total + e.unrealizedGain, 0);

    // Return the totals AND the array of individual holdings
    return {
      currentPortfolioValue,
      totalDayChange,
      totalUnrealizedGain,
      individualHoldings: h,
    };
  }
</script>

{#await getPrice()}
  <Loading />
{:then value}
  {@const data = calculatePortfolioValue(props.holdings, value.data.resp)}

  <div class="card shadow-sm mb-5" style="max-width: 450px;">
    <div class="card-body">
      <h6 class="card-subtitle mb-2 text-muted">Current Portfolio Value</h6>

      <h2 class="card-title mb-3">
        Rs. {data.currentPortfolioValue.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </h2>

      <div class="d-flex justify-content-between align-items-center mt-3 border-top pt-3">
        <div>
          <span class="text-muted d-block" style="font-size: 0.9rem;">Day Change</span>
          <span class="fw-bold {data.totalDayChange >= 0 ? 'text-success' : 'text-danger'}">
            {data.totalDayChange >= 0 ? "+" : ""}{data.totalDayChange.toLocaleString("en-IN", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </span>
        </div>
        <div class="text-end">
          <span class="text-muted d-block" style="font-size: 0.9rem;">Total Unrealized Gain</span>
          <span class="fw-bold {data.totalUnrealizedGain >= 0 ? 'text-success' : 'text-danger'}">
            {data.totalUnrealizedGain >= 0 ? "+" : ""}{data.totalUnrealizedGain.toLocaleString("en-IN", {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </span>
        </div>
      </div>

      <div class="mt-3 bg-light p-2 rounded">
        <small class="text-muted d-block mb-1">* Includes provisional shares.</small>
        <small class="text-muted d-block">** Disclaimer: For merged or unlisted companies where price data is unavailable, the current price is assumed as 100.</small>
      </div>
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
          <th class="text-end">Unrealized Gain</th>
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
            <td class="text-end fw-bold {item.unrealizedGain >= 0 ? 'text-success' : 'text-danger'}">
              {item.unrealizedGain >= 0 ? "+" : ""}{item.unrealizedGain.toLocaleString("en-IN", {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </td>
          </tr>
        {:else}
          <tr>
            <td colspan="10" class="text-center py-4 text-muted">No holdings available.</td>
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
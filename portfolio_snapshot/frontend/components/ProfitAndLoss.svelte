<script>
  let { ledger = [] } = $props();

  let activeTab = $state("summary");

  let pnl = $derived.by(() => {
    const sellTransactions = ledger.filter((t) => t.transaction_type === "Sell");

    let summary = {
      salesValue: 0,
      investmentCost: 0,
      totalFees: 0,
      grossCapitalGain: 0,
      cgt: 0,
      netProfit: 0,
    };

    const details = sellTransactions.map((t) => {
      // Aggregate all fees
      const f = t.fees || {};
      const fees = (f.broker || 0) + (f.sebo || 0) + (f.nepse || 0) + (f.dp_charge || 0) + (f.regulatory || 0);

      const salesValue = t.gross_amount || 0;
      const investmentCost = (t.out_qty || 0) * (t.wacc || 0);
      const grossGain = t.capital_gain || 0;
      const cgt = t.cgt_total || 0;
      const netProfit = grossGain - cgt;

      // Add to summary totals
      summary.salesValue += salesValue;
      summary.investmentCost += investmentCost;
      summary.totalFees += fees;
      summary.grossCapitalGain += grossGain;
      summary.cgt += cgt;
      summary.netProfit += netProfit;

      return {
        date: t.date,
        trn_no: t.trn_no,
        symbol: t.symbol,
        qty: t.out_qty,
        rate: t.rate,
        wacc: t.wacc,
        salesValue,
        fees,
        cgt,
        grossGain,
        netProfit,
      };
    });

    const symbolMap = {};
    details.forEach((d) => {
      if (!symbolMap[d.symbol]) {
        symbolMap[d.symbol] = {
          symbol: d.symbol,
          totalQty: 0,
          salesValue: 0,
          fees: 0,
          cgt: 0,
          grossGain: 0,
          netProfit: 0,
        };
      }
      symbolMap[d.symbol].totalQty += d.qty;
      symbolMap[d.symbol].salesValue += d.salesValue;
      symbolMap[d.symbol].fees += d.fees;
      symbolMap[d.symbol].cgt += d.cgt;
      symbolMap[d.symbol].grossGain += d.grossGain;
      symbolMap[d.symbol].netProfit += d.netProfit;
    });

    return {
      summary,
      grouped: Object.values(symbolMap).sort((a, b) => b.netProfit - a.netProfit),
      details: details.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()),
    };
  });
</script>


<div class="container-fluid p-0 mt-4">
  <div class="row gx-4 mb-4">
    <div class="col-lg-5 mb-3">
      <div class="card shadow-sm border-0 h-100 text-dark">
        <div class="card-header bg-white border-bottom-0 pt-4 pb-0">
          <h5 class="fw-bold mb-0">Realized Profit & Loss Statement</h5>
          <p class="small" style="opacity: 0.8;">Consolidated summary of all sell transactions</p>
        </div>
        <div class="card-body">
          <div class="d-flex justify-content-between mb-2">
            <span>Total Sales Revenue</span>
            <span class="fw-medium">Rs. {pnl.summary.salesValue.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
          </div>
          <div class="d-flex justify-content-between mb-2">
            <span>Less: Investment Cost (WACC)</span>
            <span>(Rs. {pnl.summary.investmentCost.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })})</span>
          </div>
          <div class="d-flex justify-content-between mb-3">
            <span>Less: Trading Fees</span>
            <span>(Rs. {pnl.summary.totalFees.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })})</span>
          </div>
          
          <hr style="opacity: 0.2;" />
          
          <div class="d-flex justify-content-between mb-3">
            <span class="fw-bold">Gross Capital Gain</span>
            <span class="fw-bold {pnl.summary.grossCapitalGain >= 0 ? 'text-success' : 'text-danger'}">
              Rs. {pnl.summary.grossCapitalGain.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>
          
          <div class="d-flex justify-content-between mb-3">
            <span>Less: Capital Gains Tax (CGT)</span>
            <span>(Rs. {pnl.summary.cgt.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })})</span>
          </div>

          <hr style="opacity: 0.5;" />
          
          <div class="d-flex justify-content-between align-items-center mt-2">
            <span class="fw-bold fs-5">Net Realized Profit</span>
            <span class="fw-bold fs-4 {pnl.summary.netProfit >= 0 ? 'text-success' : 'text-danger'}">
              {pnl.summary.netProfit >= 0 ? "+" : ""} Rs. {pnl.summary.netProfit.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div class="col-lg-7 mb-3 d-flex flex-column gap-3">
      <div class="card shadow-sm border-0 flex-grow-1 text-dark">
        <div class="card-body d-flex align-items-center">
          <div>
            <h6 class="text-uppercase mb-1" style="font-size: 0.8rem; letter-spacing: 0.5px; opacity: 0.8;">Performance Highlight</h6>
            <h4 class="mb-0">
              You have locked in <span class="fw-bold {pnl.summary.netProfit >= 0 ? 'text-success' : 'text-danger'}">
                Rs. {pnl.summary.netProfit.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span> 
              in {pnl.summary.netProfit >= 0 ? 'profits' : 'losses'} after all taxes and fees.
            </h4>
          </div>
        </div>
      </div>
      <div class="row h-50">
        <div class="col-sm-6 mb-3 mb-sm-0">
          <div class="card shadow-sm border-0 h-100 text-dark" style="background-color: #f8f9fa;">
            <div class="card-body d-flex flex-column justify-content-center">
              <span class="small" style="opacity: 0.8;">Total Tax Contributions</span>
              <span class="fs-5 fw-medium">Rs. {pnl.summary.cgt.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</span>
            </div>
          </div>
        </div>
        <div class="col-sm-6">
          <div class="card shadow-sm border-0 h-100 text-dark" style="background-color: #f8f9fa;">
            <div class="card-body d-flex flex-column justify-content-center">
              <span class="small" style="opacity: 0.8;">Total Trades Analyzed</span>
              <span class="fs-5 fw-medium">{pnl.details.length} Trades</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="card shadow-sm border-0 text-dark">
    <div class="card-header bg-white border-bottom pt-3 px-4">
      <ul class="nav nav-tabs border-bottom-0 gap-3">
        <li class="nav-item">
          <button
            class="nav-link border-0 {activeTab === 'summary' ? 'active fw-bold border-bottom border-primary border-3 text-dark' : 'bg-transparent'}"
            style="border-radius: 0; padding-bottom: 12px; color: {activeTab === 'summary' ? 'inherit' : '#6c757d'};"
            onclick={() => (activeTab = 'summary')}
          >
            Symbol-Wise Breakdown
          </button>
        </li>
        <li class="nav-item">
          <button
            class="nav-link border-0 {activeTab === 'detailed' ? 'active fw-bold border-bottom border-primary border-3 text-dark' : 'bg-transparent'}"
            style="border-radius: 0; padding-bottom: 12px; color: {activeTab === 'detailed' ? 'inherit' : '#6c757d'};"
            onclick={() => (activeTab = 'detailed')}
          >
            Detailed Ledger
          </button>
        </li>
      </ul>
    </div>

    <div class="card-body p-0">
      <div class="table-responsive">
        <table class="table table-hover align-middle mb-0" style="font-size: 0.9rem;">
          <thead style="background-color: #f8f9fa;">
            <tr class="text-uppercase" style="font-size: 0.75rem; letter-spacing: 0.5px; opacity: 0.8;">
              {#if activeTab === 'detailed'}
                <th class="ps-4">Date</th>
              {/if}
              <th class={activeTab === 'summary' ? 'ps-4' : ''}>Symbol</th>
              <th class="text-end">Qty</th>
              {#if activeTab === 'detailed'}
                <th class="text-end">Rate</th>
                <th class="text-end">WACC</th>
              {/if}
              <th class="text-end">Revenue</th>
              <th class="text-end">Fees</th>
              <th class="text-end">CGT</th>
              <th class="text-end">Gross Gain</th>
              <th class="text-end pe-4">Net Profit</th>
            </tr>
          </thead>
          <tbody>
            {#if activeTab === 'summary'}
              {#each pnl.grouped as item}
                <tr>
                  <td class="fw-bold ps-4">{item.symbol}</td>
                  <td class="text-end">{item.totalQty.toLocaleString("en-IN")}</td>
                  <td class="text-end">{item.salesValue.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</td>
                  <td class="text-end">({item.fees.toLocaleString("en-IN", { minimumFractionDigits: 2 })})</td>
                  <td class="text-end">({item.cgt.toLocaleString("en-IN", { minimumFractionDigits: 2 })})</td>
                  <td class="text-end {item.grossGain >= 0 ? 'text-success' : 'text-danger'}">
                    {item.grossGain.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </td>
                  <td class="text-end fw-bold pe-4 {item.netProfit >= 0 ? 'text-success' : 'text-danger'}">
                    {item.netProfit >= 0 ? "+" : ""}{item.netProfit.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </td>
                </tr>
              {:else}
                <tr><td colspan="7" class="text-center py-5" style="opacity: 0.7;">No realized profit or loss available.</td></tr>
              {/each}
            {:else}
              {#each pnl.details as item}
                <tr>
                  <td class="text-nowrap ps-4" style="opacity: 0.9;">{item.date}</td>
                  <td class="fw-bold">{item.symbol}</td>
                  <td class="text-end">{item.qty.toLocaleString("en-IN")}</td>
                  <td class="text-end">{item.rate.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</td>
                  <td class="text-end">{item.wacc.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</td>
                  <td class="text-end">{item.salesValue.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</td>
                  <td class="text-end">({item.fees.toLocaleString("en-IN", { minimumFractionDigits: 2 })})</td>
                  <td class="text-end">({item.cgt.toLocaleString("en-IN", { minimumFractionDigits: 2 })})</td>
                  <td class="text-end {item.grossGain >= 0 ? 'text-success' : 'text-danger'}">
                    {item.grossGain.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </td>
                  <td class="text-end fw-bold pe-4 {item.netProfit >= 0 ? 'text-success' : 'text-danger'}">
                    {item.netProfit >= 0 ? "+" : ""}{item.netProfit.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </td>
                </tr>
              {:else}
                <tr><td colspan="10" class="text-center py-5" style="opacity: 0.7;">No sell transactions found.</td></tr>
              {/each}
            {/if}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>
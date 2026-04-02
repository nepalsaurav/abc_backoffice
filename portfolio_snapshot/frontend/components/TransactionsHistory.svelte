<script>
  let props = $props();

  // FIX: Look for props.history, since that is what the parent is passing!
  let ledgerData = $derived(props.history || []);

  let searchQuery = $state("");
  let selectedType = $state("All");

  let transactionTypes = $derived(["All", ...new Set(ledgerData.map((item) => item.transaction_type))]);

  let filteredLedger = $derived(
    ledgerData.filter((row) => {
      const matchesSearch =
        searchQuery === "" ||
        row.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
        row.date.includes(searchQuery) ||
        (row.trn_no && row.trn_no.toLowerCase().includes(searchQuery.toLowerCase())) ||
        row.transaction_type.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesType = selectedType === "All" || row.transaction_type === selectedType;

      return matchesSearch && matchesType;
    }),
  );

  const formatNumber = (num, decimals = 2) => {
    if (num === undefined || num === null || num === 0) return "-";
    return Number(num).toLocaleString("en-US", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  };

  const getBadgeClass = (type) => {
    switch (type.toLowerCase()) {
      case "buy":
        return "bg-success";
      case "sell":
        return "bg-danger";
      case "bonus share":
        return "bg-info text-dark";
      case "bonus share (provisional)":
        return "bg-warning text-dark";
      case "cash dividend":
        return "bg-primary";
      default:
        return "bg-secondary";
    }
  };

  const formatFeesTooltip = (fees) => {
    if (!fees || Object.keys(fees).length === 0) return "No fees applied";
    return `Broker: Rs.${fees.broker?.toFixed(2) || 0}\nSEBO: Rs.${fees.sebo?.toFixed(2) || 0}\nNEPSE: Rs.${fees.nepse?.toFixed(2) || 0}\nDP: Rs.${fees.dp_charge?.toFixed(2) || 0}\nReg: Rs.${fees.regulatory?.toFixed(2) || 0}`;
  };

  const formatCGTTooltip = (row) => {
    if (!row.cgt_total) return "No tax applied";
    return `Long-Term (5%): Rs.${row.cgt_5_pct?.toFixed(2) || 0}\nShort-Term (7.5%): Rs.${row.cgt_7_5_pct?.toFixed(2) || 0}`;
  };
</script>

<div class="container-fluid py-4">
  <div class="card shadow-sm">
    <div class="card-header bg-white py-3 d-flex flex-wrap justify-content-between align-items-center gap-2">
      <h5 class="mb-0 fw-bold">Transaction Ledger</h5>
      <span class="badge bg-primary rounded-pill">{filteredLedger.length} Records</span>
    </div>

    <div class="card-body bg-light border-bottom py-3">
      <div class="row g-3">
        <div class="col-12 col-md-8">
          <div class="input-group">
            <span class="input-group-text bg-white text-muted">🔍</span>
            <input
              type="text"
              class="form-control"
              placeholder="Search by Symbol, Date, Trn No, or Type..."
              bind:value={searchQuery} />
          </div>
        </div>
        <div class="col-12 col-md-4">
          <select class="form-select" bind:value={selectedType}>
            {#each transactionTypes as type}
              <option value={type}>{type === "All" ? "All Transaction Types" : type}</option>
            {/each}
          </select>
        </div>
      </div>
    </div>

    <div class="card-body p-0">
      <div class="table-responsive" style="max-height: 70vh;">
        <table class="table table-hover table-bordered table-sm mb-0 align-middle text-nowrap">
          <thead class="table-light sticky-top shadow-sm" style="z-index: 1;">
            <tr>
              <th scope="col" class="px-3 py-2">Date</th>
              <th scope="col" class="px-3 py-2">Trn No</th>
              <th scope="col" class="px-3 py-2">Symbol</th>
              <th scope="col" class="px-3 py-2">Type</th>
              <th scope="col" class="text-end px-3 py-2">In Qty</th>
              <th scope="col" class="text-end px-3 py-2">Out Qty</th>
              <th scope="col" class="text-end px-3 py-2">Rate</th>
              <th scope="col" class="text-end px-3 py-2 text-muted">Gross Amt</th>
              <th scope="col" class="text-end px-3 py-2">Net Amt <i class="bi bi-info-circle small text-muted"></i></th>
              <th scope="col" class="text-end px-3 py-2">WACC</th>
              <th scope="col" class="text-end px-3 py-2">Gain/Loss</th>
              <th scope="col" class="text-end px-3 py-2">CGT <i class="bi bi-info-circle small text-muted"></i></th>
              <th scope="col" class="text-end px-3 py-2">Balance</th>
              <th scope="col" class="px-3 py-2">Remarks</th>
            </tr>
          </thead>
          <tbody>
            {#if filteredLedger.length === 0}
              <tr>
                <td colspan="14" class="text-center py-4 text-muted">
                  No transactions found matching your search criteria.
                </td>
              </tr>
            {:else}
              {#each filteredLedger as row}
                <tr>
                  <td class="px-3 text-muted font-monospace">{row.date}</td>
                  <td class="px-3 text-muted small">{row.trn_no || "-"}</td>
                  <td class="px-3 fw-bold">{row.symbol}</td>
                  <td class="px-3">
                    <span class="badge {getBadgeClass(row.transaction_type)}">
                      {row.transaction_type}
                    </span>
                  </td>
                  <td class="px-3 text-end">{row.in_qty || "-"}</td>
                  <td class="px-3 text-end">{row.out_qty || "-"}</td>
                  <td class="px-3 text-end">{formatNumber(row.rate)}</td>

                  <td class="px-3 text-end text-muted">{formatNumber(row.gross_amount)}</td>

                  <td class="px-3 text-end fw-semibold" title={formatFeesTooltip(row.fees)} style="cursor: help;">
                    {formatNumber(row.net_amount)}
                  </td>

                  <td class="px-3 text-end text-muted">{formatNumber(row.wacc, 4)}</td>

                  <td
                    class="px-3 text-end {row.capital_gain > 0
                      ? 'text-success fw-bold'
                      : row.capital_gain < 0
                        ? 'text-danger fw-bold'
                        : ''}">
                    {row.capital_gain ? formatNumber(row.capital_gain) : "-"}
                  </td>

                  <td class="px-3 text-end text-muted" title={formatCGTTooltip(row)} style="cursor: help;">
                    {row.cgt_total ? formatNumber(row.cgt_total) : "-"}
                  </td>

                  <td class="px-3 text-end fw-bold">{row.balance_qty}</td>

                  <td class="px-3 text-muted small">{row.remarks || "-"}</td>
                </tr>
              {/each}
            {/if}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>

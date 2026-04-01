<script>
  let props = $props();

  // Reactive states for our search and filter inputs
  let searchQuery = $state("");
  let selectedType = $state("All");

  // Dynamically extract unique transaction types for the dropdown filter
  let transactionTypes = $derived(["All", ...new Set((props.history || []).map((item) => item.transaction_type))]);

  // Derived reactive variable that automatically updates when search/filter changes
  let filteredHistory = $derived(
    (props.history || []).filter((row) => {
      // 1. Check if it matches the text search (Symbol, Date, or Type)
      const matchesSearch =
        searchQuery === "" ||
        row.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
        row.date.includes(searchQuery) ||
        row.transaction_type.toLowerCase().includes(searchQuery.toLowerCase());

      // 2. Check if it matches the dropdown filter
      const matchesType = selectedType === "All" || row.transaction_type === selectedType;

      // Include row only if it matches both conditions
      return matchesSearch && matchesType;
    }),
  );

  // Format numbers with commas and decimals
  const formatNumber = (num, decimals = 2) => {
    if (num === undefined || num === null) return "-";
    return Number(num).toLocaleString("en-US", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  };

  // Helper to style badge based on transaction type
  const getBadgeClass = (type) => {
    switch (type.toLowerCase()) {
      case "buy":
        return "bg-success";
      case "sell":
        return "bg-danger";
      case "bonus share":
        return "bg-info text-dark";
      case "cash dividend":
        return "bg-primary";
      default:
        return "bg-secondary";
    }
  };
</script>

<div class="container-fluid py-4">
  <div class="card shadow-sm">
    <div class="card-header bg-white py-3 d-flex flex-wrap justify-content-between align-items-center gap-2">
      <h5 class="mb-0 fw-bold">Transaction Ledger</h5>
      <span class="badge bg-primary rounded-pill">{filteredHistory.length} Records</span>
    </div>

    <div class="card-body bg-light border-bottom py-3">
      <div class="row g-3">
        <div class="col-12 col-md-8">
          <div class="input-group">
            <span class="input-group-text bg-white text-muted">🔍</span>
            <input
              type="text"
              class="form-control"
              placeholder="Search by Symbol, Date, or Type..."
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
        <table class="table table-hover table-bordered table-sm mb-0 align-middle">
          <thead class="table-light sticky-top shadow-sm" style="z-index: 1;">
            <tr>
              <th scope="col" class="text-nowrap px-3 py-2">Date</th>
              <th scope="col" class="text-nowrap px-3 py-2">Symbol</th>
              <th scope="col" class="text-nowrap px-3 py-2">Type</th>
              <th scope="col" class="text-end text-nowrap px-3 py-2">In Qty</th>
              <th scope="col" class="text-end text-nowrap px-3 py-2">Out Qty</th>
              <th scope="col" class="text-end text-nowrap px-3 py-2">Rate</th>
              <th scope="col" class="text-end text-nowrap px-3 py-2">Amount</th>
              <th scope="col" class="text-end text-nowrap px-3 py-2">WACC</th>
              <th scope="col" class="text-end text-nowrap px-3 py-2">Gain/Loss</th>
              <th scope="col" class="text-end text-nowrap px-3 py-2">CGT</th>
              <th scope="col" class="text-end text-nowrap px-3 py-2">Balance</th>
            </tr>
          </thead>
          <tbody>
            {#if filteredHistory.length === 0}
              <tr>
                <td colspan="11" class="text-center py-4 text-muted">
                  No transactions found matching your search criteria.
                </td>
              </tr>
            {:else}
              {#each filteredHistory as row}
                <tr>
                  <td class="px-3 text-nowrap text-muted font-monospace">{row.date}</td>
                  <td class="px-3 fw-bold">{row.symbol}</td>
                  <td class="px-3">
                    <span class="badge {getBadgeClass(row.transaction_type)}">
                      {row.transaction_type}
                    </span>
                  </td>
                  <td class="px-3 text-end">{row.in_qty || "-"}</td>
                  <td class="px-3 text-end">{row.out_qty || "-"}</td>
                  <td class="px-3 text-end">{formatNumber(row.rate)}</td>
                  <td class="px-3 text-end fw-semibold">{formatNumber(row.amount)}</td>
                  <td class="px-3 text-end text-muted">{formatNumber(row.wacc, 4)}</td>

                  <td
                    class="px-3 text-end {row.capital_gain > 0
                      ? 'text-success'
                      : row.capital_gain < 0
                        ? 'text-danger'
                        : ''}">
                    {row.capital_gain ? formatNumber(row.capital_gain) : "-"}
                  </td>

                  <td class="px-3 text-end text-muted">{row.cgt ? formatNumber(row.cgt) : "-"}</td>
                  <td class="px-3 text-end fw-bold">{row.balance_qty}</td>
                </tr>
              {/each}
            {/if}
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>

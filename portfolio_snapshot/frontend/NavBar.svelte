<script>
  import { link } from "svelte-spa-router";
</script>

<ul class="nav flex-column w-100" style="font-size: 0.825rem;">
  <li class="nav-item">
    <a href="/" class="nav-link text-dark rounded-2 mb-1 py-2 px-3 fw-medium hover-bg-light"
      ><i class="bi bi-house me-2"></i> <span class="nav-text">Home / Desk</span></a
    >
  </li>
  <li class="nav-item mt-3 mb-2">
    <span class="text-uppercase text-muted fw-bold px-3" style="font-size: 0.7rem; letter-spacing: 0.5px;">Portfolio Snapshot</span>
  </li>
  <li class="nav-item">
    <a class="nav-link text-dark rounded-2 mb-1 py-2 px-3 fw-medium hover-bg-light" href="/" use:link
      ><i class="bi bi-speedometer2 me-2"></i> <span class="nav-text">Dashboard</span></a
    >
  </li>
  <li class="nav-item">
    <a
      class="nav-link text-dark rounded-2 mb-1 py-2 px-3 fw-medium hover-bg-light"
      href="/import_transactions"
      use:link
      ><i class="bi bi-file-earmark-arrow-up me-2"></i> <span class="nav-text">Import Transactions</span></a
    >
  </li>
  <li class="nav-item">
    <a
      class="nav-link text-dark rounded-2 py-2 px-3 fw-medium hover-bg-light"
      href="/corporate_action"
      use:link><i class="bi bi-arrow-repeat me-2"></i> <span class="nav-text">Corporate Actions</span></a
    >
  </li>
</ul>

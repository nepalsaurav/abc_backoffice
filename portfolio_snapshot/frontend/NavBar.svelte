<script>
  import { link } from "svelte-spa-router";
</script>

<ul class="nav nav-pills" style="font-size: 0.85rem;">
  <li class="nav-item">
    <a class="nav-link py-1 px-3 fw-medium rounded-2" href="/" use:link
      ><i class="bi bi-speedometer2 me-1"></i> Dashboard</a
    >
  </li>
  <li class="nav-item ms-1">
    <a
      class="nav-link py-1 px-3 fw-medium rounded-2"
      href="/import_transactions"
      use:link
      ><i class="bi bi-file-earmark-arrow-up me-1"></i> Import Transactions</a
    >
  </li>
  <li class="nav-item ms-1">
    <a
      class="nav-link py-1 px-3 fw-medium rounded-2"
      href="/corporate_action"
      use:link><i class="bi bi-arrow-repeat me-1"></i> Corporate Actions</a
    >
  </li>
</ul>

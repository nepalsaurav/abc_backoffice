<script>
    import { createEventDispatcher } from 'svelte';
    const dispatch = createEventDispatcher();

    let searchQuery = "";
    let isDropdownOpen = false;
    let selectedCustomer = null;
    
    export let customers = [];

    $: filteredCustomers = customers.filter(c => 
        c.toLowerCase().includes(searchQuery.toLowerCase())
    );

    function selectCustomer(customer) {
        searchQuery = customer;
        selectedCustomer = customer;
        isDropdownOpen = false;
        
        // Dispatch event for App.svelte to catch and show loading
        dispatch('select', { customer });
    }

    function handleInput() {
        isDropdownOpen = true;
        selectedCustomer = null; 
    }

    // Close when clicking outside (simple blur works for now)
    function handleBlur() {
        // slight delay to allow click event on option to fire
        setTimeout(() => {
            isDropdownOpen = false;
        }, 200);
    }
</script>

<div class="customer-select position-relative">
    <div class="input-group shadow-sm search-container rounded">
        <span class="input-group-text bg-white border-0 text-muted px-3">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-search" viewBox="0 0 16 16">
              <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/>
            </svg>
        </span>
        <input 
            type="text" 
            class="form-control border-0 ps-2 fw-medium shadow-none py-2" 
            bind:value={searchQuery} 
            on:input={handleInput}
            on:focus={() => isDropdownOpen = true}
            on:blur={handleBlur}
            placeholder="Search and select customer..." 
        />
        {#if searchQuery}
            <button class="btn border-0 text-muted bg-white px-3" type="button" aria-label="Clear search" on:click={() => {searchQuery = ''; isDropdownOpen = true;}}>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-x" viewBox="0 0 16 16">
                  <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
                </svg>
            </button>
        {/if}
    </div>

    {#if isDropdownOpen && filteredCustomers.length > 0}
        <ul class="dropdown-menu show w-100 position-absolute mt-2 shadow-lg border-0 rounded-3 p-1" style="max-height: 280px; overflow-y: auto; overflow-x: hidden; z-index: 1050;">
            {#each filteredCustomers as customer}
                <li>
                    <button class="dropdown-item py-2 px-3 rounded-2 text-truncate {selectedCustomer === customer ? 'active' : ''}" on:click={() => selectCustomer(customer)} title={customer}>
                        {customer}
                    </button>
                </li>
            {/each}
        </ul>
    {:else if isDropdownOpen && filteredCustomers.length === 0}
        <ul class="dropdown-menu show w-100 position-absolute mt-2 shadow-lg border-0 p-3 text-center text-muted h-auto rounded-3">
            <small>No customers found</small>
        </ul>
    {/if}
</div>

<style>
    .customer-select {
        min-width: 420px;
    }
    .search-container {
        border: 1px solid #dee2e6;
        transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
    }
    .search-container:focus-within {
        border-color: #86b7fe;
        box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25) !important;
    }
    .dropdown-item {
        transition: all 0.1s ease;
        font-size: 0.95rem;
    }
    .dropdown-item:hover {
        background-color: #f8f9fa;
    }
    .dropdown-item:active {
        background-color: #e9ecef;
        color: #212529;
    }
    .dropdown-item.active {
        background-color: #eff6ff;
        color: #0d6efd;
        font-weight: 600;
    }
    
    /* Custom scrollbar for a more premium look */
    .dropdown-menu::-webkit-scrollbar {
        width: 6px;
    }
    .dropdown-menu::-webkit-scrollbar-track {
        background: transparent;
    }
    .dropdown-menu::-webkit-scrollbar-thumb {
        background: #ced4da;
        border-radius: 10px;
    }
    .dropdown-menu::-webkit-scrollbar-thumb:hover {
        background: #adb5bd;
    }
</style>

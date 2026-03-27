<script>
    import { createEventDispatcher } from 'svelte';
    const dispatch = createEventDispatcher();

    let searchQuery = "";
    let isDropdownOpen = false;
    let selectedCustomer = null;
    
    let customers = [
        "Acme Corp",
        "Global Industries",
        "Stark Enterprises",
        "Wayne Enterprises",
        "Cyberdyne Systems",
        "Umbrella Corporation",
        "Massive Dynamic"
    ];

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
    <div class="input-group shadow-sm">
        <span class="input-group-text bg-white border-end-0 text-muted">
            <!-- Icon placeholder if Bootstrap Icons is not present, otherwise it will just render safely -->
            <i class="bi bi-person-fill"></i>
        </span>
        <input 
            type="text" 
            class="form-control border-start-0 ps-0 fw-medium" 
            bind:value={searchQuery} 
            on:input={handleInput}
            on:focus={() => isDropdownOpen = true}
            on:blur={handleBlur}
            placeholder="Search and select customer..." 
        />
        {#if searchQuery}
            <button class="btn btn-outline-secondary border-start-0 border text-muted bg-white" type="button" aria-label="Clear search" on:click={() => {searchQuery = ''; isDropdownOpen = true;}}>
                <i class="bi bi-x"></i>
            </button>
        {/if}
    </div>

    {#if isDropdownOpen && filteredCustomers.length > 0}
        <ul class="dropdown-menu show w-100 position-absolute mt-1 shadow border-0" style="max-height: 250px; overflow-y: auto; z-index: 1050;">
            {#each filteredCustomers as customer}
                <li>
                    <button class="dropdown-item py-2 {selectedCustomer === customer ? 'active' : ''}" on:click={() => selectCustomer(customer)}>
                        {customer}
                    </button>
                </li>
            {/each}
        </ul>
    {:else if isDropdownOpen && filteredCustomers.length === 0}
        <ul class="dropdown-menu show w-100 position-absolute mt-1 shadow border-0 p-3 text-center text-muted h-auto">
            <small>No customers found</small>
        </ul>
    {/if}
</div>

<style>
    .customer-select {
        min-width: 320px;
    }
    .dropdown-item:active {
        background-color: #f8f9fa;
        color: #212529;
    }
    .dropdown-item.active {
        background-color: #e9ecef;
        color: #0d6efd;
        font-weight: 600;
    }
</style>

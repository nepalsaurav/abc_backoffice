<script>
    import { onMount, onDestroy } from "svelte";
    import Chart from "chart.js/auto";

    let chartCanvas;
    let chartInstance;

    onMount(() => {
        if (chartCanvas) {
            chartInstance = new Chart(chartCanvas, {
                type: 'pie',
                data: {
                    labels: ['Technology', 'Financials', 'Healthcare', 'Energy', 'Consumer Discretionary'],
                    datasets: [{
                        label: 'Sector Allocation',
                        data: [35, 20, 15, 10, 20],
                        backgroundColor: [
                            '#0d6efd', // Primary
                            '#198754', // Success
                            '#dc3545', // Danger
                            '#ffc107', // Warning
                            '#0dcaf0'  // Info
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                        }
                    }
                }
            });
        }
    });

    onDestroy(() => {
        if (chartInstance) {
            chartInstance.destroy();
        }
    });
</script>

<div class="mt-4">
    <h5 class="fw-bold mb-3">Sector Distribution</h5>
    <div class="card border-0 shadow-sm">
        <div class="card-body">
            <div style="height: 300px; position: relative; width: 100%;">
                <canvas bind:this={chartCanvas}></canvas>
            </div>
        </div>
    </div>
</div>

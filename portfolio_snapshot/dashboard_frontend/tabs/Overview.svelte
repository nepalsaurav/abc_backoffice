<script>
    import { onMount, onDestroy } from "svelte";
    import Chart from "chart.js/auto";

    let chartCanvas;
    let chartInstance;

    onMount(() => {
        if (chartCanvas) {
            const ctx = chartCanvas.getContext('2d');
            
            // Create a gradient for the line chart fill
            let gradient = ctx.createLinearGradient(0, 0, 0, 350);
            gradient.addColorStop(0, 'rgba(13, 110, 253, 0.2)');
            gradient.addColorStop(1, 'rgba(13, 110, 253, 0.0)');

            chartInstance = new Chart(chartCanvas, {
                type: 'line',
                data: {
                    labels: ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'],
                    datasets: [{
                        label: 'Portfolio Value',
                        data: [1200000, 1250000, 1220000, 1310000, 1380000, 1425300],
                        borderColor: '#0d6efd',
                        backgroundColor: gradient,
                        borderWidth: 3,
                        pointBackgroundColor: '#0d6efd',
                        pointBorderColor: '#0d6efd',
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            backgroundColor: 'rgba(255, 255, 255, 0.9)',
                            titleColor: '#212529',
                            bodyColor: '#212529',
                            borderColor: '#dee2e6',
                            borderWidth: 1,
                            padding: 10,
                            displayColors: false,
                            callbacks: {
                                label: function(context) {
                                    let value = context.parsed.y;
                                    return 'Rs. ' + new Intl.NumberFormat('en-IN').format(value);
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            min: 1200000,
                            max: 1450000,
                            ticks: {
                                stepSize: 50000,
                                color: '#6c757d',
                                font: {
                                    size: 11
                                },
                                callback: function(value) {
                                    return 'Rs.' + Math.floor(value / 1000) + 'k';
                                }
                            },
                            grid: {
                                color: '#f8f9fa',
                                drawBorder: false
                            },
                            border: {
                                display: false
                            }
                        },
                        x: {
                            ticks: {
                                color: '#6c757d',
                                font: {
                                    size: 11
                                }
                            },
                            grid: {
                                display: false,
                                drawBorder: false
                            },
                            border: {
                                display: true,
                                color: '#f8f9fa'
                            }
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

<div class="mt-2">
    <!-- Top Cards Row -->
    <div class="row g-4 mb-4">
        <!-- Value Card -->
        <div class="col-md-4">
            <div class="card h-100 p-4 border-0 shadow-sm sleek-card">
                <div class="card-body p-0">
                    <h6 class="text-uppercase fw-bold text-muted mb-3" style="font-size: 0.75rem; letter-spacing: 0.5px;">Total Portfolio Value</h6>
                    <h2 class="fw-bold mb-3 text-dark">Rs. 1,425,300</h2>
                    <p class="text-dark small mb-0 fw-medium">Includes Provisional Units</p>
                </div>
            </div>
        </div>
        
        <!-- P/L Card -->
        <div class="col-md-4">
            <div class="card h-100 p-4 border-0 shadow-sm sleek-card">
                <div class="card-body p-0">
                    <h6 class="text-uppercase fw-bold text-muted text-center mb-3" style="font-size: 0.75rem; letter-spacing: 0.5px;">Overall Profit / Loss</h6>
                    <h2 class="fw-bold mb-3 text-success text-center">Rs. 245,000</h2>
                    <p class="text-muted small mb-0 fw-medium text-center">Realized + Unrealized Gains</p>
                </div>
            </div>
        </div>
        
        <!-- Assets Card -->
        <div class="col-md-4">
            <div class="card h-100 p-4 border-0 shadow-sm sleek-card">
                <div class="card-body p-0">
                    <h6 class="text-uppercase fw-bold text-muted text-center mb-3" style="font-size: 0.75rem; letter-spacing: 0.5px;">Provisional Assets</h6>
                    <h2 class="fw-bold mb-3 text-warning text-center">Rs. 45,200</h2>
                    <p class="text-muted small mb-0 fw-medium text-center">Scraped from Sharesansar</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Chart Row -->
    <div class="card border-0 shadow-sm sleek-card mb-4">
        <div class="card-body p-4 p-md-5">
            <div class="d-flex justify-content-between align-items-center mb-5">
                <h4 class="fw-bold mb-0 text-dark">Portfolio Growth</h4>
                <button class="btn btn-outline-secondary btn-sm px-3 py-1 rounded-2 bg-white text-dark fw-medium border shadow-sm">
                    Last 6 Months
                </button>
            </div>
            <div style="height: 350px; position: relative; width: 100%;">
                <canvas bind:this={chartCanvas}></canvas>
            </div>
        </div>
    </div>
</div>

<style>
    /* Styling to match the design aesthetics closely */
    .sleek-card {
        border-radius: 1.25rem;
    }
    
    .sleek-card.shadow-sm {
        box-shadow: 0 0.25rem 0.5rem -0.25rem rgba(0, 0, 0, 0.05), 0 0.5rem 1rem -0.5rem rgba(0, 0, 0, 0.05) !important;
        border: 1px solid rgba(0,0,0,0.02) !important;
    }
</style>

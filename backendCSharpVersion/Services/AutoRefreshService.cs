using backendCSharpVersion.Scraper;

namespace backendCSharpVersion.Services;

public class AutoRefreshService : BackgroundService
{
    private static readonly TimeSpan RefreshInterval = TimeSpan.FromHours(1);

    private readonly IServiceProvider _serviceProvider;
    private readonly ILogger<AutoRefreshService> _logger;

    public AutoRefreshService(IServiceProvider serviceProvider, ILogger<AutoRefreshService> logger)
    {
        _serviceProvider = serviceProvider;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _logger.LogInformation("[auto-refresh] Background refresh service started.");

        while (!stoppingToken.IsCancellationRequested)
        {
            // Wait one full interval before first refresh (mirrors the Python behaviour
            // where the thread sleeps *before* the first scrape).
            await Task.Delay(RefreshInterval, stoppingToken);

            if (stoppingToken.IsCancellationRequested) break;

            _logger.LogInformation("[auto-refresh] Starting scheduled product refresh...");
            try
            {
                // Resolve a fresh scoped scraper for each run
                using var scope = _serviceProvider.CreateScope();
                var scraper = scope.ServiceProvider.GetRequiredService<ProductScraper>();
                var products = await scraper.ScrapeAllProducts();
                _logger.LogInformation("[auto-refresh] Done — {Count} products updated.", products.Count);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "[auto-refresh] Error during refresh.");
            }
        }
    }
}

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using backendCSharpVersion.Data;
using backendCSharpVersion.Models;
using backendCSharpVersion.Scraper;

namespace backendCSharpVersion.Controllers;

[ApiController]
[Route("api")]
public class ProductsController : ControllerBase
{
    private readonly Database _db;
    private readonly ProductScraper _scraper;

    public ProductsController(Database db, ProductScraper scraper)
    {
        _db = db;
        _scraper = scraper;
    }

    // GET /api/products
    [HttpGet("products")]
    public IActionResult GetProducts(
        [FromQuery] string? sort_by,
        [FromQuery] string? sort_order,
        [FromQuery] string? category,
        [FromQuery] string? strain_type,
        [FromQuery] string? purchase_type,
        [FromQuery] string? terpenes,
        [FromQuery] double? min_thc,
        [FromQuery] double? max_thc)
    {
        var filters = new ProductFilters
        {
            PurchaseType = purchase_type,
            Category     = category,
            StrainType   = strain_type,
            MinThc       = min_thc,
            MaxThc       = max_thc,
        };

        // Strip null-equivalent filters
        if (string.IsNullOrEmpty(filters.PurchaseType)) filters.PurchaseType = null;
        if (string.IsNullOrEmpty(filters.Category))     filters.Category = null;
        if (string.IsNullOrEmpty(filters.StrainType))   filters.StrainType = null;

        var products = _db.LoadProducts(filters);

        // In-memory terpene filter
        if (!string.IsNullOrEmpty(terpenes))
        {
            var required = terpenes.Split(',')
                .Select(t => t.Trim().ToLower())
                .Where(t => t.Length > 0)
                .ToList();

            products = products
                .Where(p => required.All(t => p.Terpenes.TryGetValue(t, out var v) && v > 0))
                .ToList();
        }

        // Sorting
        var sortBy    = sort_by ?? "total_terpenes";
        var sortOrder = sort_order ?? "desc";
        var descending = sortOrder.ToLower() == "desc";

        products = sortBy switch
        {
            "total_terpenes" => descending
                ? products.OrderByDescending(p => p.TotalTerpenes).ToList()
                : products.OrderBy(p => p.TotalTerpenes).ToList(),
            "thc" => descending
                ? products.OrderByDescending(p => p.Thc).ToList()
                : products.OrderBy(p => p.Thc).ToList(),
            "cbd" => descending
                ? products.OrderByDescending(p => p.Cbd).ToList()
                : products.OrderBy(p => p.Cbd).ToList(),
            "price" => descending
                ? products.OrderByDescending(p => p.SalePrice > 0 ? p.SalePrice : p.Price).ToList()
                : products.OrderBy(p => p.SalePrice > 0 ? p.SalePrice : p.Price).ToList(),
            "name" => descending
                ? products.OrderByDescending(p => p.Name.ToLower()).ToList()
                : products.OrderBy(p => p.Name.ToLower()).ToList(),
            _ => descending
                ? products.OrderByDescending(p => p.Terpenes.TryGetValue(sortBy, out var v) ? v : 0).ToList()
                : products.OrderBy(p => p.Terpenes.TryGetValue(sortBy, out var v) ? v : 0).ToList(),
        };

        return Ok(new
        {
            products,
            total = products.Count
        });
    }

    // GET /api/refresh
    [HttpGet("refresh")]
    public async Task<IActionResult> RefreshGet()
    {
        return await RunRefresh();
    }

    // POST /api/refresh
    [HttpPost("refresh")]
    public async Task<IActionResult> RefreshPost()
    {
        return await RunRefresh();
    }

    private async Task<IActionResult> RunRefresh()
    {
        try
        {
            var products = await _scraper.ScrapeAllProducts();
            return Ok(new
            {
                success  = true,
                message  = $"Successfully scraped {products.Count} products",
                products,
                total    = products.Count
            });
        }
        catch (Exception ex)
        {
            return StatusCode(500, new
            {
                success = false,
                error   = ex.Message
            });
        }
    }

    // GET /api/terpenes
    [HttpGet("terpenes")]
    public IActionResult GetTerpenes()
    {
        var products = _db.LoadProducts();
        var terpeneSet = new SortedSet<string>(StringComparer.Ordinal);
        foreach (var p in products)
            foreach (var key in p.Terpenes.Keys)
                terpeneSet.Add(key);

        return Ok(new { terpenes = terpeneSet.ToList() });
    }

    // GET /api/categories
    [HttpGet("categories")]
    public IActionResult GetCategories()
    {
        var products = _db.LoadProducts();
        var categories = products
            .Select(p => p.Category)
            .Where(c => !string.IsNullOrEmpty(c))
            .Distinct()
            .OrderBy(c => c)
            .ToList();

        return Ok(new { categories });
    }

    // GET /api/strain-types
    [HttpGet("strain-types")]
    public IActionResult GetStrainTypes()
    {
        var products = _db.LoadProducts();
        var strainTypes = products
            .Select(p => p.StrainType)
            .Where(s => !string.IsNullOrEmpty(s))
            .Distinct()
            .OrderBy(s => s)
            .ToList();

        return Ok(new { strain_types = strainTypes });
    }

    // GET /api/stats
    [HttpGet("stats")]
    public IActionResult GetStats()
    {
        var products = _db.LoadProducts();

        if (products.Count == 0)
        {
            return Ok(new
            {
                total_products          = 0,
                products_with_terpenes  = 0,
                categories              = new List<string>(),
                strain_types            = new List<string>(),
                terpene_averages        = new Dictionary<string, double>()
            });
        }

        var productsWithTerpenes = products
            .Where(p => p.Terpenes.Count > 0 && p.Terpenes.Values.Sum() > 0)
            .ToList();

        var terpTotals = new Dictionary<string, double>();
        var terpCounts = new Dictionary<string, int>();

        foreach (var p in productsWithTerpenes)
        {
            foreach (var (terpene, value) in p.Terpenes)
            {
                if (value <= 0) continue;
                terpTotals[terpene]  = terpTotals.GetValueOrDefault(terpene) + value;
                terpCounts[terpene]  = terpCounts.GetValueOrDefault(terpene) + 1;
            }
        }

        var terpeneAverages = terpTotals
            .ToDictionary(
                kv => kv.Key,
                kv => Math.Round(kv.Value / terpCounts[kv.Key], 2));

        var categories = products
            .Select(p => p.Category)
            .Where(c => !string.IsNullOrEmpty(c))
            .Distinct()
            .OrderBy(c => c)
            .ToList();

        var strainTypes = products
            .Select(p => p.StrainType)
            .Where(s => !string.IsNullOrEmpty(s))
            .Distinct()
            .OrderBy(s => s)
            .ToList();

        return Ok(new
        {
            total_products          = products.Count,
            products_with_terpenes  = productsWithTerpenes.Count,
            categories,
            strain_types            = strainTypes,
            terpene_averages        = terpeneAverages
        });
    }

    // GET /api/health
    [HttpGet("health")]
    public IActionResult Health()
    {
        return Ok(new { status = "healthy" });
    }
}

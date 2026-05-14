using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using backendCSharpVersion.Data;
using backendCSharpVersion.Models;

namespace backendCSharpVersion.Scraper;

public class ProductScraper
{
    private const string BaseUrl = "https://shop.revcanna.com";
    private const string LabApiUrl = BaseUrl + "/_api/Products/GetExtendedLabdata";
    private const string ProductListApiUrl = BaseUrl + "/_api/Products/GetProductList";
    private const string StoreId = "235";
    private const string StoreSlug = "abingdon";
    private const int PageSize = 100;

    private static string Slugify(string text)
    {
        var lower = text.ToLower();
        var dashed = Regex.Replace(lower, @"[^a-z0-9]+", "-");
        return dashed.Trim('-');
    }

    private readonly HttpClient _httpClient;
    private readonly Database _db;

    public ProductScraper(Database db)
    {
        _db = db;
        _httpClient = new HttpClient();
        _httpClient.DefaultRequestHeaders.Add("storeid", StoreId);
        _httpClient.DefaultRequestHeaders.Add("ssr", "false");
        // content-type is set per-request
    }

    private async Task<JsonNode?> ApiPostAsync(string url, object payload, int retries = 3, int timeoutSeconds = 15)
    {
        for (int attempt = 0; attempt < retries; attempt++)
        {
            try
            {
                var json = JsonSerializer.Serialize(payload);
                using var content = new StringContent(json, Encoding.UTF8, "application/json");
                using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(timeoutSeconds));
                var response = await _httpClient.PostAsync(url, content, cts.Token);
                response.EnsureSuccessStatusCode();
                var body = await response.Content.ReadAsStringAsync();
                return JsonNode.Parse(body);
            }
            catch (Exception ex)
            {
                if (attempt < retries - 1)
                {
                    await Task.Delay(TimeSpan.FromSeconds(Math.Pow(2, attempt)));
                }
                else
                {
                    Console.WriteLine($"Failed POST {url}: {ex.Message}");
                    return null;
                }
            }
        }
        return null;
    }

    public async Task<JsonNode?> FetchLabData(int variantId)
    {
        return await ApiPostAsync(LabApiUrl, new { variantId });
    }

    private async Task<JsonNode?> FetchProductListPage(int pageNum, string saleType)
    {
        return await ApiPostAsync(ProductListApiUrl, new
        {
            filters = new { },
            page = pageNum,
            pageSize = PageSize,
            sortingMethodId = 7,
            searchTerm = "",
            saleType,
            platformOs = "web",
            sourcePage = 1,
        });
    }

    private static Product ParseProductListItem(JsonNode item, JsonNode variant)
    {
        var strain = item["strain"]?["prevalence"];
        var strainType = strain?["name"]?.GetValue<string>() ?? "";

        var price = 0.0;
        var priceNode = variant["price"];
        if (priceNode != null)
            double.TryParse(priceNode.ToString(), out price);

        var salePrice = 0.0;
        var promoNode = variant["promoPrice"];
        if (promoNode != null && promoNode.GetValueKind() != JsonValueKind.Null)
            double.TryParse(promoNode.ToString(), out salePrice);
        if (salePrice >= price)
            salePrice = 0.0;

        var lab = variant["labTests"];
        var thcVals = lab?["thc"]?["value"]?.AsArray();
        var thc = thcVals != null && thcVals.Count > 0
            ? double.Parse(thcVals[0]!.ToString())
            : 0.0;

        var cbdVals = lab?["cbd"]?["value"]?.AsArray();
        var cbd = cbdVals != null && cbdVals.Count > 0
            ? double.Parse(cbdVals[0]!.ToString())
            : 0.0;

        var images = item["images"]?.AsArray() ?? variant["images"]?.AsArray();
        var image = images != null && images.Count > 0
            ? images[0]?.GetValue<string>() ?? ""
            : "";

        var brandObj = item["brand"];
        var brand = brandObj is JsonObject bo ? bo["name"]?.GetValue<string>() ?? "" : "";

        var catObj = item["category"];
        var category = catObj is JsonObject co ? co["name"]?.GetValue<string>() ?? "" : "";
        var catId = catObj is JsonObject coid ? coid["id"]?.ToString() ?? "" : "";

        var variantIdNode = variant["id"];
        var variantId = variantIdNode != null ? variantIdNode.GetValue<int>() : 0;

        var productName = item["name"]?.GetValue<string>() ?? "";
        var variantName = variant["name"]?.GetValue<string>() ?? "";

        var catSlug = !string.IsNullOrEmpty(catId) ? $"{Slugify(category)}-{catId}" : Slugify(category);
        var prodSlug = !string.IsNullOrEmpty(variantName)
            ? $"{Slugify(productName)}-{Slugify(variantName)}-{variantId}"
            : $"{Slugify(productName)}-{variantId}";
        var url = $"{BaseUrl}/{StoreSlug}/medical/menu/{catSlug}/{prodSlug}?stockType=Default";

        return new Product
        {
            Name         = productName,
            Brand        = brand,
            Category     = category,
            StrainType   = strainType,
            Price        = price,
            SalePrice    = salePrice,
            Weight       = variantName,
            Thc          = thc,
            Cbd          = cbd,
            Image        = image,
            Url          = url,
            VariantId    = variantId,
            Terpenes     = new Dictionary<string, double>(),
            TotalTerpenes = 0.0,
            PurchaseType  = "",
        };
    }

    public static double EdibleMgPerUnit(string weight)
    {
        // "10pk 100mg" — pack count first
        var packFirst = Regex.Match(weight, @"(\d+)pk\s+(\d+)mg");
        if (packFirst.Success)
            return double.Parse(packFirst.Groups[2].Value) / double.Parse(packFirst.Groups[1].Value);

        // "20mg" or "20mg 10pk"
        var mgFirst = Regex.Match(weight, @"(\d+)mg");
        if (mgFirst.Success)
            return double.Parse(mgFirst.Groups[1].Value);

        return 0;
    }

    public static double ConcentrateGrams(string weight)
    {
        var m = Regex.Match(weight, @"([\d.]+)g");
        return m.Success ? double.Parse(m.Groups[1].Value) : 0;
    }

    public static string ClassifyPurchaseType(Product product)
    {
        if (product.Category == "Edibles" && EdibleMgPerUnit(product.Weight) > 10)
            return "Medical";
        if (product.Category == "Concentrates" && ConcentrateGrams(product.Weight) > 1)
            return "Medical";
        return "Recreational";
    }

    public async Task<List<Product>> FetchAllProductsApi()
    {
        var products = new Dictionary<int, Product>();
        int page = 1;

        while (true)
        {
            Console.WriteLine($"Fetching product list page {page}...");
            var data = await FetchProductListPage(page, "Medical");
            if (data == null) break;

            var items = data["list"]?.AsArray() ?? new JsonArray();
            var total = data["total"]?.GetValue<int>() ?? 0;

            foreach (var itemNode in items)
            {
                if (itemNode == null) continue;
                var variants = itemNode["variants"]?.AsArray() ?? new JsonArray();
                foreach (var variantNode in variants)
                {
                    if (variantNode == null) continue;
                    var product = ParseProductListItem(itemNode, variantNode);
                    if (!string.IsNullOrEmpty(product.Name) && product.VariantId != 0)
                    {
                        product.PurchaseType = ClassifyPurchaseType(product);
                        products[product.VariantId] = product;
                    }
                }
            }

            Console.WriteLine($"  Got {items.Count} items (running total: {products.Count} variants)");

            if (page * PageSize >= total || items.Count == 0)
                break;

            page++;
        }

        return products.Values.ToList();
    }

    private async Task<Product> EnrichProduct(Product product)
    {
        var variantId = product.VariantId;
        if (variantId == 0) return product;

        var lab = await FetchLabData(variantId);
        if (lab?["terpenes"] is JsonNode terpNode)
        {
            var terpenes = new Dictionary<string, double>();
            var total = 0.0;

            var values = terpNode["values"]?.AsArray() ?? new JsonArray();
            foreach (var entry in values)
            {
                if (entry == null) continue;
                var name = entry["name"]?.GetValue<string>()?.ToLower() ?? "";
                var minNode = entry["min"];
                var value = minNode != null ? minNode.GetValue<double>() : 0.0;

                if (name == "total terpenes")
                    total = value;
                else
                    terpenes[name] = value;
            }

            product.Terpenes = terpenes;
            product.TotalTerpenes = total;
        }

        return product;
    }

    public async Task EnrichWithLabData(List<Product> products)
    {
        Console.WriteLine($"\nFetching terpene lab data for {products.Count} products...");

        int completed = 0;
        const int maxConcurrent = 10;

        var semaphore = new SemaphoreSlim(maxConcurrent, maxConcurrent);

        var tasks = products.Select(async product =>
        {
            await semaphore.WaitAsync();
            try
            {
                await EnrichProduct(product);
            }
            finally
            {
                semaphore.Release();
                var done = Interlocked.Increment(ref completed);
                if (done % 50 == 0 || done == products.Count)
                    Console.WriteLine($"  {done}/{products.Count} variants enriched");
            }
        });

        await Task.WhenAll(tasks);
    }

    public async Task<List<Product>> ScrapeAllProducts()
    {
        _db.InitDb();
        Console.WriteLine("Fetching all products from SweedPOS API...");
        var allProducts = await FetchAllProductsApi();
        Console.WriteLine($"Fetched {allProducts.Count} product variants");

        await EnrichWithLabData(allProducts);

        _db.SaveProducts(allProducts);
        _db.DeleteStaleProducts(allProducts.Select(p => p.VariantId));
        return allProducts;
    }
}

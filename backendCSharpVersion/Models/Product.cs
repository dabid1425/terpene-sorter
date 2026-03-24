using System.Text.Json.Serialization;

namespace backendCSharpVersion.Models;

public class Product
{
    [JsonPropertyName("variant_id")]
    public int VariantId { get; set; }

    [JsonPropertyName("name")]
    public string Name { get; set; } = "";

    [JsonPropertyName("brand")]
    public string Brand { get; set; } = "";

    [JsonPropertyName("category")]
    public string Category { get; set; } = "";

    [JsonPropertyName("strain_type")]
    public string StrainType { get; set; } = "";

    [JsonPropertyName("price")]
    public double Price { get; set; }

    [JsonPropertyName("sale_price")]
    public double SalePrice { get; set; }

    [JsonPropertyName("weight")]
    public string Weight { get; set; } = "";

    [JsonPropertyName("thc")]
    public double Thc { get; set; }

    [JsonPropertyName("cbd")]
    public double Cbd { get; set; }

    [JsonPropertyName("image")]
    public string Image { get; set; } = "";

    [JsonPropertyName("url")]
    public string Url { get; set; } = "";

    [JsonPropertyName("terpenes")]
    public Dictionary<string, double> Terpenes { get; set; } = new();

    [JsonPropertyName("total_terpenes")]
    public double TotalTerpenes { get; set; }

    [JsonPropertyName("purchase_type")]
    public string PurchaseType { get; set; } = "";
}

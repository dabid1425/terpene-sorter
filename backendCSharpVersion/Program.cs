using System;
using backendCSharpVersion.Data;
using backendCSharpVersion.Scraper;
using backendCSharpVersion.Services;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.DependencyInjection;

var builder = WebApplication.CreateBuilder(args);

// ------------------------------------------------------------------
// Configuration
// ------------------------------------------------------------------
var rawDbUrl = Environment.GetEnvironmentVariable("DATABASE_URL")
               ?? "Host=localhost;Database=terpene_sorter;";

// Normalise legacy Heroku "postgres://" / "postgresql://" connection strings
// to the Npgsql key=value format.
string connectionString;
if (rawDbUrl.StartsWith("postgres://") || rawDbUrl.StartsWith("postgresql://"))
{
    // Convert URI → Npgsql connection string
    var uri = new Uri(rawDbUrl.Replace("postgresql://", "postgres://"));
    var userInfo = uri.UserInfo.Split(':');
    var host     = uri.Host;
    var port     = uri.Port > 0 ? uri.Port : 5432;
    var database = uri.AbsolutePath.TrimStart('/');
    var sb       = new System.Text.StringBuilder();
    sb.Append($"Host={host};Port={port};Database={database};");
    if (userInfo.Length >= 1 && !string.IsNullOrEmpty(userInfo[0]))
        sb.Append($"Username={userInfo[0]};");
    if (userInfo.Length >= 2)
        sb.Append($"Password={userInfo[1]};");
    connectionString = sb.ToString();
}
else
{
    // Already in Npgsql key=value format
    connectionString = rawDbUrl;
}

// ------------------------------------------------------------------
// Services
// ------------------------------------------------------------------
builder.Services.AddControllers()
    .AddJsonOptions(options =>
    {
        // Use camelCase off by default; we use explicit [JsonPropertyName] attributes
        // so we need the property names passed through as-is.
        options.JsonSerializerOptions.PropertyNamingPolicy = null;
    });

builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyHeader()
              .AllowAnyMethod();
    });
});

// Singleton DB (stateless, thread-safe)
builder.Services.AddSingleton<Database>(_ => new Database(connectionString));

// Transient scraper (each resolve gets its own HttpClient wrapping is fine here)
builder.Services.AddTransient<ProductScraper>(sp => new ProductScraper(sp.GetRequiredService<Database>()));

// Hourly background refresh
builder.Services.AddHostedService<AutoRefreshService>();

// ------------------------------------------------------------------
// Listen on port 5002
// ------------------------------------------------------------------
builder.WebHost.UseUrls("http://0.0.0.0:5001");

var app = builder.Build();

// ------------------------------------------------------------------
// Middleware pipeline
// ------------------------------------------------------------------
app.UseCors();
app.UseAuthorization();
app.MapControllers();

// ------------------------------------------------------------------
// One-time DB init at startup
// ------------------------------------------------------------------
var db = app.Services.GetRequiredService<Database>();
db.InitDb();

Console.WriteLine("Starting Terpene Sorter C# API server...");
Console.WriteLine("API available at http://localhost:5002");
Console.WriteLine("\nEndpoints:");
Console.WriteLine("  GET  /api/products    - Get all products (with optional filtering/sorting)");
Console.WriteLine("  GET  /api/refresh     - Trigger a fresh scrape");
Console.WriteLine("  POST /api/refresh     - Trigger a fresh scrape");
Console.WriteLine("  GET  /api/terpenes    - List all available terpenes");
Console.WriteLine("  GET  /api/categories  - List all categories");
Console.WriteLine("  GET  /api/strain-types - List all strain types");
Console.WriteLine("  GET  /api/stats       - Get data statistics");
Console.WriteLine("  GET  /api/health      - Health check");

app.Run();

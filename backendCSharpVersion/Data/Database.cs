using System.Text.Json;
using Npgsql;
using NpgsqlTypes;
using backendCSharpVersion.Models;

namespace backendCSharpVersion.Data;

public class Database
{
    private readonly string _connectionString;

    public Database(string connectionString)
    {
        _connectionString = connectionString;
    }

    private NpgsqlConnection GetConnection()
    {
        return new NpgsqlConnection(_connectionString);
    }

    public void InitDb()
    {
        const string ddl = """
            CREATE TABLE IF NOT EXISTS products (
                variant_id      INTEGER PRIMARY KEY,
                name            TEXT           NOT NULL,
                brand           TEXT           NOT NULL DEFAULT '',
                category        TEXT           NOT NULL DEFAULT '',
                strain_type     TEXT           NOT NULL DEFAULT '',
                price           NUMERIC(10,2)  NOT NULL DEFAULT 0,
                sale_price      NUMERIC(10,2)  NOT NULL DEFAULT 0,
                weight          TEXT           NOT NULL DEFAULT '',
                thc             NUMERIC(8,3)   NOT NULL DEFAULT 0,
                cbd             NUMERIC(8,3)   NOT NULL DEFAULT 0,
                image           TEXT           NOT NULL DEFAULT '',
                url             TEXT           NOT NULL DEFAULT '',
                terpenes        JSONB          NOT NULL DEFAULT '{}',
                total_terpenes  NUMERIC(8,4)   NOT NULL DEFAULT 0,
                purchase_type   TEXT           NOT NULL DEFAULT '',
                updated_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW()
            );
            """;

        using var conn = GetConnection();
        conn.Open();

        using (var cmd = new NpgsqlCommand(ddl, conn))
        {
            cmd.ExecuteNonQuery();
        }

        using (var cmd = new NpgsqlCommand(
            "ALTER TABLE products ADD COLUMN IF NOT EXISTS purchase_type TEXT NOT NULL DEFAULT '';",
            conn))
        {
            cmd.ExecuteNonQuery();
        }
    }

    public void SaveProducts(List<Product> products)
    {
        var valid = products.Where(p => !string.IsNullOrEmpty(p.Name) && p.VariantId != 0).ToList();
        if (valid.Count == 0)
        {
            Console.WriteLine("SaveProducts: no valid rows to upsert (need name + variant_id)");
            return;
        }

        const string sql = """
            INSERT INTO products (
                variant_id, name, brand, category, strain_type,
                price, sale_price, weight, thc, cbd,
                image, url, terpenes, total_terpenes, purchase_type
            ) VALUES (
                @variant_id, @name, @brand, @category, @strain_type,
                @price, @sale_price, @weight, @thc, @cbd,
                @image, @url, @terpenes::jsonb, @total_terpenes, @purchase_type
            )
            ON CONFLICT (variant_id) DO UPDATE SET
                name           = EXCLUDED.name,
                brand          = EXCLUDED.brand,
                category       = EXCLUDED.category,
                strain_type    = EXCLUDED.strain_type,
                price          = EXCLUDED.price,
                sale_price     = EXCLUDED.sale_price,
                weight         = EXCLUDED.weight,
                thc            = EXCLUDED.thc,
                cbd            = EXCLUDED.cbd,
                image          = EXCLUDED.image,
                url            = EXCLUDED.url,
                terpenes       = EXCLUDED.terpenes,
                total_terpenes = EXCLUDED.total_terpenes,
                purchase_type  = EXCLUDED.purchase_type,
                updated_at     = NOW()
            """;

        using var conn = GetConnection();
        conn.Open();
        using var batch = new NpgsqlBatch(conn);

        foreach (var p in valid)
        {
            var cmd = new NpgsqlBatchCommand(sql);
            cmd.Parameters.AddWithValue("variant_id", p.VariantId);
            cmd.Parameters.AddWithValue("name", p.Name);
            cmd.Parameters.AddWithValue("brand", p.Brand);
            cmd.Parameters.AddWithValue("category", p.Category);
            cmd.Parameters.AddWithValue("strain_type", p.StrainType);
            cmd.Parameters.AddWithValue("price", p.Price);
            cmd.Parameters.AddWithValue("sale_price", p.SalePrice);
            cmd.Parameters.AddWithValue("weight", p.Weight);
            cmd.Parameters.AddWithValue("thc", p.Thc);
            cmd.Parameters.AddWithValue("cbd", p.Cbd);
            cmd.Parameters.AddWithValue("image", p.Image);
            cmd.Parameters.AddWithValue("url", p.Url);
            cmd.Parameters.Add(new NpgsqlParameter("terpenes", NpgsqlDbType.Jsonb)
            {
                Value = JsonSerializer.Serialize(p.Terpenes)
            });
            cmd.Parameters.AddWithValue("total_terpenes", p.TotalTerpenes);
            cmd.Parameters.AddWithValue("purchase_type", p.PurchaseType);
            batch.BatchCommands.Add(cmd);
        }

        batch.ExecuteNonQuery();

        Console.WriteLine($"Upserted {valid.Count} products into PostgreSQL ({products.Count - valid.Count} skipped)");
    }

    public void DeleteStaleProducts(IEnumerable<int> currentVariantIds)
    {
        var ids = currentVariantIds.ToList();
        if (ids.Count == 0)
        {
            Console.WriteLine("DeleteStaleProducts: empty id set, skipping to avoid wiping all products");
            return;
        }

        using var conn = GetConnection();
        conn.Open();
        using var cmd = new NpgsqlCommand("DELETE FROM products WHERE variant_id != ALL(@ids)", conn);
        cmd.Parameters.Add(new NpgsqlParameter("ids", NpgsqlDbType.Array | NpgsqlDbType.Integer)
        {
            Value = ids.ToArray()
        });
        var deleted = cmd.ExecuteNonQuery();
        if (deleted > 0)
            Console.WriteLine($"Removed {deleted} stale product(s) no longer in the API");
    }

    public List<Product> LoadProducts(ProductFilters? filters = null)
    {
        var whereClauses = new List<string>();
        var paramValues = new List<(string name, object value)>();
        int paramIndex = 1;

        if (filters != null)
        {
            foreach (var (field, value) in new[]
            {
                ("purchase_type", filters.PurchaseType),
                ("category", filters.Category),
                ("strain_type", filters.StrainType),
            })
            {
                if (!string.IsNullOrEmpty(value))
                {
                    whereClauses.Add($"LOWER({field}) = LOWER(@p{paramIndex})");
                    paramValues.Add(($"p{paramIndex}", value));
                    paramIndex++;
                }
            }

            if (filters.MinThc.HasValue)
            {
                whereClauses.Add($"thc >= @p{paramIndex}");
                paramValues.Add(($"p{paramIndex}", filters.MinThc.Value));
                paramIndex++;
            }

            if (filters.MaxThc.HasValue)
            {
                whereClauses.Add($"thc <= @p{paramIndex}");
                paramValues.Add(($"p{paramIndex}", filters.MaxThc.Value));
                paramIndex++;
            }
        }

        var where = whereClauses.Count > 0
            ? "WHERE " + string.Join(" AND ", whereClauses)
            : "";

        var querySql = $"""
            SELECT
                variant_id,
                name,
                brand,
                category,
                strain_type,
                CAST(price          AS FLOAT) AS price,
                CAST(sale_price     AS FLOAT) AS sale_price,
                weight,
                CAST(thc            AS FLOAT) AS thc,
                CAST(cbd            AS FLOAT) AS cbd,
                image,
                url,
                terpenes,
                CAST(total_terpenes AS FLOAT) AS total_terpenes,
                purchase_type
            FROM products
            {where}
            """;

        var results = new List<Product>();

        try
        {
            using var conn = GetConnection();
            conn.Open();
            using var cmd = new NpgsqlCommand(querySql, conn);

            foreach (var (name, value) in paramValues)
            {
                cmd.Parameters.AddWithValue(name, value);
            }

            using var reader = cmd.ExecuteReader();
            while (reader.Read())
            {
                var terpenesJson = reader.GetString(reader.GetOrdinal("terpenes"));
                var terpenes = JsonSerializer.Deserialize<Dictionary<string, double>>(terpenesJson)
                               ?? new Dictionary<string, double>();

                results.Add(new Product
                {
                    VariantId     = reader.GetInt32(reader.GetOrdinal("variant_id")),
                    Name          = reader.GetString(reader.GetOrdinal("name")),
                    Brand         = reader.GetString(reader.GetOrdinal("brand")),
                    Category      = reader.GetString(reader.GetOrdinal("category")),
                    StrainType    = reader.GetString(reader.GetOrdinal("strain_type")),
                    Price         = reader.GetDouble(reader.GetOrdinal("price")),
                    SalePrice     = reader.GetDouble(reader.GetOrdinal("sale_price")),
                    Weight        = reader.GetString(reader.GetOrdinal("weight")),
                    Thc           = reader.GetDouble(reader.GetOrdinal("thc")),
                    Cbd           = reader.GetDouble(reader.GetOrdinal("cbd")),
                    Image         = reader.GetString(reader.GetOrdinal("image")),
                    Url           = reader.GetString(reader.GetOrdinal("url")),
                    Terpenes      = terpenes,
                    TotalTerpenes = reader.GetDouble(reader.GetOrdinal("total_terpenes")),
                    PurchaseType  = reader.GetString(reader.GetOrdinal("purchase_type")),
                });
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"LoadProducts error: {ex.Message}");
        }

        return results;
    }
}

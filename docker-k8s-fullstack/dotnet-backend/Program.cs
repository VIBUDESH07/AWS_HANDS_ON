using Microsoft.EntityFrameworkCore;
using Npgsql;
using TaskApi.Data;
using TaskApi.Models;

var builder = WebApplication.CreateBuilder(args);

// Env variable `ConnectionStrings__Default` → config key `ConnectionStrings:Default`
var connectionString = builder.Configuration.GetConnectionString("Default")
    ?? throw new InvalidOperationException("ConnectionStrings__Default environment variable set pannala");

builder.Services.AddDbContext<AppDbContext>(options => options.UseNpgsql(connectionString));

var app = builder.Build();

// `dotnet TaskApi.dll --init-db` → table create panni exit. Compose-la one-shot service,
// K8s-la Job — app replicas start aagura munnaadi oru thadava mattum run aagum.
if (args.Contains("--init-db"))
{
    using var scope = app.Services.CreateScope();
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    await db.Database.EnsureCreatedAsync();
    app.Logger.LogInformation("Database schema ready");
    return;
}

// Liveness — DB-a touch pannadhu
app.MapGet("/api/health", () => Results.Ok(new
{
    status = "ok",
    backend = "dotnet",
    hostname = Environment.MachineName,
}));

// Readiness — DB reachable + table irukka nu check
app.MapGet("/api/ready", async (AppDbContext db) =>
{
    try
    {
        await db.Tasks.AnyAsync();
        return Results.Ok(new { status = "ready" });
    }
    catch (NpgsqlException error)
    {
        return Results.Json(new { status = "not-ready", error = error.Message }, statusCode: StatusCodes.Status503ServiceUnavailable);
    }
});

app.MapGet("/api/tasks", async (AppDbContext db) =>
    await db.Tasks.OrderByDescending(t => t.CreatedAt).ToListAsync());

app.MapPost("/api/tasks", async (CreateTaskRequest request, AppDbContext db) =>
{
    var title = request.Title?.Trim() ?? string.Empty;
    if (title.Length == 0)
    {
        return Results.BadRequest(new { error = "title is required" });
    }

    var task = new TaskItem { Title = title[..Math.Min(title.Length, TaskItem.TitleMaxLength)] };
    db.Tasks.Add(task);
    await db.SaveChangesAsync();
    return Results.Created($"/api/tasks/{task.Id}", task);
});

app.MapPatch("/api/tasks/{id:int}", async (int id, UpdateTaskRequest request, AppDbContext db) =>
{
    var task = await db.Tasks.FindAsync(id);
    if (task is null)
    {
        return Results.NotFound(new { error = "Task not found" });
    }

    if (request.Title is not null)
    {
        var title = request.Title.Trim();
        if (title.Length == 0)
        {
            return Results.BadRequest(new { error = "title cannot be empty" });
        }
        task.Title = title[..Math.Min(title.Length, TaskItem.TitleMaxLength)];
    }
    if (request.Done is bool done)
    {
        task.Done = done;
    }

    await db.SaveChangesAsync();
    return Results.Ok(task);
});

app.MapDelete("/api/tasks/{id:int}", async (int id, AppDbContext db) =>
{
    var deleted = await db.Tasks.Where(t => t.Id == id).ExecuteDeleteAsync();
    return deleted == 0
        ? Results.NotFound(new { error = "Task not found" })
        : Results.NoContent();
});

app.Run();

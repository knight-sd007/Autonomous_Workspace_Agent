using P07.Api.Middleware;
using P07.Infrastructure;

var builder = WebApplication.CreateBuilder(args);

// Add Controllers
builder.Services.AddControllers();

// Add Swagger / OpenAPI services
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new Microsoft.OpenApi.OpenApiInfo
    {
        Title = "P07 Autonomous Workspace Agent API",
        Version = "v1",
        Description = "ASP.NET Core Web API foundation for autonomous workspace developer agent orchestration."
    });
});

// Add Infrastructure & Application Services
builder.Services.AddInfrastructureServices(builder.Configuration);

var app = builder.Build();

// Global Exception Handler
app.UseMiddleware<ErrorHandlingMiddleware>();

// Enable Swagger UI (documentation view).
app.UseSwagger();
app.UseSwaggerUI(c =>
{
    c.SwaggerEndpoint("/swagger/v1/swagger.json", "P07 API v1");
    c.RoutePrefix = "swagger";
    // Read-only settings.
    c.SupportedSubmitMethods();
});

// The ASP.NET Core API and the compiled SvelteKit SPA share the same origin.
// No CORS policy is required for the production frontend.
app.UseDefaultFiles();
app.UseStaticFiles();

app.MapControllers();

// SvelteKit SPA fallback for client-side routes such as /docs/swagger and /docs/mcp.
app.MapFallbackToFile("index.html");

app.Run();

// Required for WebApplicationFactory in integration tests
public partial class Program { }

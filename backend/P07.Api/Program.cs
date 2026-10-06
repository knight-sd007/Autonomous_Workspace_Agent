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

// Add CORS policy for SvelteKit frontend
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowFrontend", policy =>
    {
        policy.WithOrigins(
            builder.Configuration["Frontend:Url"] ?? "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8007",
            "https://agent.vaikuntrix.in"
        )
        .AllowAnyHeader()
        .AllowAnyMethod();
    });
});

var app = builder.Build();

// Global Exception Handler
app.UseMiddleware<ErrorHandlingMiddleware>();

// Enable Swagger UI (Documentation view)
app.UseSwagger();
app.UseSwaggerUI(c =>
{
    c.SwaggerEndpoint("/swagger/v1/swagger.json", "P07 API v1");
    c.RoutePrefix = "swagger";
    // Read-only settings
    c.SupportedSubmitMethods(); // Disable "Try it out" execution in production compliance
});

app.UseCors("AllowFrontend");

app.MapControllers();

app.Run();

// Required for WebApplicationFactory in integration tests
public partial class Program { }

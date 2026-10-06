using Microsoft.AspNetCore.Mvc;
using P07.Application.Common.Interfaces;
using P07.Application.DTOs;

namespace P07.Api.Controllers;

[ApiController]
[Route("[controller]")]
[Route("api/v1/[controller]")]
public class HealthController : ControllerBase
{
    private readonly IAgentRuntimeClient _agentRuntimeClient;

    public HealthController(IAgentRuntimeClient agentRuntimeClient)
    {
        _agentRuntimeClient = agentRuntimeClient;
    }

    [HttpGet]
    [ProducesResponseType(typeof(HealthCheckResponse), StatusCodes.Status200OK)]
    public async Task<IActionResult> GetHealth(CancellationToken cancellationToken)
    {
        var agentHealthy = await _agentRuntimeClient.CheckHealthAsync(cancellationToken);

        var response = new HealthCheckResponse
        {
            Status = "Healthy",
            Service = "P07.Api (ASP.NET Core Web API)",
            Version = "1.0.0",
            TimestampUtc = DateTime.UtcNow,
            Subsystems = new Dictionary<string, string>
            {
                ["api"] = "Healthy",
                ["agentRuntime"] = agentHealthy ? "Healthy" : "OfflineFallbackAvailable"
            }
        };

        return Ok(response);
    }
}

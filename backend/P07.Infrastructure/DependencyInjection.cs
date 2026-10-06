using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using P07.Application.Common.Interfaces;
using P07.Application.Services;
using P07.Infrastructure.Clients;

namespace P07.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructureServices(this IServiceCollection services, IConfiguration configuration)
    {
        services.AddSingleton<ISessionService, SessionService>();

        var agentUrl = configuration["AgentRuntime:BaseUrl"] ?? "http://127.0.0.1:8001";

        services.AddHttpClient<IAgentRuntimeClient, AgentRuntimeHttpClient>(client =>
        {
            client.BaseAddress = new Uri(agentUrl);
            client.Timeout = TimeSpan.FromSeconds(30);
        });

        return services;
    }
}

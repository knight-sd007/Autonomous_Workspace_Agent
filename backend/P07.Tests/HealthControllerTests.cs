using System.Net;
using Microsoft.AspNetCore.Mvc;
using Moq;
using P07.Api.Controllers;
using P07.Application.Common.Interfaces;
using P07.Application.DTOs;
using Xunit;

namespace P07.Tests;

public class HealthControllerTests
{
    [Fact]
    public async Task GetHealth_ReturnsOk_WithSubsystemStatus()
    {
        // Arrange
        var mockAgentClient = new Mock<IAgentRuntimeClient>();
        mockAgentClient.Setup(c => c.CheckHealthAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(true);

        var controller = new HealthController(mockAgentClient.Object);

        // Act
        var result = await controller.GetHealth(CancellationToken.None);

        // Assert
        var okResult = Assert.IsType<OkObjectResult>(result);
        var response = Assert.IsType<HealthCheckResponse>(okResult.Value);
        Assert.Equal("Healthy", response.Status);
        Assert.Equal("P07.Api (ASP.NET Core Web API)", response.Service);
        Assert.Equal("Healthy", response.Subsystems["api"]);
        Assert.Equal("Healthy", response.Subsystems["agentRuntime"]);
    }
}

using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using Moq;
using P07.Api.Controllers;
using P07.Application.Common.Interfaces;
using P07.Application.DTOs;
using P07.Application.Services;
using Xunit;

namespace P07.Tests;

public class AgentControllerTests
{
    [Fact]
    public async Task ExecuteChat_ValidMessage_ReturnsSuccessResponse()
    {
        // Arrange
        var mockAgentClient = new Mock<IAgentRuntimeClient>();
        var sessionService = new SessionService();
        var mockLogger = new Mock<ILogger<AgentController>>();

        mockAgentClient.Setup(c => c.ExecuteChatAsync(It.IsAny<AgentChatRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new AgentChatResponse
            {
                SessionId = "test_sess_1",
                Status = "success",
                FinalAnswer = "Task completed successfully."
            });

        var controller = new AgentController(mockAgentClient.Object, sessionService, mockLogger.Object);

        var request = new AgentChatRequest
        {
            Message = "List all workspace files",
            Provider = "offline"
        };

        // Act
        var result = await controller.ExecuteChat(request, CancellationToken.None);

        // Assert
        var okResult = Assert.IsType<OkObjectResult>(result);
        var response = Assert.IsType<AgentChatResponse>(okResult.Value);
        Assert.Equal("success", response.Status);
        Assert.Equal("Task completed successfully.", response.FinalAnswer);
    }

    [Fact]
    public async Task ExecuteChat_EmptyMessage_ReturnsBadRequest()
    {
        // Arrange
        var mockAgentClient = new Mock<IAgentRuntimeClient>();
        var sessionService = new SessionService();
        var mockLogger = new Mock<ILogger<AgentController>>();

        var controller = new AgentController(mockAgentClient.Object, sessionService, mockLogger.Object);

        var request = new AgentChatRequest
        {
            Message = "   "
        };

        // Act
        var result = await controller.ExecuteChat(request, CancellationToken.None);

        // Assert
        Assert.IsType<BadRequestObjectResult>(result);
    }

    [Fact]
    public async Task ExecuteApproval_ValidApproval_ReturnsOk()
    {
        // Arrange
        var mockAgentClient = new Mock<IAgentRuntimeClient>();
        var sessionService = new SessionService();
        var mockLogger = new Mock<ILogger<AgentController>>();

        var session = await sessionService.CreateSessionAsync("Test Session");

        mockAgentClient.Setup(c => c.ExecuteApprovalAsync(It.IsAny<AgentApprovalRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new AgentChatResponse
            {
                SessionId = session.Id,
                Status = "success",
                FinalAnswer = "Approved action executed successfully."
            });

        var controller = new AgentController(mockAgentClient.Object, sessionService, mockLogger.Object);

        var request = new AgentApprovalRequest
        {
            SessionId = session.Id,
            ApprovalId = "appr_123",
            Decision = "approve"
        };

        // Act
        var result = await controller.ExecuteApproval(request, CancellationToken.None);

        // Assert
        var okResult = Assert.IsType<OkObjectResult>(result);
        var response = Assert.IsType<AgentChatResponse>(okResult.Value);
        Assert.Equal("success", response.Status);
        Assert.Equal("Approved action executed successfully.", response.FinalAnswer);
    }

    [Fact]
    public async Task ExecuteApproval_NonExistentSession_ReturnsBadRequest()
    {
        // Arrange
        var mockAgentClient = new Mock<IAgentRuntimeClient>();
        var sessionService = new SessionService();
        var mockLogger = new Mock<ILogger<AgentController>>();

        var controller = new AgentController(mockAgentClient.Object, sessionService, mockLogger.Object);

        var request = new AgentApprovalRequest
        {
            SessionId = "non_existent_session",
            ApprovalId = "appr_123",
            Decision = "approve"
        };

        // Act
        var result = await controller.ExecuteApproval(request, CancellationToken.None);

        // Assert
        Assert.IsType<BadRequestObjectResult>(result);
    }

    [Fact]
    public async Task ExecuteApproval_MissingFields_ReturnsBadRequest()
    {
        // Arrange
        var mockAgentClient = new Mock<IAgentRuntimeClient>();
        var sessionService = new SessionService();
        var mockLogger = new Mock<ILogger<AgentController>>();

        var controller = new AgentController(mockAgentClient.Object, sessionService, mockLogger.Object);

        var request = new AgentApprovalRequest
        {
            SessionId = "",
            ApprovalId = ""
        };

        // Act
        var result = await controller.ExecuteApproval(request, CancellationToken.None);

        // Assert
        Assert.IsType<BadRequestObjectResult>(result);
    }
}

using Microsoft.AspNetCore.Mvc;
using P07.Application.Common.Interfaces;
using P07.Application.DTOs;
using P07.Domain.Enums;
using P07.Domain.Models;

namespace P07.Api.Controllers;

[ApiController]
[Route("api/v1/[controller]")]
public class AgentController : ControllerBase
{
    private readonly IAgentRuntimeClient _agentRuntimeClient;
    private readonly ISessionService _sessionService;
    private readonly ILogger<AgentController> _logger;

    public AgentController(
        IAgentRuntimeClient agentRuntimeClient,
        ISessionService sessionService,
        ILogger<AgentController> logger)
    {
        _agentRuntimeClient = agentRuntimeClient;
        _sessionService = sessionService;
        _logger = logger;
    }

    [HttpPost("chat")]
    [ProducesResponseType(typeof(AgentChatResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> ExecuteChat([FromBody] AgentChatRequest request, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.Message))
        {
            return BadRequest(new { error = "Message cannot be empty." });
        }

        // Ensure session exists or create one
        string sessionId = request.SessionId ?? string.Empty;
        if (string.IsNullOrWhiteSpace(sessionId))
        {
            var newSession = await _sessionService.CreateSessionAsync();
            sessionId = newSession.Id;
            request.SessionId = sessionId;
        }

        // Record incoming user step
        await _sessionService.AddStepAsync(sessionId, new AgentStep
        {
            Role = "user",
            Input = request.Message,
            Status = ExecutionStatus.Success
        });

        // Delegate to Python Agent Runtime
        var result = await _agentRuntimeClient.ExecuteChatAsync(request, cancellationToken);

        // Record agent response step
        await _sessionService.AddStepAsync(sessionId, new AgentStep
        {
            Role = "agent",
            Output = result.FinalAnswer,
            Status = result.Status == "success" ? ExecutionStatus.Success : ExecutionStatus.Error
        });

        return Ok(result);
    }

    [HttpPost("approve")]
    [ProducesResponseType(typeof(AgentChatResponse), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> ExecuteApproval([FromBody] AgentApprovalRequest request, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(request.SessionId) || string.IsNullOrWhiteSpace(request.ApprovalId))
        {
            return BadRequest(new { error = "SessionId and ApprovalId are required." });
        }

        // Verify session exists
        var session = await _sessionService.GetSessionAsync(request.SessionId);
        if (session == null)
        {
            return BadRequest(new { error = $"Session '{request.SessionId}' not found." });
        }

        // Record user approval decision in session history
        await _sessionService.AddStepAsync(request.SessionId, new AgentStep
        {
            Role = "user",
            Input = $"[HITL Approval Decision] {request.Decision.ToUpperInvariant()} for approval ID: {request.ApprovalId}",
            Status = ExecutionStatus.Success
        });

        // Forward approval decision to Agent Runtime
        var result = await _agentRuntimeClient.ExecuteApprovalAsync(request, cancellationToken);

        // Record agent result in session history
        await _sessionService.AddStepAsync(request.SessionId, new AgentStep
        {
            Role = "agent",
            Output = result.FinalAnswer,
            Status = result.Status == "success" ? ExecutionStatus.Success : ExecutionStatus.Error
        });

        return Ok(result);
    }
}

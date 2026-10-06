using P07.Domain.Enums;

namespace P07.Application.DTOs;

public class AgentChatResponse
{
    public string SessionId { get; set; } = string.Empty;
    public string Status { get; set; } = "success";
    public string FinalAnswer { get; set; } = string.Empty;
    public List<AgentStepDto> Steps { get; set; } = new();
    public PendingConfirmationDto? PendingConfirmation { get; set; }
    public string? ErrorMessage { get; set; }
}

public class AgentStepDto
{
    public int Step { get; set; }
    public string Tool { get; set; } = string.Empty;
    public object? Output { get; set; }
}

public class PendingConfirmationDto
{
    public string? ApprovalId { get; set; }
    public string? SessionId { get; set; }
    public string ToolName { get; set; } = string.Empty;
    public string Resource { get; set; } = string.Empty;
    public string Reason { get; set; } = string.Empty;
    public Dictionary<string, object> ToolKwargs { get; set; } = new();
    public bool IsDestructive { get; set; }
    public string? ExpiresAt { get; set; }
}

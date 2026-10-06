using P07.Domain.Enums;

namespace P07.Domain.Models;

public class AgentStep
{
    public int StepIndex { get; set; }
    public string Role { get; set; } = "agent";
    public string? ToolName { get; set; }
    public string? Input { get; set; }
    public string? Output { get; set; }
    public ExecutionStatus Status { get; set; } = ExecutionStatus.Success;
    public DateTime TimestampUtc { get; set; } = DateTime.UtcNow;
}

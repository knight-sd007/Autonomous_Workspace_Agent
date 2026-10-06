using System.ComponentModel.DataAnnotations;

namespace P07.Application.DTOs;

public class AgentApprovalRequest
{
    [Required]
    public string SessionId { get; set; } = string.Empty;

    [Required]
    public string ApprovalId { get; set; } = string.Empty;

    [Required]
    [RegularExpression("^(approve|reject)$", ErrorMessage = "Decision must be 'approve' or 'reject'.")]
    public string Decision { get; set; } = "approve";

    public Dictionary<string, object>? ToolKwargs { get; set; }
}

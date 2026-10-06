using System.ComponentModel.DataAnnotations;

namespace P07.Application.DTOs;

public class AgentChatRequest
{
    [Required]
    public string Message { get; set; } = string.Empty;

    public string? SessionId { get; set; }

    public string Provider { get; set; } = "offline";

    public string? Model { get; set; }

    [Range(1, 15)]
    public int MaxSteps { get; set; } = 5;

    public bool UserConfirmed { get; set; } = false;
}

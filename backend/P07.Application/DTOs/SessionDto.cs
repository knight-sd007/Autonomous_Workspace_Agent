namespace P07.Application.DTOs;

public class SessionDto
{
    public string Id { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public DateTime CreatedAtUtc { get; set; }
    public DateTime LastActiveAtUtc { get; set; }
    public int MessageCount { get; set; }
}

public class CreateSessionRequest
{
    public string? Title { get; set; }
}

namespace P07.Application.DTOs;

public class HealthCheckResponse
{
    public string Status { get; set; } = "Healthy";
    public string Service { get; set; } = "P07.Api";
    public string Version { get; set; } = "1.0.0";
    public DateTime TimestampUtc { get; set; } = DateTime.UtcNow;
    public Dictionary<string, string> Subsystems { get; set; } = new();
}

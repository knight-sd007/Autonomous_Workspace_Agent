using P07.Application.DTOs;
using P07.Domain.Models;

namespace P07.Application.Common.Interfaces;

public interface ISessionService
{
    Task<SessionDto> CreateSessionAsync(string? title = null);
    Task<SessionDto?> GetSessionAsync(string id);
    Task<IReadOnlyList<SessionDto>> ListSessionsAsync();
    Task<bool> AddStepAsync(string sessionId, AgentStep step);
    Task<bool> DeleteSessionAsync(string id);
}

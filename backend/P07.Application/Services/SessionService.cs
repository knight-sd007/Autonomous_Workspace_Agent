using System.Collections.Concurrent;
using P07.Application.Common.Interfaces;
using P07.Application.DTOs;
using P07.Domain.Models;

namespace P07.Application.Services;

public class SessionService : ISessionService
{
    private static readonly ConcurrentDictionary<string, AgentSession> _sessions = new();

    public Task<SessionDto> CreateSessionAsync(string? title = null)
    {
        var session = new AgentSession
        {
            Title = string.IsNullOrWhiteSpace(title) ? $"Session {DateTime.UtcNow:yyyy-MM-dd HH:mm}" : title.Trim()
        };

        _sessions[session.Id] = session;
        return Task.FromResult(MapToDto(session));
    }

    public Task<SessionDto?> GetSessionAsync(string id)
    {
        if (_sessions.TryGetValue(id, out var session))
        {
            return Task.FromResult<SessionDto?>(MapToDto(session));
        }

        return Task.FromResult<SessionDto?>(null);
    }

    public Task<IReadOnlyList<SessionDto>> ListSessionsAsync()
    {
        var list = _sessions.Values
            .OrderByDescending(s => s.LastActiveAtUtc)
            .Select(MapToDto)
            .ToList();

        return Task.FromResult<IReadOnlyList<SessionDto>>(list);
    }

    public Task<bool> AddStepAsync(string sessionId, AgentStep step)
    {
        if (_sessions.TryGetValue(sessionId, out var session))
        {
            lock (session)
            {
                step.StepIndex = session.History.Count + 1;
                session.History.Add(step);
                session.LastActiveAtUtc = DateTime.UtcNow;
            }
            return Task.FromResult(true);
        }

        return Task.FromResult(false);
    }

    public Task<bool> DeleteSessionAsync(string id)
    {
        return Task.FromResult(_sessions.TryRemove(id, out _));
    }

    private static SessionDto MapToDto(AgentSession s)
    {
        return new SessionDto
        {
            Id = s.Id,
            Title = s.Title,
            CreatedAtUtc = s.CreatedAtUtc,
            LastActiveAtUtc = s.LastActiveAtUtc,
            MessageCount = s.History.Count
        };
    }
}

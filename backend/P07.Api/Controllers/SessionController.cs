using Microsoft.AspNetCore.Mvc;
using P07.Application.Common.Interfaces;
using P07.Application.DTOs;

namespace P07.Api.Controllers;

[ApiController]
[Route("api/v1/[controller]s")]
public class SessionController : ControllerBase
{
    private readonly ISessionService _sessionService;

    public SessionController(ISessionService sessionService)
    {
        _sessionService = sessionService;
    }

    [HttpGet]
    [ProducesResponseType(typeof(IReadOnlyList<SessionDto>), StatusCodes.Status200OK)]
    public async Task<IActionResult> ListSessions()
    {
        var sessions = await _sessionService.ListSessionsAsync();
        return Ok(sessions);
    }

    [HttpGet("{id}")]
    [ProducesResponseType(typeof(SessionDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> GetSession(string id)
    {
        var session = await _sessionService.GetSessionAsync(id);
        if (session == null) return NotFound(new { error = $"Session '{id}' not found." });
        return Ok(session);
    }

    [HttpPost]
    [ProducesResponseType(typeof(SessionDto), StatusCodes.Status201Created)]
    public async Task<IActionResult> CreateSession([FromBody] CreateSessionRequest? request)
    {
        var session = await _sessionService.CreateSessionAsync(request?.Title);
        return CreatedAtAction(nameof(GetSession), new { id = session.Id }, session);
    }

    [HttpDelete("{id}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    public async Task<IActionResult> DeleteSession(string id)
    {
        await _sessionService.DeleteSessionAsync(id);
        return NoContent();
    }
}

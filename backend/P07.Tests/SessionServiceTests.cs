using P07.Application.Services;
using P07.Domain.Models;
using Xunit;

namespace P07.Tests;

public class SessionServiceTests
{
    [Fact]
    public async Task CreateSession_GeneratesValidSession()
    {
        // Arrange
        var service = new SessionService();

        // Act
        var session = await service.CreateSessionAsync("Test Session");

        // Assert
        Assert.NotNull(session);
        Assert.NotEmpty(session.Id);
        Assert.Equal("Test Session", session.Title);
        Assert.Equal(0, session.MessageCount);
    }

    [Fact]
    public async Task AddStep_IncrementsMessageCount()
    {
        // Arrange
        var service = new SessionService();
        var session = await service.CreateSessionAsync("Step Test");

        // Act
        var added = await service.AddStepAsync(session.Id, new AgentStep
        {
            Role = "user",
            Input = "List workspace files"
        });

        var retrieved = await service.GetSessionAsync(session.Id);

        // Assert
        Assert.True(added);
        Assert.NotNull(retrieved);
        Assert.Equal(1, retrieved.MessageCount);
    }
}

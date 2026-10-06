using P07.Application.DTOs;

namespace P07.Application.Common.Interfaces;

public interface IAgentRuntimeClient
{
    Task<AgentChatResponse> ExecuteChatAsync(AgentChatRequest request, CancellationToken cancellationToken = default);
    Task<AgentChatResponse> ExecuteApprovalAsync(AgentApprovalRequest request, CancellationToken cancellationToken = default);
    Task<bool> CheckHealthAsync(CancellationToken cancellationToken = default);
}

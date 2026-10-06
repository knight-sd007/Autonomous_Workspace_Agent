/**
 * Typed API Client for P07 ASP.NET Core Backend
 */

export interface AgentChatRequest {
	message: string;
	sessionId?: string;
	provider?: string;
	model?: string;
	maxSteps?: number;
	userConfirmed?: boolean;
}

export interface AgentApprovalRequest {
	sessionId: string;
	approvalId: string;
	decision: 'approve' | 'reject';
	toolKwargs?: Record<string, any>;
}

export interface AgentStepDto {
	step: number;
	tool: string;
	output: any;
}

export interface PendingConfirmationDto {
	approvalId?: string;
	sessionId?: string;
	toolName: string;
	resource: string;
	reason: string;
	toolKwargs: Record<string, any>;
	isDestructive: boolean;
	expiresAt?: string;
}

export interface AgentChatResponse {
	sessionId: string;
	status: string;
	finalAnswer: string;
	steps: AgentStepDto[];
	pendingConfirmation?: PendingConfirmationDto;
	errorMessage?: string;
}

export interface HealthCheckResponse {
	status: string;
	service: string;
	version: string;
	timestampUtc: string;
	subsystems: Record<string, string>;
}

export const API_BASE = '/api/v1';

export async function checkBackendHealth(): Promise<HealthCheckResponse> {
	const res = await fetch(`${API_BASE}/health`);
	if (!res.ok) throw new Error(`Healthcheck failed with status ${res.status}`);
	return res.json();
}

export async function sendAgentMessage(request: AgentChatRequest): Promise<AgentChatResponse> {
	const res = await fetch(`${API_BASE}/agent/chat`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(request)
	});

	if (!res.ok) {
		const errData = await res.json().catch(() => ({}));
		throw new Error(errData.error || errData.message || `Request failed with status ${res.status}`);
	}

	return res.json();
}

export async function approveAgentAction(request: AgentApprovalRequest): Promise<AgentChatResponse> {
	const res = await fetch(`${API_BASE}/agent/approve`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(request)
	});

	if (!res.ok) {
		const errData = await res.json().catch(() => ({}));
		throw new Error(errData.error || errData.message || `Approval request failed with status ${res.status}`);
	}

	return res.json();
}

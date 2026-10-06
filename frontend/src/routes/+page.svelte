<script lang="ts">
	import { onMount } from 'svelte';
	import {
		sendAgentMessage,
		approveAgentAction,
		checkBackendHealth,
		type AgentChatResponse,
		type PendingConfirmationDto,
		type HealthCheckResponse
	} from '$lib/api';

	let authenticated = false;
	let accessKey = '';
	let authError = '';

	let messageInput = '';
	let selectedProvider = 'offline';
	let maxSteps = 5;
	let isLoading = false;
	let errorMessage = '';

	let backendStatus: HealthCheckResponse | null = null;
	let chatResponses: AgentChatResponse[] = [];
	let currentSessionId = '';
	let pendingConfirmation: PendingConfirmationDto | null = null;

	onMount(async () => {
		try {
			backendStatus = await checkBackendHealth();
		} catch (e) {
			// Backend offline or local dev
		}
	});

	function handleLogin() {
		if (accessKey.trim().length > 0) {
			authenticated = true;
			authError = '';
		} else {
			authError = 'Please enter access key.';
		}
	}

	async function handleSendMessage() {
		if (!messageInput.trim()) return;

		isLoading = true;
		errorMessage = '';
		try {
			const res = await sendAgentMessage({
				message: messageInput,
				sessionId: currentSessionId || undefined,
				provider: selectedProvider,
				maxSteps: maxSteps
			});

			currentSessionId = res.sessionId;
			chatResponses = [...chatResponses, res];
			pendingConfirmation = res.pendingConfirmation || null;
			messageInput = '';
		} catch (e: any) {
			errorMessage = e.message || 'An error occurred while processing task.';
		} finally {
			isLoading = false;
		}
	}

	async function handleApprovalDecision(decision: 'approve' | 'reject') {
		if (!pendingConfirmation || !pendingConfirmation.approvalId) return;

		isLoading = true;
		errorMessage = '';
		try {
			const res = await approveAgentAction({
				sessionId: pendingConfirmation.sessionId || currentSessionId,
				approvalId: pendingConfirmation.approvalId,
				decision: decision,
				toolKwargs: pendingConfirmation.toolKwargs
			});

			chatResponses = [...chatResponses, res];
			pendingConfirmation = res.pendingConfirmation || null;
		} catch (e: any) {
			errorMessage = e.message || `Failed to process approval decision (${decision}).`;
		} finally {
			isLoading = false;
		}
	}
</script>

{#if !authenticated}
	<div class="login-card">
		<h2>🔐 Workspace Agent Access</h2>
		<p class="subtitle">Enter access key to unlock sandboxed developer agent console.</p>

		<form on:submit|preventDefault={handleLogin} class="login-form">
			<input
				type="password"
				bind:value={accessKey}
				placeholder="Enter Access Key..."
				class="input-field"
			/>
			{#if authError}
				<p class="error-text">{authError}</p>
			{/if}
			<button type="submit" class="btn-primary">Authenticate & Enter</button>
		</form>
	</div>
{:else}
	<div class="dashboard-grid">
		<!-- Sidebar Controls -->
		<section class="control-panel">
			<h3>⚙️ Controls & Provider</h3>

			<div class="control-group">
				<label for="provider-select">AI Provider</label>
				<select id="provider-select" bind:value={selectedProvider} class="select-field">
					<option value="offline">Offline Deterministic Fallback</option>
					<option value="openai">OpenAI (GPT-4o-mini)</option>
					<option value="gemini">Google Gemini (2.5 Flash)</option>
					<option value="nvidia">NVIDIA NIM (Llama 3.1)</option>
				</select>
			</div>

			<div class="control-group">
				<label for="steps-slider">Max Steps: {maxSteps}</label>
				<input id="steps-slider" type="range" min="1" max="10" bind:value={maxSteps} class="slider" />
			</div>

			<div class="status-box">
				<h4>System Health</h4>
				<p>Backend: <span class="status-tag">{backendStatus ? backendStatus.status : 'Ready (Mock/Local)'}</span></p>
				<p>Sandbox: <span class="status-tag">Active (/app/workspace)</span></p>
				<p>Session: <span class="session-id">{currentSessionId || 'New Session'}</span></p>
			</div>
		</section>

		<!-- Main Agent Chat Area -->
		<section class="chat-panel">
			<h3>🤖 Autonomous Agent Console</h3>

			<!-- Human confirmation alert if needed -->
			{#if pendingConfirmation}
				<div class="confirmation-banner">
					<div class="banner-header">
						<h4>⚠️ Human Approval Required ({pendingConfirmation.isDestructive ? 'DESTRUCTIVE' : 'MUTATING'})</h4>
						{#if pendingConfirmation.expiresAt}
							<span class="expiry-tag">Expires: {new Date(pendingConfirmation.expiresAt).toLocaleTimeString()}</span>
						{/if}
					</div>
					<p><strong>Action:</strong> <code>{pendingConfirmation.toolName}</code></p>
					<p><strong>Resource:</strong> <code>{pendingConfirmation.resource}</code></p>
					<p><strong>Reason:</strong> {pendingConfirmation.reason}</p>
					{#if pendingConfirmation.toolKwargs}
						<div class="args-preview">
							<strong>Validated Arguments:</strong>
							<pre>{JSON.stringify(pendingConfirmation.toolKwargs, null, 2)}</pre>
						</div>
					{/if}
					<div class="btn-group">
						<button on:click={() => handleApprovalDecision('approve')} disabled={isLoading} class="btn-approve">Approve & Execute</button>
						<button on:click={() => handleApprovalDecision('reject')} disabled={isLoading} class="btn-deny">Reject Action</button>
					</div>
				</div>
			{/if}

			<!-- Messages Output -->
			<div class="messages-container">
				{#if chatResponses.length === 0}
					<div class="empty-state">
						<p>No active tasks. Enter a directive below to start.</p>
						<p class="hint">Try: <em>"List all files in workspace"</em> or <em>"Write report to notes.txt"</em></p>
					</div>
				{:else}
					{#each chatResponses as response, i}
						<div class="response-card">
							<div class="response-header">
								<span class="step-badge">Run #{i + 1}</span>
								<span class="status-indicator {response.status}">{response.status}</span>
							</div>
							<pre class="response-body">{response.finalAnswer}</pre>

							{#if response.steps && response.steps.length > 0}
								<div class="steps-list">
									{#each response.steps as step}
										<div class="step-item">
											<strong>Step {step.step}:</strong> Tool <code>{step.tool}</code>
											{#if step.output}
												<pre class="step-output">{typeof step.output === 'object' ? JSON.stringify(step.output, null, 2) : step.output}</pre>
											{/if}
										</div>
									{/each}
								</div>
							{/if}
						</div>
					{/each}
				{/if}
			</div>

			{#if errorMessage}
				<div class="error-banner">{errorMessage}</div>
			{/if}

			<!-- Input Form -->
			<form on:submit|preventDefault={handleSendMessage} class="prompt-form">
				<input
					type="text"
					bind:value={messageInput}
					placeholder="Enter workspace directive (e.g. List files in workspace)..."
					disabled={isLoading}
					class="prompt-input"
				/>
				<button type="submit" disabled={isLoading || !messageInput.trim()} class="btn-submit">
					{isLoading ? 'Processing...' : 'Execute Task'}
				</button>
			</form>
		</section>
	</div>
{/if}

<style>
	.login-card {
		max-width: 440px;
		margin: 4rem auto;
		background: #1e293b;
		padding: 2.5rem;
		border-radius: 0.75rem;
		border: 1px solid #334155;
		text-align: center;
	}

	.subtitle {
		color: #94a3b8;
		font-size: 0.9rem;
		margin-bottom: 1.5rem;
	}

	.login-form {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.input-field, .select-field, .prompt-input {
		width: 100%;
		padding: 0.75rem 1rem;
		background: #0f172a;
		border: 1px solid #334155;
		border-radius: 0.5rem;
		color: #f8fafc;
		box-sizing: border-box;
	}

	.btn-primary, .btn-submit, .btn-approve {
		padding: 0.75rem 1.5rem;
		background: #2563eb;
		color: white;
		border: none;
		border-radius: 0.5rem;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.2s;
	}

	.btn-primary:hover, .btn-submit:hover, .btn-approve:hover {
		background: #1d4ed8;
	}

	.btn-deny {
		padding: 0.75rem 1.5rem;
		background: #dc2626;
		color: white;
		border: none;
		border-radius: 0.5rem;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.2s;
	}

	.btn-deny:hover {
		background: #b91c1c;
	}

	.dashboard-grid {
		display: grid;
		grid-template-columns: 280px 1fr;
		gap: 1.5rem;
	}

	.control-panel, .chat-panel {
		background: #1e293b;
		padding: 1.5rem;
		border-radius: 0.75rem;
		border: 1px solid #334155;
	}

	.control-group {
		margin-bottom: 1.25rem;
	}

	.control-group label {
		display: block;
		font-size: 0.85rem;
		color: #94a3b8;
		margin-bottom: 0.4rem;
	}

	.status-box {
		background: #0f172a;
		padding: 1rem;
		border-radius: 0.5rem;
		font-size: 0.85rem;
	}

	.status-tag {
		color: #34d399;
		font-weight: 600;
	}

	.session-id {
		color: #94a3b8;
		font-family: monospace;
		font-size: 0.75rem;
		word-break: break-all;
	}

	.confirmation-banner {
		background: #451a03;
		border: 1px solid #b45309;
		padding: 1.25rem;
		border-radius: 0.5rem;
		margin-bottom: 1rem;
	}

	.banner-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.expiry-tag {
		font-size: 0.75rem;
		background: #78350f;
		color: #fed7aa;
		padding: 0.2rem 0.5rem;
		border-radius: 0.25rem;
	}

	.args-preview {
		margin-top: 0.5rem;
		background: #1e1b18;
		padding: 0.5rem;
		border-radius: 0.25rem;
		font-size: 0.8rem;
	}

	.args-preview pre {
		margin: 0.25rem 0 0;
		white-space: pre-wrap;
		color: #fde68a;
	}

	.btn-group {
		display: flex;
		gap: 0.75rem;
		margin-top: 1rem;
	}

	.messages-container {
		min-height: 350px;
		max-height: 500px;
		overflow-y: auto;
		background: #0f172a;
		padding: 1rem;
		border-radius: 0.5rem;
		margin-bottom: 1rem;
	}

	.empty-state {
		text-align: center;
		padding: 3rem 1rem;
		color: #64748b;
	}

	.response-card {
		background: #1e293b;
		border: 1px solid #334155;
		padding: 1rem;
		border-radius: 0.5rem;
		margin-bottom: 1rem;
	}

	.response-header {
		display: flex;
		justify-content: space-between;
		font-size: 0.8rem;
		margin-bottom: 0.5rem;
	}

	.step-badge {
		background: #334155;
		padding: 0.2rem 0.5rem;
		border-radius: 0.25rem;
	}

	.status-indicator {
		padding: 0.2rem 0.5rem;
		border-radius: 0.25rem;
		font-size: 0.75rem;
		text-transform: uppercase;
		font-weight: 600;
	}

	.status-indicator.success {
		background: #064e3b;
		color: #6ee7b7;
	}

	.status-indicator.needs_confirmation {
		background: #78350f;
		color: #fde68a;
	}

	.status-indicator.rejected {
		background: #7f1d1d;
		color: #fca5a5;
	}

	.response-body {
		white-space: pre-wrap;
		font-family: monospace;
		font-size: 0.9rem;
		color: #e2e8f0;
	}

	.steps-list {
		margin-top: 0.75rem;
		border-top: 1px solid #334155;
		padding-top: 0.5rem;
	}

	.step-item {
		font-size: 0.85rem;
		margin-bottom: 0.4rem;
	}

	.step-output {
		background: #0f172a;
		padding: 0.4rem;
		border-radius: 0.25rem;
		font-size: 0.8rem;
		color: #94a3b8;
		white-space: pre-wrap;
	}

	.prompt-form {
		display: flex;
		gap: 0.75rem;
	}

	.error-banner {
		background: #7f1d1d;
		color: #fecaca;
		padding: 0.75rem;
		border-radius: 0.5rem;
		margin-bottom: 1rem;
	}

	.error-text {
		color: #f87171;
		font-size: 0.85rem;
	}
</style>

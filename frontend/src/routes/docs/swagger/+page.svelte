<script lang="ts">
	// Read-only Swagger Documentation View placeholder
</script>

<div class="doc-container">
	<h2>📄 ASP.NET Core OpenAPI / Swagger Documentation</h2>
	<p class="desc">
		Authenticated, read-only architectural specification for the backend REST API endpoints.
		Interactive execution ("Try it out") is disabled to maintain security compliance.
	</p>

	<div class="spec-card">
		<h3>Endpoints Overview (v1)</h3>
		<div class="endpoint-item">
			<span class="method get">GET</span>
			<code>/health</code>
			<span class="summary">Health & Subsystem Status Probes</span>
		</div>
		<div class="endpoint-item">
			<span class="method post">POST</span>
			<code>/api/v1/agent/chat</code>
			<span class="summary">Execute Agent Task via Orchestrator</span>
		</div>
		<div class="endpoint-item">
			<span class="method get">GET</span>
			<code>/api/v1/sessions</code>
			<span class="summary">List Active Agent Workstation Sessions</span>
		</div>
		<div class="endpoint-item">
			<span class="method post">POST</span>
			<code>/api/v1/sessions</code>
			<span class="summary">Create New Agent Workstation Session</span>
		</div>
	</div>
</div>

<style>
	.doc-container {
		background: #1e293b;
		padding: 2rem;
		border-radius: 0.75rem;
		border: 1px solid #334155;
	}
	.desc {
		color: #94a3b8;
		margin-bottom: 2rem;
	}
	.spec-card {
		background: #0f172a;
		padding: 1.5rem;
		border-radius: 0.5rem;
	}
	.endpoint-item {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 0.75rem;
		border-bottom: 1px solid #1e293b;
		font-family: monospace;
	}
	.method {
		padding: 0.2rem 0.6rem;
		border-radius: 0.25rem;
		font-weight: 700;
		font-size: 0.8rem;
	}
	.get {
		background: #065f46;
		color: #6ee7b7;
	}
	.post {
		background: #1e40af;
		color: #93c5fd;
	}
	.summary {
		color: #94a3b8;
		font-family: sans-serif;
		font-size: 0.85rem;
		margin-left: auto;
	}
</style>

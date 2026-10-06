<script lang="ts">
	export const prerender = true;
	export const ssr = false;
</script>

<div class="app-layout">
	<header class="app-header">
		<div class="brand">
			<span class="logo">🤖</span>
			<div>
				<h1 class="title">Autonomous Workspace Agent</h1>
				<span class="badge">P07 Workstation</span>
			</div>
		</div>
		<nav class="nav-links">
			<a href="/" class="nav-item">Dashboard & Chat</a>
			<a href="/docs/swagger" class="nav-item">API Docs (Swagger)</a>
			<a href="/docs/mcp" class="nav-item">MCP Tool Inspector</a>
		</nav>
	</header>

	<main class="app-content">
		<slot />
	</main>

	<footer class="app-footer">
		<p>P07 Autonomous Developer Workstation & Workspace Agent &bull; Hardened Sandbox Architecture</p>
	</footer>
</div>

<style>
	:global(body) {
		margin: 0;
		background: #0b1329;
		color: #e2e8f0;
		font-family: system-ui, -apple-system, sans-serif;
	}

	.app-layout {
		display: flex;
		flex-direction: column;
		min-height: 100vh;
	}

	.app-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem 2rem;
		background: #111c38;
		border-bottom: 1px solid #1e293b;
	}

	.brand {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.logo {
		font-size: 1.75rem;
	}

	.title {
		margin: 0;
		font-size: 1.25rem;
		font-weight: 600;
		color: #f8fafc;
	}

	.badge {
		font-size: 0.75rem;
		background: #1e3a8a;
		color: #93c5fd;
		padding: 0.15rem 0.5rem;
		border-radius: 9999px;
		font-weight: 500;
	}

	.nav-links {
		display: flex;
		gap: 1.25rem;
	}

	.nav-item {
		color: #94a3b8;
		text-decoration: none;
		font-size: 0.9rem;
		font-weight: 500;
		transition: color 0.2s;
	}

	.nav-item:hover {
		color: #60a5fa;
	}

	.app-content {
		flex: 1;
		padding: 2rem;
		max-width: 1200px;
		margin: 0 auto;
		width: 100%;
		box-sizing: border-box;
	}

	.app-footer {
		text-align: center;
		padding: 1rem;
		font-size: 0.8rem;
		color: #64748b;
		border-top: 1px solid #1e293b;
		background: #0f172a;
	}
</style>

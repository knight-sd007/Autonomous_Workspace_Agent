<script lang="ts">
	// Read-only MCP Documentation View
</script>

<div class="doc-container">
	<h2>🛠️ Model Context Protocol (MCP) Server Specifications</h2>
	<p class="desc">
		Read-only documentation of tools, JSON schemas, and access boundaries exposed by the custom Python MCP Server.
		Direct external invocation is restricted to internal authenticated agent processes.
	</p>

	<div class="tool-grid">
		<div class="tool-card">
			<div class="tool-header">
				<h3><code>list_files</code></h3>
				<span class="badge read">READ</span>
			</div>
			<p>Lists files and directories inside the sandboxed workspace root directory.</p>
			<h4>Input Schema</h4>
			<pre><code>{`{
  "sub_dir": "string (optional, default: '.')"
}`}</code></pre>
		</div>

		<div class="tool-card">
			<div class="tool-header">
				<h3><code>read_file</code></h3>
				<span class="badge read">READ</span>
			</div>
			<p>Reads text content from a file inside the sandboxed workspace root.</p>
			<h4>Input Schema</h4>
			<pre><code>{`{
  "file_path": "string (required)",
  "max_bytes": "integer (optional, default: 100000)"
}`}</code></pre>
		</div>

		<div class="tool-card">
			<div class="tool-header">
				<h3><code>inspect_schema</code></h3>
				<span class="badge read">READ</span>
			</div>
			<p>Inspects SQLite tables and columns inside the workspace database.</p>
			<h4>Input Schema</h4>
			<pre><code>{`{
  "db_filename": "string (optional, default: 'app_data.db')"
}`}</code></pre>
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
	.tool-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: 1.5rem;
	}
	.tool-card {
		background: #0f172a;
		padding: 1.25rem;
		border-radius: 0.5rem;
		border: 1px solid #1e293b;
	}
	.tool-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}
	.tool-header h3 {
		margin: 0;
	}
	.badge {
		font-size: 0.75rem;
		padding: 0.15rem 0.5rem;
		border-radius: 0.25rem;
		font-weight: 700;
	}
	.read {
		background: #065f46;
		color: #6ee7b7;
	}
	pre {
		background: #020617;
		padding: 0.75rem;
		border-radius: 0.25rem;
		font-size: 0.85rem;
		color: #cbd5e1;
		overflow-x: auto;
	}
</style>

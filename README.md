# Exa-Bundle (Universal Exasol Orchestrator)

A single installation entrypoint for the modern Exasol ecosystem. This tool automatically fetches OS-native database binaries, installs pre-compiled Rust extensions, and bridges local database secrets to the Exasol MCP Server.

## Installation

**Using `uv` (Recommended):**
\`\`\`bash
uv tool install exa-bundle
exa-bundle init
\`\`\`

**Using `curl` (Linux / macOS):**
\`\`\`bash
curl -fsSL https://raw.githubusercontent.com/your-org/exa-bundle/main/install.sh | bash
\`\`\`

## Usage Commands
- `exa-bundle init` - Detects your OS and sets up all tools automatically.
- `exa-bundle start mcp` - Injects local database secrets into the environment and starts the MCP AI Agent.
- `exa-bundle install personal` - Forces an update of the local database binary.
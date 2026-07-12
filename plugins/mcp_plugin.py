from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml
from mcp_use import MCPClient

DEFAULT_MCP_SERVERS: dict[str, dict[str, Any]] = {
    "playwright": {
        "command": "npx",
        "args": ["@playwright/mcp@latest"],
    },
    "playwright_headless": {
        "command": "npx",
        "args": ["@playwright/mcp@latest", "--headless"],
    },
}


class MCPServerPlugin:
    """Loads and manages multiple MCP server definitions."""

    def __init__(self, config_path: str | Path | None = None):
        self.config_path = Path(config_path) if config_path else self._default_config_path()
        self._servers: dict[str, dict[str, Any]] | None = None

    def _default_config_path(self) -> Path:
        return Path(__file__).resolve().parents[1] / "config" / "mcp_servers.yaml"

    def _normalize_servers(self, servers: Any) -> dict[str, dict[str, Any]]:
        normalized: dict[str, dict[str, Any]] = {}
        if not isinstance(servers, dict):
            return normalized

        for name, config in servers.items():
            if isinstance(name, str) and isinstance(config, dict):
                normalized[name] = copy.deepcopy(config)
        return normalized

    def load_servers(self) -> dict[str, dict[str, Any]]:
        if self._servers is not None:
            return copy.deepcopy(self._servers)

        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}

            servers = data.get("mcpServers", data.get("servers", {}))
            normalized = self._normalize_servers(servers)
            if normalized:
                self._servers = normalized
                return copy.deepcopy(self._servers)

        self._servers = copy.deepcopy(DEFAULT_MCP_SERVERS)
        return copy.deepcopy(self._servers)

    def save_servers(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as handle:
            yaml.safe_dump({"mcpServers": self.load_servers()}, handle, sort_keys=False)

    def register_server(self, name: str, server_config: dict[str, Any], persist: bool = True) -> None:
        servers = self.load_servers()
        servers[name] = copy.deepcopy(server_config)
        self._servers = servers
        if persist:
            self.save_servers()

    def build_client_config(self) -> dict[str, Any]:
        return {"mcpServers": self.load_servers()}

    def create_client(self) -> MCPClient:
        return MCPClient(config=self.build_client_config())

    async def create_session(self, server_name: str):
        client = self.create_client()
        session = await client.create_session(server_name)
        await session.initialize()
        return session

    async def close_session(self, session: Any) -> None:
        if hasattr(session, "disconnect"):
            await session.disconnect()
        elif hasattr(session, "close"):
            await session.close()


mcp_plugin = MCPServerPlugin()

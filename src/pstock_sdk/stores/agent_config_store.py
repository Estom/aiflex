"""Missing store file - agent config store"""
from typing import Any


class AgentConfig(dict):
    """Agent 配置"""
    def __init__(
        self,
        name: str,
        model: str,
        description: str | None = None,
        prompt: str | None = None,
        tools: list[str] | None = None,
        mcps: list[str] | None = None,
        skills: list[str] | None = None,
        children: list[str] | None = None,
        memories: list[dict] | None = None,
        config: dict | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            name=name,
            model=model,
            description=description,
            prompt=prompt,
            tools=tools or [],
            mcps=mcps or [],
            skills=skills or [],
            children=children or [],
            memories=memories or [],
            config=config or {},
            **kwargs,
        )


class InMemoryAgentConfigStore:
    """Agent 配置内存存储"""

    def __init__(self, initial: list[dict] | None = None):
        self._configs: dict[str, AgentConfig] = {}
        if initial:
            for cfg in initial:
                self.save(cfg, allow_overwrite=True)

    def list(self) -> list[AgentConfig]:
        return list(self._configs.values())

    def get(self, name: str) -> AgentConfig | None:
        return self._configs.get(name)

    def save(self, config: dict, options: dict | None = None) -> AgentConfig:
        agent_config = AgentConfig(**config)
        exists = agent_config["name"] in self._configs
        if exists and not (options or {}).get("allow_overwrite", False):
            raise ValueError(f"Agent {agent_config['name']} already exists.")

        self._configs[agent_config["name"]] = agent_config
        return agent_config

    def delete(self, name: str) -> None:
        self._configs.pop(name, None)


# Type aliases
AgentRuntimeOptions = dict
KnowledgeBaseAgentConfig = dict
KnowledgeBaseRetrievalConfig = dict

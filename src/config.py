"""Central config for the Market-Entry & Fundraising Diligence Pipeline."""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    model_name: str = os.getenv("MODEL_NAME", "claude-sonnet-4-6")
    max_tokens: int = int(os.getenv("MAX_TOKENS", "4000"))
    output_dir: str = "sample_output"
    mcp_server_url: str = os.getenv("MCP_SERVER_URL", "")

    def has_api_key(self) -> bool:
        return bool(self.anthropic_api_key)

    def validate(self) -> None:
        if not self.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key, "
                "or run with --offline to use the Germany seed fixture."
            )


config = Config()

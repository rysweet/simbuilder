"""
CLI commands for SimBuilder LLM integration.
"""

import asyncio
import json
import logging
from typing import Any

import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text

from src.scaffolding.config import get_settings

from .client import AzureOpenAIClient
from .client import ChatMessage
from .exceptions import LLMError
from .exceptions import PromptRenderError
from .prompts import list_prompts
from .prompts import render_prompt

app = typer.Typer(name="llm", help="LLM integration commands")
console = Console()
logger = logging.getLogger(__name__)


@app.command("chat")
def chat_command(
    prompt: str = typer.Option(..., "--prompt", help="Name of the prompt template to use"),
    variables: str = typer.Option(
        "{}",
        "--variables",
        help="JSON string with variables for the prompt (e.g., '{\"question\":\"hello\"}')",
    ),
    model: str | None = typer.Option(None, "--model", help="Model to use (overrides config)"),
    temperature: float = typer.Option(0.7, "--temperature", help="Sampling temperature"),
    max_tokens: int | None = typer.Option(None, "--max-tokens", help="Maximum tokens to generate"),
    stream: bool = typer.Option(False, "--stream", help="Stream the response"),
) -> None:
    """Send a chat message using a prompt template."""
    try:
        # Parse variables JSON
        try:
            prompt_vars = json.loads(variables)
        except json.JSONDecodeError as e:
            console.print(f"[red]Error:[/red] Invalid JSON in variables: {e}")
            raise typer.Exit(1)

        # Render the prompt
        try:
            rendered_prompt = render_prompt(prompt, prompt_vars)
        except PromptRenderError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

        # Create chat message
        messages = [ChatMessage(role="user", content=rendered_prompt)]

        # Send to LLM
        asyncio.run(
            _send_chat_completion(messages, model, temperature, max_tokens, stream)
        )

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


async def _send_chat_completion(
    messages: list[ChatMessage],
    model: str | None,
    temperature: float,
    max_tokens: int | None,
    stream: bool,
) -> None:
    """Send chat completion request."""
    client = AzureOpenAIClient()

    try:
        if stream:
            console.print("[dim]Streaming response...[/dim]")
            response = await client.create_chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    console.print(chunk.choices[0].delta.content, end="")
            console.print()  # Final newline
        else:
            response = await client.create_chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )

            if response.choices:
                content = response.choices[0].message.content
                console.print(f"[green]Response:[/green] {content}")
            else:
                console.print("[yellow]No response content received[/yellow]")

    except LLMError as e:
        console.print(f"[red]LLM Error:[/red] {e}")
        raise typer.Exit(1)
    finally:
        await client.close()


@app.command("embed")
def embed_command(
    text: str = typer.Option(..., "--text", help="Text to embed"),
    model: str | None = typer.Option(None, "--model", help="Model to use (overrides config)"),
    output_format: str = typer.Option("summary", "--format", help="Output format: summary, json, or values"),
) -> None:
    """Generate embeddings for text."""
    asyncio.run(_create_embeddings(text, model, output_format))


async def _create_embeddings(text: str, model: str | None, output_format: str) -> None:
    """Create embeddings for text."""
    client = AzureOpenAIClient()

    try:
        response = await client.create_embeddings(text, model=model)

        if output_format == "json":
            console.print(json.dumps(response.model_dump(), indent=2))
        elif output_format == "values":
            if response.data:
                values = response.data[0].embedding
                console.print(json.dumps(values))
            else:
                console.print("[yellow]No embedding data received[/yellow]")
        else:  # summary
            table = Table(title="Embedding Summary")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")

            table.add_row("Model", response.model or "Unknown")
            table.add_row("Usage (Tokens)", str(response.usage.total_tokens) if response.usage else "Unknown")
            if response.data:
                table.add_row("Embedding Dimensions", str(len(response.data[0].embedding)))
                table.add_row("Input Text Length", str(len(text)))

            console.print(table)

    except LLMError as e:
        console.print(f"[red]LLM Error:[/red] {e}")
        raise typer.Exit(1)
    finally:
        await client.close()


@app.command("info")
def info_command() -> None:
    """Show LLM configuration and status."""
    try:
        settings = get_settings()

        table = Table(title="LLM Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")

        # Mask the API key
        masked_key = "***" if settings.azure_openai_key else "[red]Not Set[/red]"

        table.add_row("Azure OpenAI Endpoint", settings.azure_openai_endpoint)
        table.add_row("API Version", settings.azure_openai_api_version)
        table.add_row("Chat Model", settings.azure_openai_model_chat)
        table.add_row("Reasoning Model", settings.azure_openai_model_reasoning)
        table.add_row("API Key", masked_key)

        console.print(table)

        # Show available prompts
        prompts = list_prompts()
        if prompts:
            prompt_table = Table(title="Available Prompts")
            prompt_table.add_column("Prompt Name", style="green")

            for prompt_name in prompts:
                prompt_table.add_row(prompt_name)

            console.print(prompt_table)
        else:
            console.print("[yellow]No prompt templates found[/yellow]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("check")
def check_command() -> None:
    """Check LLM configuration and connectivity."""
    try:
        settings = get_settings()

        # Check configuration
        config_status = _check_configuration(settings)

        # Check connectivity
        connectivity_status = asyncio.run(_check_connectivity())

        # Display results
        table = Table(title="LLM Health Check")
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Details", style="dim")

        for check, status, details in config_status + connectivity_status:
            status_text = Text("✓ PASS", style="green") if status else Text("✗ FAIL", style="red")
            table.add_row(check, status_text, details)

        console.print(table)

        # Exit with error code if any checks failed
        all_passed = all(status for _, status, _ in config_status + connectivity_status)
        if not all_passed:
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _check_configuration(settings: Any) -> list[tuple[str, bool, str]]:
    """Check configuration settings."""
    checks = []

    # Check required settings
    checks.append((
        "Azure OpenAI Endpoint",
        bool(settings.azure_openai_endpoint),
        settings.azure_openai_endpoint if settings.azure_openai_endpoint else "Not configured"
    ))

    checks.append((
        "Azure OpenAI API Key",
        bool(settings.azure_openai_key),
        "Configured" if settings.azure_openai_key else "Not configured"
    ))

    checks.append((
        "API Version",
        bool(settings.azure_openai_api_version),
        settings.azure_openai_api_version if settings.azure_openai_api_version else "Not configured"
    ))

    checks.append((
        "Chat Model",
        bool(settings.azure_openai_model_chat),
        settings.azure_openai_model_chat if settings.azure_openai_model_chat else "Not configured"
    ))

    return checks


async def _check_connectivity() -> list[tuple[str, bool, str]]:
    """Check connectivity to Azure OpenAI."""
    checks = []
    client = AzureOpenAIClient()

    try:
        health_info = await client.check_health()

        if health_info["status"] == "healthy":
            checks.append((
                "Azure OpenAI Connectivity",
                True,
                f"Connected (Response ID: {health_info.get('response_id', 'N/A')})"
            ))
        else:
            checks.append((
                "Azure OpenAI Connectivity",
                False,
                f"Failed: {health_info.get('error', 'Unknown error')}"
            ))

    except Exception as e:
        checks.append((
            "Azure OpenAI Connectivity",
            False,
            f"Connection failed: {str(e)}"
        ))
    finally:
        await client.close()

    return checks


if __name__ == "__main__":
    app()

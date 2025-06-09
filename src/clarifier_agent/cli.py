import typer
from .agent import ClarifierAgent
from .models import ClarifyRequest

app = typer.Typer(name="clarifier-cli")

@app.command()
def clarify(spec: str = typer.Argument(..., help="Spec string to clarify")):
    """Clarifies the given spec using ClarifierAgent (stub)."""
    agent = ClarifierAgent()
    request = ClarifyRequest(spec=spec)
    result = agent.clarify(request)
    typer.echo(result.dict())

if __name__ == "__main__":
    app()
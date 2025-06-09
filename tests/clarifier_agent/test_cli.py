import pytest
from typer.testing import CliRunner
from src.clarifier_agent.cli import app

runner = CliRunner()

def test_clarifier_cli_smoke():
    result = runner.invoke(app, ["dummy spec"])
    print("CLI OUTPUT:", result.output)
    print("CLI ERR:", result.stderr)
    assert result.exit_code == 0
    assert "clarification placeholder" in result.output
    assert "ClarifierAgent stub called" in result.output
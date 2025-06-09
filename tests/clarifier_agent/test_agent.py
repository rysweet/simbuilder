import pytest
from src.clarifier_agent.agent import ClarifierAgent
from src.clarifier_agent.models import ClarifyRequest, ClarifyResponse

def test_clarifier_agent_stub():
    agent = ClarifierAgent()
    req = ClarifyRequest(spec="Example spec")
    resp = agent.clarify(req)
    assert isinstance(resp, ClarifyResponse)
    assert resp.clarified == "clarification placeholder"
    assert "ClarifierAgent stub called" in (resp.metadata or {}).get("info", "")
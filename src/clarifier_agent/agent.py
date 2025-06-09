from .models import ClarifyRequest, ClarifyResponse

class ClarifierAgent:
    def clarify(self, request: ClarifyRequest) -> ClarifyResponse:
        """Stub clarify method: echo metadata only."""
        return ClarifyResponse(
            clarified="clarification placeholder",
            metadata={"info": "ClarifierAgent stub called"}
        )
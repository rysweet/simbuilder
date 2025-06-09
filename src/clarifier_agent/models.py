from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

class ClarifyRequest(BaseModel):
    spec: str = Field(..., description="Specification text to clarify")
    metadata: Optional[Dict[str, Any]] = None

class ClarifyResponse(BaseModel):
    clarified: str = Field(..., description="Clarified specification output")
    metadata: Optional[Dict[str, Any]] = None
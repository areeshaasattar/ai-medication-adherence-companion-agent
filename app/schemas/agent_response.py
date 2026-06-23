from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class AgentResponseType(str, Enum):
    ADHERENCE_ANALYSIS = "adherence_analysis"
    SIDE_EFFECT_GUIDANCE = "side_effect_guidance"
    MEDICATION_EDUCATION = "medication_education"
    GENERAL = "general"

class AgentResponse(BaseModel):
    message: str = Field(..., description="The main response message from the agent.")
    response_type: AgentResponseType = Field(..., description="The category of the response.")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="The agent's confidence in its response.")
    requires_medical_attention: bool = Field(False, description="Whether the user should seek immediate medical help.")
    follow_up_questions: List[str] = Field(default_factory=list, description="Suggested questions for the user to ask next.")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Your weekly adherence is 85%. You missed one dose of Metformin on Tuesday.",
                "response_type": "adherence_analysis",
                "confidence_score": 0.95,
                "requires_medical_attention": False,
                "follow_up_questions": ["Why did you miss your dose on Tuesday?", "Would you like a reminder for your next dose?"]
            }
        }

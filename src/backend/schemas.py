from pydantic import BaseModel, Field


class ScoreRequest(BaseModel):
    """Field names match the dataset columns exactly."""
    amount: float = Field(ge=0)
    transaction_hour: int = Field(ge=0, le=23)
    merchant_category: str
    foreign_transaction: bool = False
    location_mismatch: bool = False
    device_trust_score: int = Field(ge=0, le=100)
    velocity_last_24h: int = Field(ge=0)
    cardholder_age: int = Field(ge=0, le=120)


class Part(BaseModel):
    label: str
    points: float


class Driver(BaseModel):
    feature: str
    impact: int


class ScoreResponse(BaseModel):
    score: int
    probability: int
    tier: str
    action: str
    parts: list[Part]
    drivers: list[Driver] = []


class DecisionRequest(BaseModel):
    case_id: str
    decision: str  # Confirmed fraud | False positive | Escalated
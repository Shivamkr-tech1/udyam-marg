from pydantic import BaseModel, Field, model_validator
from typing import Optional


class AnalyzeRequest(BaseModel):
    location: Optional[str] = Field(default='Maner, Patna, Bihar')
    lat: Optional[float] = None
    lon: Optional[float] = None
    margin_capital: float = Field(gt=0, examples=[100000])
    business_category: str = Field(min_length=2, examples=['Dairy'])

    @model_validator(mode='after')
    def validate_coordinates(self):
        if (self.lat is None) != (self.lon is None):
            raise ValueError('Provide both lat and lon, or neither.')
        return self

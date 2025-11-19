"""
General DTOs for common TVmaze API response constructs.
"""

from pydantic import BaseModel, HttpUrl


class TVmazeCountryDTO(BaseModel):
    name: str


class TVmazeNetworkDTO(BaseModel):
    name: str
    country: TVmazeCountryDTO | None


class TVmazeWebChannelDTO(BaseModel):
    name: str
    country: TVmazeCountryDTO | None


class TVmazeImageDTO(BaseModel):
    medium: HttpUrl | None

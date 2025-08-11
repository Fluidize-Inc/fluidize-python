"""

This module defines the structure of parameters.json

"""

from typing import Optional

from pydantic import BaseModel


class ParameterOption(BaseModel):
    value: str
    label: str


class Parameter(BaseModel):
    value: str
    description: str
    # type specifies the type of the value, e.g. "text", "dropdown"
    type: str
    label: str
    name: str
    latex: Optional[str] = None
    location: Optional[list[str]] = None
    options: Optional[list[ParameterOption]] = None
    scope: Optional[str] = None

from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

FEATURES = ["Type", "Air temperature [K]", "Process temperature [K]",
            "Rotational speed [rpm]", "Torque [Nm]", "Tool wear [min]"]
Number = Annotated[float, Field(ge=0, allow_inf_nan=False)]

class MachineRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=False, loc_by_alias=True)
    machine_type: Literal["L", "M", "H"] = Field(alias="Type")
    air_temperature: Number = Field(alias="Air temperature [K]")
    process_temperature: Number = Field(alias="Process temperature [K]")
    rotational_speed: Number = Field(alias="Rotational speed [rpm]")
    torque: Number = Field(alias="Torque [Nm]")
    tool_wear: Number = Field(alias="Tool wear [min]")

    @field_validator("air_temperature", "process_temperature", "rotational_speed", "torque", "tool_wear", mode="before")
    @classmethod
    def numeric_only(cls, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Se requiere un número finito, no texto ni booleano")
        return value

class BatchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    records: list[MachineRecord] = Field(min_length=1)

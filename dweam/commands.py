from typing import Literal, Any
from pydantic import BaseModel

class SchemaCommand(BaseModel):
    cmd: Literal["schema"] = "schema"

class StopCommand(BaseModel):
    cmd: Literal["stop"] = "stop"

class UpdateParamsCommand(BaseModel):
    cmd: Literal["update"] = "update"
    data: dict[str, Any]

class OfferData(BaseModel):
    sdp: str
    type: str

class HandleOfferCommand(BaseModel):
    cmd: Literal["handle_offer"] = "handle_offer"
    data: OfferData

Command = SchemaCommand | StopCommand | UpdateParamsCommand | HandleOfferCommand

class SuccessResponse(BaseModel):
    status: Literal["success"] = "success"
    data: Any | None = None

class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    error: str

Response = SuccessResponse | ErrorResponse 
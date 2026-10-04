from pydantic import BaseModel


class CommuneResponse(BaseModel):
    commune_code: str
    commune_name: str
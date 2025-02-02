from pydantic import BaseModel


class Language(BaseModel):

    code: str
    name: str
    native_name: str
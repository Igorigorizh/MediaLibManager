import inspect
from typing import Dict, Type, TypeVar, Protocol, Generic, NewType

from fastapi import Depends, FastAPI, File, Form
from pydantic import BaseModel, validator, BaseSettings, Json

app = FastAPI()

StringId = NewType('StringId', str)


def as_form(cls: Type[BaseModel]):
    """
    Adds an as_form class method to decorated models. The as_form class method
    can be used with FastAPI endpoints
    """
    new_params = [
        inspect.Parameter(
            field.alias,
            inspect.Parameter.POSITIONAL_ONLY,
            default=(Form(field.default) if not field.required else Form(...)),
        )
        for field in cls.__fields__.values()
    ]

    async def _as_form(**data):
        return cls(**data)

    sig = inspect.signature(_as_form)
    sig = sig.replace(parameters=new_params)
    _as_form.__signature__ = sig
    setattr(cls, "as_form", _as_form)
    return cls


@as_form
class Item(BaseModel):
    name: str
    another: str
    opts: Json[Dict[str, int]] = '{}'


@app.post("/test")
async def endpoint(item: Item = Depends(Item.as_form)):
    return item.dict()


if __name__ == "__main__":
    import json
    import os


    from fastapi.testclient import TestClient

    tc = TestClient(app)

    item = {"name": "vivalldi", "another": "mause"}

    data = bytearray(os.urandom(1))
    files = {"data": ("data", data, "text/csv")}

    r = tc.post("/test", data=item, files=files)
    assert r.status_code == 200, r.text
    assert r.json() == {"name": "vivalldi", "another": "mause", "opts": {}}

    files["opts"] = (None, json.dumps({"a": 2}), "application/json")
    r = tc.post("/test", data=item, files=files)
    assert r.status_code == 200
    assert r.json() == {"name": "vivalldi", "another": "mause", "opts": {"a": 2}}

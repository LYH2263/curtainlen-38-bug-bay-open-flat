from fastapi import APIRouter
from pydantic import BaseModel
from app.repositories import settings_repo
router = APIRouter()
class SettingValue(BaseModel):
    value: str
@router.get("/settings")
def settings(): return settings_repo.get_all()
@router.put("/settings/{key}")
def set_setting(key: str, body: SettingValue):
    settings_repo.set_value(key, body.value)
    return {key: body.value}

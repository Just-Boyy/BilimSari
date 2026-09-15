from pydantic import BaseModel, ConfigDict


class TelegramAuthRequest(BaseModel):
    init_data: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    first_name: str | None
    lang: str
    grade: int | None
    role: str
    streak: int
    total_xp: int


class TelegramAuthResponse(BaseModel):
    token: str
    user: UserOut

from pydantic import BaseModel


class AdminStatsResponse(BaseModel):
    total_users: int
    total_messages: int
    messages_today: int
    active_users_7d: int
    new_signups_7d: int

# backend/app/db/base_class.py (updated)
from app.db.base import Base
from app.models.user import User
from app.models.oauth_token import OAuthToken
from app.models.email import Email
from app.models.agent import AgentTask, ActionLog
from app.models.user_profile import UserPreference
from app.models.agent_thought import AgentThought
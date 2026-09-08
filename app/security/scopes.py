from enum import StrEnum


class APIKeyScope(StrEnum):
    API_KEYS_READ = "api-keys:read"
    API_KEYS_WRITE = "api-keys:write"


ALL_API_KEY_SCOPES = tuple(APIKeyScope)

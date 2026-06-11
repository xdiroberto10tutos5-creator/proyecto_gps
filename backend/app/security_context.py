from contextvars import ContextVar

from fastapi import HTTPException

_access_token = ContextVar("access_token", default=None)
_auth_user = ContextVar("auth_user", default=None)


def set_security_context(access_token, user):
    return _access_token.set(access_token), _auth_user.set(user)


def reset_security_context(tokens):
    access_token_token, auth_user_token = tokens
    _access_token.reset(access_token_token)
    _auth_user.reset(auth_user_token)


def get_access_token():
    return _access_token.get()


def get_auth_user():
    user = _auth_user.get()
    if not user:
        raise HTTPException(status_code=401, detail="Sesión no autenticada")
    return user

# Story 2.4: API Key Management (List, Revoke, Regenerate)

Status: ready-for-dev

## Story

As an authenticated developer,
I want to list, revoke, and regenerate my API keys,
so that I can maintain security control over my account access.

## Acceptance Criteria

1. **Given** GET /api/v1/keys with a valid JWT, **When** called, **Then** HTTP 200 is returned with `{"items": [...], "total": N}` — each item includes `id`, `name`, `created_at`, `is_active`; `key_hash` is never returned.

2. **Given** DELETE /api/v1/keys/{key_id} with valid JWT and the key belonging to the authenticated user, **When** called, **Then** HTTP 200 is returned and `is_active` is set to `false`; the key no longer works for authentication.

3. **Given** DELETE /api/v1/keys/{key_id} with a key belonging to a different user, **When** called, **Then** HTTP 403 is returned with error code `FORBIDDEN`.

4. **Given** POST /api/v1/keys/{key_id}/regenerate with valid JWT, **When** called, **Then** the old key is deactivated, a new key is created, and the response returns the new plaintext key once.

5. **Given** a revoked key used in the `Authorization` header for a scraping request, **When** called, **Then** HTTP 401 is returned with error code `INVALID_API_KEY`.

## Tasks / Subtasks

- [ ] Implement list keys endpoint (AC: 1)
  - [ ] `app/auth/service.py`: `list_api_keys(db, user_id)` → list of ApiKey
  - [ ] `app/api/v1/keys.py`: `GET /api/v1/keys` — NEVER return `key_hash`

- [ ] Implement revoke key endpoint (AC: 2, 3)
  - [ ] `app/auth/service.py`: `revoke_api_key(db, key_id, user_id)` → check ownership, set is_active=False
  - [ ] `app/api/v1/keys.py`: `DELETE /api/v1/keys/{key_id}`

- [ ] Implement regenerate key endpoint (AC: 4)
  - [ ] `app/auth/service.py`: `regenerate_api_key(db, key_id, user_id)` → deactivate old, create new
  - [ ] `app/api/v1/keys.py`: `POST /api/v1/keys/{key_id}/regenerate`

- [ ] Viết tests (AC: 1, 2, 3, 4, 5)

## Dev Notes

### `app/auth/service.py` — Management functions

```python
async def list_api_keys(db: AsyncSession, user_id: uuid.UUID) -> list[ApiKey]:
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.user_id == user_id)
        .order_by(ApiKey.created_at.desc())
    )
    return list(result.scalars().all())


async def revoke_api_key(db: AsyncSession, key_id: uuid.UUID, user_id: uuid.UUID) -> ApiKey:
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id))
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise NotFoundError()
    if api_key.user_id != user_id:
        raise ForbiddenError()

    api_key.is_active = False
    await db.commit()
    return api_key


async def regenerate_api_key(
    db: AsyncSession, key_id: uuid.UUID, user_id: uuid.UUID
) -> tuple[ApiKey, str]:
    """Deactivate old key, create new key. Returns (new_key, plaintext)."""
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id))
    old_key = result.scalar_one_or_none()

    if not old_key:
        raise NotFoundError()
    if old_key.user_id != user_id:
        raise ForbiddenError()

    async with db.begin():
        old_key.is_active = False
        new_key, plaintext = await create_api_key(db, user_id, old_key.name)

    return new_key, plaintext
```

### `app/auth/schemas.py` — List schemas

```python
class ApiKeyListItem(BaseModel):
    id: uuid.UUID
    name: str | None
    created_at: datetime
    is_active: bool
    # NEVER include key_hash!
    model_config = {"from_attributes": True}

class ApiKeyListResponse(BaseModel):
    items: list[ApiKeyListItem]
    total: int
```

### `app/api/v1/keys.py` — Complete implementation

```python
@router.get("", response_model=schemas.ApiKeyListResponse)
async def list_keys(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    keys = await service.list_api_keys(db, user.id)
    return {"items": keys, "total": len(keys)}


@router.delete("/{key_id}", status_code=200)
async def revoke_key(
    key_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await service.revoke_api_key(db, key_id, user.id)
    return {"message": "Key revoked successfully"}


@router.post("/{key_id}/regenerate", status_code=201)
async def regenerate_key(
    key_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    new_key, plaintext = await service.regenerate_api_key(db, key_id, user.id)
    return {
        "id": new_key.id,
        "key": plaintext,  # ONLY time plaintext is returned
        "created_at": new_key.created_at,
    }
```

### Response Field Security

`key_hash` PHẢI KHÔNG BAO GIỜ được trả về trong bất kỳ response nào:
- List endpoint: chỉ `id`, `name`, `created_at`, `is_active`
- Create/Regenerate: chỉ `id`, `key` (plaintext, once), `created_at`

Dùng Pydantic schema để enforce — nếu schema không include `key_hash`, nó sẽ không được serialize.

### Revoked Key → 401 (AC: 5)

Story 2.5 sẽ implement API key authentication middleware cho scraping endpoints. Khi revoked key được dùng, `is_active=False` check trong auth service sẽ raise `InvalidApiKeyError`. Story này chỉ cần test revoke functionality — AC 5 được verified trong Story 2.5.

### References

- [Source: epics.md#Story-2.4] — acceptance criteria
- [Source: architecture.md#Format-Patterns] — list response format `{"items": [...], "total": N}`
- [Source: architecture.md#Enforcement-Guidelines] — key_hash NEVER returned

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**UPDATE:**
- `backend/app/auth/service.py` — add list, revoke, regenerate functions
- `backend/app/auth/schemas.py` — add list schemas
- `backend/app/api/v1/keys.py` — add GET, DELETE, POST regenerate endpoints

**NEW:**
- `backend/tests/api/test_key_management.py`

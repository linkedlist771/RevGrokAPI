from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from tortoise import Model, fields
from tortoise.expressions import Q

from revgrokapi.models.cookie_models import Cookie, CookieType


# Pydantic schemas for API request/response models
class CookieBase(BaseModel):
    cookie: str
    cookie_type: CookieType
    account: str


class CookieCreateRequest(CookieBase):
    pass


class CookieUpdateRequest(BaseModel):
    cookie: Optional[str] = None
    cookie_type: Optional[CookieType] = None
    account: Optional[str] = None


class CookieResponse(CookieBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# FastAPI router for RESTful endpoints
router = APIRouter()


@router.post("/", response_model=CookieResponse, status_code=status.HTTP_201_CREATED)
async def create_cookie(cookie_in: CookieCreateRequest):
    try:
        cookie = await Cookie.create_item(**cookie_in.model_dump())
        return cookie
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not create cookie: {str(e)}",
        )


@router.get("/{cookie_id}", response_model=CookieResponse)
async def get_cookie(cookie_id: int):
    cookie = await Cookie.get_by_id(cookie_id)
    if not cookie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cookie with ID {cookie_id} not found",
        )
    return cookie


@router.get("/", response_model=List[CookieResponse])
async def list_cookies(
    skip: int = 0,
    limit: int = 100,
    cookie_type: Optional[CookieType] = None,
    search: Optional[str] = None,
):
    filters = {}
    if cookie_type:
        filters["cookie_type"] = cookie_type

    if search:
        cookies = await Cookie.search_items(
            search_fields=["cookie", "account"],
            search_term=search,
            skip=skip,
            limit=limit,
        )
    else:
        cookies = await Cookie.get_multi(skip=skip, limit=limit, **filters)

    return cookies


@router.put("/{cookie_id}", response_model=CookieResponse)
async def update_cookie(cookie_id: int, cookie_in: CookieUpdateRequest):
    cookie = await Cookie.get_by_id(cookie_id)
    if not cookie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cookie with ID {cookie_id} not found",
        )

    update_data = {k: v for k, v in cookie_in.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No valid fields to update"
        )

    updated_cookie = await cookie.update_item(**update_data)
    return updated_cookie


@router.delete("/{cookie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cookie(cookie_id: int):
    deleted = await Cookie.delete_by_id(cookie_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cookie with ID {cookie_id} not found",
        )

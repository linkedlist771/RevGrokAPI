from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from tortoise import Model, fields
from tortoise.expressions import Q

from revgrokapi.models.cookie_models import Cookie, CookieType, CookieQueries, QueryCategory


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


class CookieTotalCountResponse(BaseModel):
    total_count: int
    model_counts: Dict[str, int]


class CookieTypeModelCountResponse(BaseModel):
    cookie_type: str
    total_count: int
    model_counts: Dict[str, int]


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


@router.get("/stats/total", response_model=CookieTotalCountResponse)
async def get_total_cookie_stats():
    """
    获取所有cookie的总数和各模型的可用量
    """
    # 获取所有cookie的总数
    total_count = await Cookie.get_count()
    
    # 获取各模型的可用量
    model_counts = {}
    actual_weights = {}  # 添加一个字典来存储实际的权重值
    
    for category in QueryCategory:
        # 获取该模型下权重大于0的cookie数量
        cookies_with_weight = await CookieQueries.filter(
            category=category,
            queries_weight__gt=0
        ).count()
        
        # 添加详细日志，查看每个类别的cookie数量和权重
        all_records = await CookieQueries.filter(category=category).all()
        weights_list = []
        for record in all_records:
            cookie = await record.cookie_ref
            weights_list.append(record.queries_weight)
            print(f"Debug - Category {category}: Cookie {cookie.id} has weight {record.queries_weight}")
        
        print(f"Debug - Category {category}: All weights: {weights_list}")
        model_counts[category.value] = cookies_with_weight
        actual_weights[category.value] = weights_list  # 存储实际的权重值
    
    print(f"Debug - Total stats: {total_count} cookies, model counts: {model_counts}")
    print(f"Debug - Actual weights: {actual_weights}")
    
    # 返回一个包含实际权重的响应，用于调试
    response = {
        "total_count": total_count,
        "model_counts": model_counts,
        "actual_weights": actual_weights  # 这个字段不会在响应中显示，因为它不在响应模型中
    }
    
    return response


@router.get("/stats/by-type", response_model=List[CookieTypeModelCountResponse])
async def get_cookie_stats_by_type():
    """
    获取按cookie类型分组的各模型可用量
    """
    result = []
    
    # 遍历所有cookie类型
    for cookie_type in CookieType:
        # 获取该类型的cookie总数
        type_count = await Cookie.get_count(cookie_type=cookie_type)
        
        # 获取该类型下各模型的可用量
        model_counts = {}
        for category in QueryCategory:
            # 获取该类型和模型下权重大于0的cookie数量
            cookies_with_weight = await CookieQueries.filter(
                cookie_ref__cookie_type=cookie_type,
                category=category,
                queries_weight__gt=0
            ).count()
            model_counts[category.value] = cookies_with_weight
        
        result.append({
            "cookie_type": cookie_type.value,
            "total_count": type_count,
            "model_counts": model_counts
        })
    
    return result

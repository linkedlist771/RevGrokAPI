"""
revgrokapi/models/cookie_models.py

This file defines the tortoise based models for the cookie to restore.
"""
from revgrokapi.models.base import CRUDBase
from tortoise import fields
from enum import Enum


from revgrokapi.models.base import CRUDBase
from tortoise import fields
from enum import Enum


class CookieType(str, Enum):  # 注意这里继承 str
    PLUS = "plus"
    BASIC = "basic"
    TEST = "test"



class Cookie(CRUDBase):
    cookie = fields.CharField(max_length=4000, unique=True)
    cookie_type = fields.CharEnumField(enum_type=CookieType, max_length=50)
    account = fields.CharField(max_length=254)
    # cookie = await Cookie.create_item(
    #     cookie="your_cookie_string",
    #     cookie_type=CookieType.PLUS,  # 使用枚举值
    #     account="account_name"
    # )
    #
    # # 查询指定类型的 cookie
    # plus_cookies = await Cookie.get_multi(cookie_type=CookieType.PLUS)

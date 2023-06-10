import os

from typing import List
from fastapi import APIRouter, UploadFile
from starlette.responses import JSONResponse

from dependencies import get_instagram_photos, post_photos_to_profile, apply_function_in_parallel

instagram_router = APIRouter()


@instagram_router.get("/getPhotos/")
async def get_photos(username: str, max_count: int = 3):

    result = apply_function_in_parallel(get_instagram_photos, username, max_count)

    return JSONResponse(content={'urls': result})


@instagram_router.post("/postPhotos")
async def post_photos(photos: List[UploadFile], caption: str):

    result = apply_function_in_parallel(post_photos_to_profile, photos, caption)

    return JSONResponse(content={'postURL': result})


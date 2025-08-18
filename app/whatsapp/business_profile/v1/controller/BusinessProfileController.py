from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile
from dependency_injector.wiring import Provide, inject

from app.core.security.JwtUtility import get_current_user
from app.core.config.container import Container
from app.core.exceptions.custom_exceptions.ClientExceptionHandler import ClientException
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.exceptions.GlobalException import GlobalException
from app.core.exceptions.custom_exceptions.UnAuthorizedException import UnAuthorizedException
from app.utils.generate_responses import generate_responses
from app.whatsapp.business_profile.v1.use_case.GetBusinessProfile import (
    GetBusinessProfile,
)
from app.whatsapp.business_profile.v1.use_case.UpdateBusinessProfile import (
    UpdateBusinessProfile,
)
from app.core.config.container import Container
from app.core.exceptions.GlobalException import GlobalException

router = APIRouter()

@router.get("",
            responses={**generate_responses({UnAuthorizedException,
                                                DataBaseException,
                                                ClientException})},
)
@inject
async def get_business_profile(
    fields: str = None,
    get_business_profile: GetBusinessProfile = Depends(
        Provide[Container.business_profile_get_business_profile]
    ),
    token: dict = Depends(get_current_user),
):
    try:
        return await get_business_profile.execute(token["userId"], fields)
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e


@router.put(
    "",
    responses={**generate_responses({UnAuthorizedException,
                                    DataBaseException, 
                                    ClientException})},
)
@inject
async def update_business_profile(
    image: Optional[UploadFile] = File(None, description="JPEG business profile image"),
    description: Optional[str] = Form(None),
    about: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    websites: Optional[str] = Form(None, description="Comma-separated website URLs"),
    vertical: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    updater: UpdateBusinessProfile = Depends(Provide[Container.business_profile_update_business_profile]),
    token: dict = Depends(get_current_user),
):
    form_data = {
        "description": description,
        "about": about,
        "email": email,
        "vertical": vertical,
        "address": address,
    }
    if websites:
        form_data["websites"] = [w.strip() for w in websites.split(",") if w.strip()]
    try:
        return await updater.execute(user_id=token["userId"], image=image, data=form_data)
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e
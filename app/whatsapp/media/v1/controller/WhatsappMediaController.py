from fastapi import APIRouter, Depends, File, UploadFile
from dependency_injector.wiring import Provide, inject

from app.core.config.container import Container
from app.core.exceptions.custom_exceptions.ClientExceptionHandler import ClientException
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.exceptions.GlobalException import GlobalException
from app.core.security.JwtUtility import get_current_user
from app.core.exceptions.custom_exceptions.UnAuthorizedException import UnAuthorizedException
from app.utils.generate_responses import generate_responses
from app.whatsapp.media.v1.usecase import UploadSession
from app.whatsapp.media.v1.usecase.CreaeSession import CreateSession
from app.whatsapp.media.v1.usecase.DeleteMedia import DeleteMedia
from app.whatsapp.media.v1.usecase.DownloadMedia import DownloadMedia
from app.whatsapp.media.v1.usecase.RetrieveMediaUrl import RetrieveMediaUrl
from app.whatsapp.media.v1.usecase.UploadMedia import UploadMedia
from app.core.logs.logger import get_logger

logger = get_logger("WhatsappMediaController")
router = APIRouter()

@router.get(
    "/download-media",
    responses={
        **generate_responses(
            [UnAuthorizedException, DataBaseException, ClientException]
        )
    },
)
@inject
async def download_media(
    media_url: str,
    download_media: DownloadMedia = Depends(
        Provide[Container.whatsapp_media_download_media]
    ),
    token: dict = Depends(get_current_user),
):
    try:
        return await download_media.execute(token["userId"], media_url)
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e

@router.get(
    "/retrieve-media-url/{media_id}",
    responses={
        **generate_responses(
            [UnAuthorizedException, DataBaseException, ClientException]
        )
    },
)
@inject
async def retrieve_media_url(
    media_id: str,
    retrieve_media_url: RetrieveMediaUrl = Depends(
        Provide[Container.whatsapp_media_retrieve_media_url]
    ),
    token: dict = Depends(get_current_user),
):
    try:
        return await retrieve_media_url.execute(token["userId"], media_id)
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e

@router.post(
    "/upload-media",
    responses={
        **generate_responses(
            [UnAuthorizedException, DataBaseException, ClientException]
        )
    },
)
@inject
async def upload_media(
    file: UploadFile = File(...),
    whatsapp_media_upload_media: UploadMedia = Depends(
        Provide[Container.whatsapp_media_upload_media]
    ),
    token: dict = Depends(get_current_user),
):
    try:
        response = await whatsapp_media_upload_media.execute(token["userId"], file)
        return response
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e

@router.post(
    "/create-upload-session",
    responses={
        **generate_responses(
            [UnAuthorizedException, DataBaseException, ClientException]
        )
    },
)
@inject
async def create_upload_session(
    file_length: int,
    file_type: str,
    file_name: str,
    create_upload_session: CreateSession = Depends(
        Provide[Container.whatsapp_media_create_upload_session]
    ),
    token: dict = Depends(get_current_user),
):
    try:
        return await create_upload_session.execute(
            token["userId"], file_length, file_type, file_name
        )
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e

@router.post(
    "/upload-file-data/{session_id}",
    responses={
        **generate_responses(
            [UnAuthorizedException, DataBaseException, ClientException]
        )
    },
)
@inject
async def upload_file_data(
    session_id: str,
    file: UploadFile | str = File(...),
    file_offset: int = 0,
    upload_file_data: UploadSession = Depends(
        Provide[Container.whatsapp_media_upload_file_data]
    ),
    token: dict = Depends(get_current_user),
):
    try:
        return await upload_file_data.execute(
            token["userId"], session_id, file, file_offset
        )
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e
    
@router.post(
    "/upload-template-media",
    responses={
        **generate_responses(
            [UnAuthorizedException, DataBaseException, ClientException]
        )
    },
)
@inject
async def upload_template_media(

    file: UploadFile | str = File(...),
    create_upload_session: CreateSession = Depends(
        Provide[Container.whatsapp_media_create_upload_session]
    ),
    upload_file_data: UploadSession = Depends(
        Provide[Container.whatsapp_media_upload_file_data]
    ),
    token: dict = Depends(get_current_user),
):
    try:
        file_length = file.file._file.tell() if hasattr(file.file, '_file') else file.file.tell()
        file_type = file.content_type
        file_name = file.filename
        session = await create_upload_session.execute(
            token["userId"], file_length, file_type, file_name
        )
        logger.info(f"Session created: {session}")
        response = await upload_file_data.execute(
            token["userId"], session["data"]["id"], file, 0
        )
        logger.info(f"File uploaded successfully: {response}")

        return response
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e
        

@router.delete(
    "/delete-media/{media_id}",
    responses={
        **generate_responses(
            [UnAuthorizedException, DataBaseException, ClientException]
        )
    },
)
@inject
async def delete_media(
    media_id: str,
    delete_media: DeleteMedia = Depends(Provide[Container.whatsapp_media_delete_media]),
    token: dict = Depends(get_current_user),
):
    try:
        return await delete_media.execute(token["userId"], media_id)
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e
    

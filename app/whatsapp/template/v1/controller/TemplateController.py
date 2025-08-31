from fastapi import APIRouter, Path, Query
from fastapi.params import Depends
from app.core.security.JwtUtility import get_current_user
from app.core.exceptions.custom_exceptions.ClientExceptionHandler import ClientException
from app.core.exceptions.custom_exceptions.DataBaseException import DataBaseException
from app.core.exceptions.GlobalException import GlobalException
from app.core.exceptions.custom_exceptions.UnAuthorizedException import UnAuthorizedException
from app.utils.enums.SortBy import SortByCreatedAt
from app.utils.generate_responses import generate_responses
from app.whatsapp.template.models.schema.template_body.DynamicTemplateRequest import DynamicTemplateRequest
from app.whatsapp.template.v1.usecase.CreateTemplate import CreateTemplate
from app.whatsapp.template.v1.usecase.DeleteTemplate import DeleteTemplate
from dependency_injector.wiring import Provide, inject

from app.core.config.container import Container
from app.whatsapp.template.v1.usecase.GetTemplates import GetTemplates

router = APIRouter()

@router.get(
    "/",
    responses={
        **generate_responses(
            [UnAuthorizedException, DataBaseException, ClientException]
        )
    },
)
@inject
async def get_templates(
    page: int = Query(1, gt=0, description="The page number to fetch."),
    limit: int = Query(10, gt=0, description="The maximum number of templates to return per page."),
    sort_by: SortByCreatedAt = Query(SortByCreatedAt.DESC, description="The field to sort by."),
    search_name: str = Query("", description="The name to search for."),
    get_templates_use_case: GetTemplates = Depends(
        Provide[Container.whatsapp_template_get_templates]
    ),
    token: dict = Depends(get_current_user),
):
    try:
        user_id = token["userId"]
        response = await get_templates_use_case.execute(
            user_id=user_id,  page=page, limit=limit, sort_by=sort_by, search_name=search_name
        )
        return response
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e


@router.post(
    "/",
    responses={
        **generate_responses(
            [UnAuthorizedException, DataBaseException, ClientException]
        )
    },
)
@inject
async def create_template(
    create_template_request: DynamicTemplateRequest,
    create_template_use_case: CreateTemplate = Depends(
        Provide[Container.whatsapp_template_create_template]
    ),
    token: dict = Depends(get_current_user),
):

    try:
        user_id = token["userId"]
        response = await create_template_use_case.execute(
            user_id, create_template_request
        )
        return response
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e


@router.delete(
    "/{name}",
    responses={
        **generate_responses(
            [UnAuthorizedException, DataBaseException, ClientException]
        )
    },
)
@inject
async def delete_template(
    name: str = Path(..., description="The name of the template to delete."),
    template_id: str = Query(None, description="The unique template ID for deletion by ID."),
    delete_template_use_case: DeleteTemplate = Depends(
        Provide[Container.whatsapp_template_delete_template]
    ),
    token: dict = Depends(get_current_user),
):
    """
    Deletes a WhatsApp message template.

    Deleting by name:
        - If no template_id is provided, all templates with the matching name (including different languages)
        will be deleted.
    Deleting by ID:
        - If template_id is provided, only the template with the matching template_id and name will be deleted.

    :param name: The name of the template to delete.
    :param template_id: (Optional) The unique template ID for deletion by ID.
    :return: JSON response from the API containing the success status.
    """
    try:
        user_id = token["userId"]
        return await delete_template_use_case.execute(user_id, name, template_id)
    except GlobalException as e:
        raise e
    except Exception as e:
        raise e



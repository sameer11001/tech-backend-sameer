from fastapi import APIRouter, Depends, Query, Request, HTTPException, status
from fastapi.responses import JSONResponse, PlainTextResponse
from dependency_injector.wiring import Provide, inject
from app.core.config.container import Container
from app.core.config.settings import settings
from app.real_time.webhook.services.WebhookDispatcher import WebhookDispatcher

router = APIRouter()

@router.get("", status_code=status.HTTP_200_OK)
async def verify_webhook(
    mode: str = Query(..., alias="hub.mode"),
    verify_token: str = Query(..., alias="hub.verify_token"),
    challenge: str = Query(..., alias="hub.challenge"),
):

    if mode and verify_token:
        if (
            mode == "subscribe"
            and verify_token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN
        ):
            return PlainTextResponse(content=challenge, status_code=status.HTTP_200_OK)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Verification failed"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing parameters"
        )


@router.post("", status_code=status.HTTP_200_OK)
@inject
async def handle_webhook(
    request: Request,
    webhook_dispatcher: WebhookDispatcher = Depends(Provide[Container.webhook_dispatcher]),
):

    payload = await request.json()
    for entry in payload.get("entry", []):
        profile_id = entry.get("id")
        for change in entry.get("changes", []):
            field = change.get("field")
            value = change.get("value", {})
            if profile_id is not None:
                value["profile_id"] = profile_id
            
            await webhook_dispatcher.dispatch(field, value)

    return JSONResponse(content={"status": "received"}, status_code=status.HTTP_200_OK)

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from my_celery.api.BaseWhatsAppBusinessApi import send_template_message
from my_celery.signals.lifecycle import get_message_crud
from my_celery.tasks.base_task import BaseTask
from my_celery.celery_app import celery_app
from my_celery.database.db_config import get_db
from my_celery.models.Message import Message
from my_celery.utils.DateTimeHelper import DateTimeHelper
from my_celery.utils.Helper import Helper

RETRY_COUNTDOWN = 60
MAX_RETRIES = 1

@celery_app.task(
    name="my_celery.tasks.template_broadcast",
    bind=True,
    base=BaseTask,
    max_retries=MAX_RETRIES,
    retry_jitter=True,        
    default_retry_delay=RETRY_COUNTDOWN,
    acks_late=False,
)
def template_broadcast(self, data):
    try:
        message_crud = get_message_crud()
    except RuntimeError as e:
        self.logger.error("failed_to_initialize_message_crud", error=str(e))
        raise self.retry(exc=e)

    business_number = data.get("business_number")
    user_id = data.get("user_id")
    content = data.get("content")
    business_token = data.get("business_token")
    business_number_id = data.get("business_number_id")
    phone_to = content.get("to") if content else None

    if not all([business_number, user_id, content, business_token, business_number_id, phone_to]):
        self.logger.error("invalid_input_data", data=data)
        return {"error": "Invalid input"}

    try:
        response_template = send_template_message(
            accessToken=business_token,
            phone_number_id=business_number_id,
            payload=content
        )
    except Exception as e:
        return self.retry_task(exc=e)

    messages = response_template.get("messages", [])
    if not messages:
        self.logger.error("no_messages_in_response", response=response_template)
        return {"error": "There is no message in response from WhatsApp"}

    wa_message_id = messages[0].get("id")
    if not wa_message_id:
        self.logger.error("Missing WhatsApp message ID from response.")
        return {"error": "No message ID in WhatsApp response"}

    country_code, contact_number = Helper.number_parsed(phone_to)

    try:
        with get_db() as db:
            procedure_sql = text("""
                CALL broadcast_messaging(
                    :p_contact_phone, 
                    :p_country_code_phone, 
                    :p_business_phone, 
                    :p_whatsapp_message_id, 
                    :p_user_id, 
                    NULL,
                    NULL
                )
            """)
            result = db.execute(procedure_sql, {
                "p_contact_phone": str(contact_number),
                "p_country_code_phone": country_code,
                "p_business_phone": business_number,
                "p_whatsapp_message_id": wa_message_id,
                "p_user_id": user_id
            })

            row = result.fetchone()
            if not row:
                self.logger.error("stored_procedure_no_result")
                return {"error": "Stored procedure did not return IDs"}
            conversation_id, message_id = row
    except OperationalError as db_exc:
        return self.retry_task(exc=db_exc)

    try:
        message_doc = Message(
            id=message_id,
            message_type="template",
            message_status="sent",
            conversation_id=conversation_id,
            wa_message_id=wa_message_id,
            content=content,
            is_from_contact=False,
            member_id=user_id,
            created_at=DateTimeHelper.now_utc(),
            updated_at=DateTimeHelper.now_utc()
        )
        message_crud.create(message_doc)
    except Exception as mongo_exc:
        self.logger.error("mongo_insertion_failed", error=str(mongo_exc))
        return self.retry_task(exc=mongo_exc)
    
from typing import List, Optional, Dict

from app.chat_bot.models.schema.interactive_body.DynamicInteractiveMessageRequest import DynamicInteractiveMessageRequest
from app.chat_bot.models.schema.interactive_body.InteractiveActionRequest import InteractiveActionRequest, ListRowRequest, ListSectionRequest
from app.chat_bot.models.schema.interactive_body.InteractiveBodyRequest import InteractiveBodyRequest
from app.chat_bot.models.schema.interactive_body.InteractiveButtonRequest import InteractiveButtonRequest
from app.chat_bot.models.schema.interactive_body.InteractiveFooterRequest import InteractiveFooterRequest
from app.chat_bot.models.schema.interactive_body.InteractiveHeaderRequest import InteractiveHeaderRequest
from app.chat_bot.models.schema.interactive_builder.ActionComponentBuilder import ActionComponentBuilder
from app.chat_bot.models.schema.interactive_builder.BodyComponentBuilder import BodyComponentBuilder
from app.chat_bot.models.schema.interactive_builder.FooterComponentBuilder import FooterComponentBuilder
from app.chat_bot.models.schema.interactive_builder.HeaderComponentBuilder import HeaderComponentBuilder
from app.chat_bot.models.schema.request.CreateInteractiveMessageRequest import CreateInteractiveMessageRequest
from app.utils.enums.InteractiveMessageEnum import InteractiveType


class WhatsAppInteractiveMessageBuilder:
    
    @staticmethod
    def build_interactive_message(
        interactive_request: DynamicInteractiveMessageRequest,
        recipient: str
    ) -> CreateInteractiveMessageRequest:
        header_builder = HeaderComponentBuilder()
        body_builder = BodyComponentBuilder()
        footer_builder = FooterComponentBuilder()
        action_builder = ActionComponentBuilder()
        
        interactive_content = {
            "type": interactive_request.type.value,
            "body": body_builder.build(interactive_request.body),
            "action": action_builder.build(interactive_request.action)
        }
        
        if interactive_request.header:
            interactive_content["header"] = header_builder.build(interactive_request.header)
        
        if interactive_request.footer:
            interactive_content["footer"] = footer_builder.build(interactive_request.footer)
        
        return CreateInteractiveMessageRequest(
            to=recipient,
            interactive=interactive_content
        )
    
    @staticmethod
    def build_button_message(
        body_text: str,
        buttons: List[Dict[str, str]], 
        recipient: str,
        header: Optional[InteractiveHeaderRequest] = None,
        footer_text: Optional[str] = None
    ) -> CreateInteractiveMessageRequest:

        button_objects = [
            InteractiveButtonRequest(reply=btn) for btn in buttons
        ]
        
        interactive_request = DynamicInteractiveMessageRequest(
            type=InteractiveType.BUTTON,
            header=header,
            body=InteractiveBodyRequest(text=body_text),
            footer=InteractiveFooterRequest(text=footer_text) if footer_text else None,
            action=InteractiveActionRequest(buttons=button_objects)
        )
        
        return WhatsAppInteractiveMessageBuilder.build_interactive_message(
            interactive_request, recipient
        )
    
    @staticmethod
    def build_list_message(
        body_text: str,
        button_text: str,
        sections: List[Dict],  
        recipient: str,
        header: Optional[InteractiveHeaderRequest] = None,
        footer_text: Optional[str] = None
    ) -> CreateInteractiveMessageRequest:
        
        section_objects = []
        for section in sections:
            rows = [
                ListRowRequest(
                    id=row['id'],
                    title=row['title'],
                    description=row.get('description')
                )
                for row in section['rows']
            ]
            section_objects.append(
                ListSectionRequest(
                    title=section.get('title'),
                    rows=rows
                )
            )
        
        interactive_request = DynamicInteractiveMessageRequest(
            type=InteractiveType.LIST,
            header=header,
            body=InteractiveBodyRequest(text=body_text),
            footer=InteractiveFooterRequest(text=footer_text) if footer_text else None,
            action=InteractiveActionRequest(
                button=button_text,
                sections=section_objects
            )
        )
        
        return WhatsAppInteractiveMessageBuilder.build_interactive_message(
            interactive_request, recipient
        )
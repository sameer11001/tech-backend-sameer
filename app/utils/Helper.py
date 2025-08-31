from __future__ import annotations
import ast
import phonenumbers
from phonenumbers import NumberParseException
from datetime import datetime, timezone, tzinfo
from typing import Any, Dict, Optional
class Helper:
    
    @staticmethod
    def number_parsed(number: str):

        if not number.startswith("+"):
            number = f"+{number.lstrip('+')}"         
        try:
            parsed = phonenumbers.parse(number, None) 
        except NumberParseException as exc:
            raise ValueError(f"Invalid phone number: {exc}") from exc
        if not phonenumbers.is_valid_number(parsed):   
            raise ValueError("Invalid phone number")
        return f"+{parsed.country_code}", str(parsed.national_number)
    
    @staticmethod
    def to_utc_aware(dt: datetime, *, assume_tz: Optional[tzinfo] = None) -> datetime:
        if dt.tzinfo is None:
            local_tz = assume_tz or timezone.utc
            dt = dt.replace(tzinfo=local_tz)
    
        return dt.astimezone(timezone.utc)
    
    @staticmethod
    def conversation_expiration_calculate(time_to_subtract: Any) -> str:
        if isinstance(time_to_subtract, str):
            try:
                time_dict = ast.literal_eval(time_to_subtract)
                time_to_subtract = time_dict.get("__datetime__")
            except Exception as e:
                raise ValueError(f"Could not parse datetime from redis: {e}")
        
        if isinstance(time_to_subtract, str):
            expires = datetime.fromisoformat(time_to_subtract)
        elif isinstance(time_to_subtract, datetime):
            expires = time_to_subtract
        else:
            raise TypeError("Invalid type for time_to_subtract")
    
        td = expires - datetime.now(timezone.utc)
        total_sec = int(td.total_seconds())
        h, rem = divmod(total_sec, 3600)
        m, _ = divmod(rem, 60)
        return f"{h}:{m:02d}:{rem % 60:02d}"     

    @staticmethod
    def _get_last_message_content(message_data: Dict[str, Any]) -> str:

        message_type = message_data.get("type", "unknown")
        content = message_data.get("content", {})
        
        if message_type == "text":
            return content.get("text", "")
            
        elif message_type == "image":
            caption = content.get("caption", "")
            return f"📷 Photo{f': {caption}' if caption else ''}"
            
        elif message_type == "video":
            caption = content.get("caption", "")
            return f"🎥 Video{f': {caption}' if caption else ''}"
            
        elif message_type == "audio":
            return "🎵 Audio"
            
        elif message_type == "document":
            filename = content.get("filename", "Document")
            return f"📄 {filename}"
            
        elif message_type == "location":
            location_name = content.get("name", "")
            address = content.get("address", "")
            if location_name:
                return f"📍 {location_name}"
            elif address:
                return f"📍 {address}"
            else:
                return "📍 Location"
                
        elif message_type == "reaction":
            emoji = content.get("emoji", "👍")
            return f"Reacted {emoji} to a message"
            
        elif message_type == "interactive":
            interactive_type = content.get("interactive_type", "")
            if interactive_type == "button_reply":
                button_text = content.get("interactive", {}).get("button_reply", {}).get("title", "")
                return f"Selected: {button_text}" if button_text else "Interactive message"
            elif interactive_type == "list_reply":
                list_title = content.get("interactive", {}).get("list_reply", {}).get("title", "")
                return f"Selected: {list_title}" if list_title else "List selection"
            else:
                return "Interactive message"
                
        elif message_type == "sticker":
            return "Sticker"
            
        elif message_type == "contacts":
            return "📞 Contact"
            
        else:
            return f"{message_type.capitalize()} message" if message_type != "unknown" else "Message"
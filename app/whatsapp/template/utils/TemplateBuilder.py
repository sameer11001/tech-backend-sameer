from typing import Any, Dict, List, Optional
from app.whatsapp.template.models.schema.TemplateBody import (
    TemplateComponent,
    HeaderComponent, 
    BodyComponent,
    FooterComponent,
    QuickReplyButton,
    URLButton,
    CallButton,
    TextParameter,
    PayloadParameter,
    TemplateLanguage,
    TemplateObject
)


class TemplateBuilder:
    
    LANGUAGE_MAPPING = {
        'en': 'en_US',
        'ar': 'ar_EG', 
        'es': 'es_ES',
        'fr': 'fr_FR',
        'de': 'de_DE',
        'it': 'it_IT',
        'pt': 'pt_BR',
        'ru': 'ru_RU',
        'zh': 'zh_CN',
        'ja': 'ja_JP',
        'ko': 'ko_KR',
        'hi': 'hi_IN',
        'tr': 'tr_TR',
        'nl': 'nl_NL',
        'pl': 'pl_PL'
    }

    @staticmethod
    def build_template_object(template_body: Dict[str, Any], parameters: Optional[List[str]] = None) -> TemplateObject:

        components = TemplateBuilder._build_components(template_body, parameters)
        
        lang_raw = template_body["language"]
        normalized_lang = TemplateBuilder._normalize_language_code(lang_raw)
        
        language = TemplateLanguage(code=normalized_lang)

        return TemplateObject(
            name=template_body["name"],
            language=language,
            components=components
        )

    @staticmethod
    def _build_components(template_body: Dict[str, Any], parameters: Optional[List[str]] = None) -> List[TemplateComponent]:

        user_params = parameters or []
        param_idx = 0
        components: List[TemplateComponent] = []

        for comp in template_body.get("components", []):
            comp_type = comp["type"]

            if comp_type in ["HEADER", "BODY", "FOOTER"]:
                result = TemplateBuilder._build_text_component(
                    comp, comp_type, user_params, param_idx
                )
                if result:
                    components.append(result["component"])
                    param_idx = result["param_idx"]

            elif comp_type == "BUTTONS":
                result = TemplateBuilder._build_button_components(
                    comp, user_params, param_idx
                )
                if result:
                    components.extend(result["components"])
                    param_idx = result["param_idx"]

        return components

    @staticmethod
    def _build_text_component(comp: Dict[str, Any], comp_type: str, user_params: List[str], param_idx: int) -> Optional[Dict]:
        text = comp.get("text", "")
        
        if not text:
            return None
            
        placeholder_count = text.count("{{")
        
        if placeholder_count == 0:
            return None
            
        vals = user_params[param_idx:param_idx + placeholder_count]
        param_idx += placeholder_count
        
        if not vals:
            if comp_type == "HEADER":
                example_data = comp.get("example", {}).get("header_text", [])
                vals = example_data[0] if example_data and example_data[0] else []
            elif comp_type == "BODY":
                example_data = comp.get("example", {}).get("body_text", [[]])
                vals = example_data[0] if example_data and example_data[0] else []
            
            if not vals:
                return None
            
        params_objs = [TextParameter(text=str(v)) for v in vals]
        
        if comp_type == "HEADER":
            component = HeaderComponent(parameters=params_objs)
        elif comp_type == "BODY":
            component = BodyComponent(parameters=params_objs)
        else:  
            component = FooterComponent(parameters=params_objs)
            
        return {
            "component": component,
            "param_idx": param_idx
        }

    @staticmethod
    def _build_button_components(comp: Dict[str, Any], user_params: List[str], param_idx: int) -> Optional[Dict]:
        """Build button components only for dynamic buttons."""
        buttons = comp.get("buttons", [])
        if not buttons:
            return None
            
        components = []
        
        for idx, btn in enumerate(buttons):
            btn_type = btn.get("type")
            
            if btn_type == "QUICK_REPLY":
                btn_text = btn.get("text", "")
                if "{{" in btn_text and param_idx < len(user_params):
                    payload_value = user_params[param_idx]
                    param_idx += 1
                    prm = PayloadParameter(payload=payload_value)
                    components.append(QuickReplyButton(index=idx, parameters=[prm]))
                
            elif btn_type == "URL":
                url = btn.get("url", "")
                if "{{" in url and param_idx < len(user_params):
                    url_param = user_params[param_idx]
                    param_idx += 1
                    txt = TextParameter(text=url_param)
                    components.append(URLButton(index=idx, parameters=[txt]))
                
            elif btn_type == "PHONE_NUMBER":
                phone = btn.get("phone_number", "")
                if "{{" in phone and param_idx < len(user_params):
                    phone_param = user_params[param_idx]
                    param_idx += 1
                    txt = TextParameter(text=phone_param)
                    components.append(CallButton(index=idx, parameters=[txt]))
                        
        if not components:
            return None
            
        return {
            "components": components,
            "param_idx": param_idx
        }

    @staticmethod
    def _normalize_language_code(language: str) -> str:
        return TemplateBuilder.LANGUAGE_MAPPING.get(language.lower(), language)

    @staticmethod
    def is_template_static(template_body: Dict[str, Any]) -> bool:
        """
        Check if a template is completely static (no dynamic placeholders).
        Returns True if the template needs no parameters.
        """
        for comp in template_body.get("components", []):
            comp_type = comp["type"]
            
            # Check text components
            if comp_type in ["HEADER", "BODY", "FOOTER"]:
                text = comp.get("text", "")
                if text and "{{" in text:
                    return False
            
            # Check button components
            elif comp_type == "BUTTONS":
                buttons = comp.get("buttons", [])
                for btn in buttons:
                    btn_text = btn.get("text", "")
                    btn_url = btn.get("url", "")
                    btn_phone = btn.get("phone_number", "")
                    
                    if ("{{" in btn_text) or ("{{" in btn_url) or ("{{" in btn_phone):
                        return False
        
        return True

    @staticmethod
    def count_parameters_needed(template_body: Dict[str, Any]) -> int:
        """Count how many parameters are needed for a template."""
        total_params = 0
        
        for comp in template_body.get("components", []):
            comp_type = comp["type"]
            
            if comp_type in ["HEADER", "BODY", "FOOTER"]:
                text = comp.get("text", "")
                if text:
                    total_params += text.count("{{")
            
            elif comp_type == "BUTTONS":
                buttons = comp.get("buttons", [])
                for btn in buttons:
                    btn_text = btn.get("text", "")
                    btn_url = btn.get("url", "")
                    btn_phone = btn.get("phone_number", "")
                    
                    total_params += btn_text.count("{{") + btn_url.count("{{") + btn_phone.count("{{")
        
        return total_params
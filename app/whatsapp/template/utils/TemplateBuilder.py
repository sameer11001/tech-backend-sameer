from typing import List, Dict, Any, Optional
from app.whatsapp.template.models.Template import Template
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
    @staticmethod
    def build_template_components(template_body: Dict[str, Any], parameters: Optional[List[str]] = None) -> List[TemplateComponent]:
        user_params = parameters or []
        param_idx = 0
        components: List[TemplateComponent] = []

        for comp in template_body["components"]:
            t = comp["type"]

            if t == "HEADER":
                # Handle header component
                example_hdr = comp.get("example", {}).get("header_text", [])
                count = len(example_hdr) if example_hdr else comp["text"].count("{{")

                vals = user_params[param_idx:param_idx + count]
                param_idx += count

                if vals:
                    params_objs = [TextParameter(text=v) for v in vals]
                else:
                    default = example_hdr[0] if example_hdr else comp.get("text", "")
                    params_objs = [TextParameter(text=default)]

                components.append(HeaderComponent(parameters=params_objs))

            elif t == "BODY":
                # Handle body component
                example_body = comp.get("example", {}).get("body_text", [[]])
                ex_list = example_body[0] if example_body and example_body[0] else []
                count = len(ex_list) if ex_list else comp["text"].count("{{")

                vals = user_params[param_idx:param_idx + count]
                param_idx += count

                if vals:
                    params_objs = [TextParameter(text=v) for v in vals]
                else:
                    params_objs = [TextParameter(text=v) for v in ex_list]

                components.append(BodyComponent(parameters=params_objs))

            elif t == "FOOTER":
                # Handle footer component
                example_ftr = comp.get("example", {}).get("footer_text", [])
                vals = user_params[param_idx:param_idx + 1]
                if vals:
                    txt = vals[0]
                else:
                    txt = example_ftr[0] if example_ftr else comp.get("text", "")
                components.append(FooterComponent(parameters=[TextParameter(text=txt)]))
                if vals:
                    param_idx += 1

            elif t == "BUTTONS":
                # Handle buttons component
                for idx, btn in enumerate(comp.get("buttons", [])):
                    if btn["type"] == "QUICK_REPLY":
                        prm = PayloadParameter(payload=btn["text"])
                        components.append(QuickReplyButton(index=idx, parameters=[prm]))
                    elif btn["type"] == "URL":
                        txt = TextParameter(text=btn["url"])
                        components.append(URLButton(index=idx, parameters=[txt]))
                    else:
                        txt = TextParameter(text=btn["phone_number"])
                        components.append(CallButton(index=idx, parameters=[txt]))

        return components

    @staticmethod
    def build_template_object(template_body: Dict[str, Any], parameters: Optional[List[str]] = None) -> TemplateObject:
        components = TemplateBuilder.build_template_components(template_body, parameters)
        
        lang_raw = template_body["language"]
        language = (
            TemplateLanguage(code=lang_raw)
            if isinstance(lang_raw, str)
            else TemplateLanguage(**lang_raw)
        )

        return TemplateObject(
            name=template_body["name"],
            language=language,
            components=components
        ) 
def darkness_to_hex(value: int) -> str:
    clamped = max(0, min(30, value))
    return f"#{clamped:02x}{clamped:02x}{clamped:02x}"


def generate_css(stealth: bool, darkness: int, opacity: float,
                 font_family: str = "Monospace", font_size: int = 13) -> str:
    if stealth:
        text_color = darkness_to_hex(darkness)
        user_color = darkness_to_hex(min(darkness + 5, 30))
        border_color = darkness_to_hex(min(darkness + 3, 25))
        bg_alpha = opacity

        return f"""
window {{
    background-color: rgba(0, 0, 0, {bg_alpha});
}}

.chat-container {{
    background-color: transparent;
}}

.chat-view {{
    background-color: #000000;
    color: {text_color};
    font-family: "{font_family}";
    font-size: {font_size}px;
    padding: 8px;
}}

.chat-view text {{
    background-color: #000000;
    color: {text_color};
}}

.user-message {{
    color: {user_color};
}}

.ai-message {{
    color: {text_color};
}}

.input-entry {{
    background-color: #000000;
    color: {text_color};
    border: 1px solid {border_color};
    font-family: "{font_family}";
    font-size: {font_size}px;
    padding: 6px 10px;
    min-height: 28px;
}}

.input-entry:focus {{
    border-color: {darkness_to_hex(min(darkness + 6, 30))};
    outline: none;
}}

.send-button {{
    background-color: #000000;
    color: {text_color};
    border: 1px solid {border_color};
    padding: 6px 12px;
    min-height: 28px;
}}

headerbar {{
    background-color: rgba(0, 0, 0, {bg_alpha});
    border: none;
    box-shadow: none;
    min-height: 24px;
}}

headerbar title {{
    color: {border_color};
    font-size: 10px;
}}

headerbar windowcontrols button {{
    color: {border_color};
    opacity: 0.3;
}}

scrollbar {{
    opacity: 0;
}}

.status-label {{
    color: {border_color};
    font-family: "{font_family}";
    font-size: {font_size - 2}px;
    padding: 2px 8px;
}}

.model-selector {{
    background-color: #000000;
    color: {text_color};
    border: 1px solid {border_color};
    font-size: {font_size - 2}px;
    min-height: 20px;
    padding: 2px 6px;
}}
"""
    else:
        return f"""
window {{
    background-color: rgba(30, 30, 30, 0.95);
}}

.chat-container {{
    background-color: transparent;
}}

.chat-view {{
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: "{font_family}";
    font-size: {font_size}px;
    padding: 8px;
}}

.chat-view text {{
    background-color: #1e1e1e;
    color: #e0e0e0;
}}

.user-message {{
    color: #8bc6fc;
}}

.ai-message {{
    color: #e0e0e0;
}}

.input-entry {{
    background-color: #2a2a2a;
    color: #e0e0e0;
    border: 1px solid #444444;
    font-family: "{font_family}";
    font-size: {font_size}px;
    padding: 6px 10px;
    min-height: 28px;
}}

.input-entry:focus {{
    border-color: #6699cc;
    outline: none;
}}

.send-button {{
    background-color: #333333;
    color: #e0e0e0;
    border: 1px solid #444444;
    padding: 6px 12px;
    min-height: 28px;
}}

headerbar {{
    background-color: rgba(30, 30, 30, 0.95);
    border-bottom: 1px solid #444444;
    min-height: 24px;
}}

headerbar title {{
    color: #888888;
    font-size: 10px;
}}

scrollbar {{
    opacity: 0.5;
}}

.status-label {{
    color: #888888;
    font-family: "{font_family}";
    font-size: {font_size - 2}px;
    padding: 2px 8px;
}}

.model-selector {{
    background-color: #2a2a2a;
    color: #e0e0e0;
    border: 1px solid #444444;
    font-size: {font_size - 2}px;
    min-height: 20px;
    padding: 2px 6px;
}}
"""


def apply_css(css_provider, css_string: str):
    css_provider.load_from_string(css_string)

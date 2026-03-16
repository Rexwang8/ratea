# Text Helper Functions
import textwrap

def sanitize_text(input_text: str) -> str:
    """Sanitize text by stripping leading/trailing whitespace and normalizing spaces."""
    if not isinstance(input_text, str):
        return ""
    # Strip leading/trailing whitespace
    sanitized = input_text.strip()
    # Replace multiple spaces/newlines with a single space
    sanitized = ' '.join(sanitized.split())
    return sanitized

def wrap_text(input_text: str, width: int) -> str:
    """Wrap text to a specified width."""
    if not isinstance(input_text, str):
        return ""
    wrapped = textwrap.fill(input_text, width=width)
    return wrapped
def wrap_text_no_break_words(input_text: str, width: int) -> str:
    """Wrap text to a specified width without breaking words."""
    if not isinstance(input_text, str):
        return ""
    wrapper = textwrap.TextWrapper(width=width, break_long_words=False, replace_whitespace=False, expand_tabs=True)
    wrapped = wrapper.fill(input_text)
    return wrapped, len(wrapped.splitlines())



def truncate_text(input_text: str, max_length: int) -> str:
    """Truncate text to a maximum length, adding ellipsis if truncated."""
    if not isinstance(input_text, str):
        return ""
    if len(input_text) <= max_length:
        return input_text
    return input_text[:max_length - 3] + "..."
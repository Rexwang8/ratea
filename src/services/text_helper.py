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
def wrap_text_no_break_words(input_text: str, width: int) -> tuple[str, int]:
    """Wrap text to a specified width without breaking words.

    Preserves intentional paragraph breaks (blank-line-separated blocks)
    and single newlines within blocks are collapsed into spaces.  Each
    paragraph is wrapped independently so earlier paragraphs don't
    influence later ones, and blank lines are kept as paragraph separators.
    """
    if not isinstance(input_text, str):
        return "", 0

    # Split into paragraphs on blank lines (one or more consecutive newlines)
    paragraphs = input_text.split('\n')
    wrapped_paras = []

    for para in paragraphs:
        # Collapse intra-paragraph newlines/spaces into single spaces,
        # so that soft line breaks within a paragraph don't cause
        # double-wrapping.
        flat = ' '.join(para.split())
        if not flat:
            # Preserve empty paragraphs as blank lines
            wrapped_paras.append('')
            continue
        wrapper = textwrap.TextWrapper(
            width=width,
            break_long_words=False,
            replace_whitespace=True,
            expand_tabs=True,
        )
        wrapped_paras.append(wrapper.fill(flat))

    result = '\n'.join(wrapped_paras)
    return result, len(result.splitlines())



def truncate_text(input_text: str, max_length: int) -> str:
    """Truncate text to a maximum length, adding ellipsis if truncated."""
    if not isinstance(input_text, str):
        return ""
    if len(input_text) <= max_length:
        return input_text
    return input_text[:max_length - 3] + "..."
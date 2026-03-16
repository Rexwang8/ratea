import dearpygui.dearpygui as dpg


def add_autocomplete_input(
    *,
    tag: str,
    label: str,
    items: list[str],
    default_value: str = "",
    width: int = 200,
    max_visible_items: int = 5,
    on_change=None
):
    """
    Reusable autocomplete input with dropdown.

    Args:
        tag: Base tag for the widget
        label: Input label
        items: List of possible values
        default_value: Initial value
        width: Input width
        max_visible_items: Max items shown in dropdown
        on_change: Optional callback(value: str)
    """

    uuid = dpg.generate_uuid()

    group_tag = f"{tag}_group_{uuid}"

    input_tag = f"{tag}_input_{uuid}"
    dropdown_tag = f"{tag}_dropdown_{uuid}"
    listbox_tag = f"{tag}_listbox_{uuid}"

    items = list(dict.fromkeys(items))  # de-dupe, preserve order

    def filtered_items(text: str):
        text = text.lower()
        matches = [v for v in items if text in v.lower()]
        return sorted(matches, key=lambda v: v.lower())

    def on_input(sender, app_data):
        matches = filtered_items(app_data)

        dpg.configure_item(listbox_tag, items=matches)

        if matches:
            dpg.show_item(dropdown_tag)
        else:
            dpg.hide_item(dropdown_tag)

        if on_change:
            on_change(app_data)

    def on_select(sender, app_data):
        dpg.set_value(input_tag, app_data)
        dpg.hide_item(dropdown_tag)

        if on_change:
            on_change(app_data)

    def hide_dropdown():
        dpg.hide_item(dropdown_tag)

    def on_focus(sender, app_data):
        # app_data == True when focused, False when focus lost
        if not app_data:
            hide_dropdown()

    # ---- UI ----
    with dpg.group(tag=group_tag):
        dpg.add_input_text(
            tag=input_tag,
            label=label,
            default_value=default_value,
            width=width,
            callback=on_input,
            on_focus=on_focus
        )

        with dpg.child_window(
            tag=dropdown_tag,
            width=width,
            height=30 * max_visible_items,
            border=True
        ):
            dpg.add_listbox(
                tag=listbox_tag,
                items=items,
                num_items=max_visible_items,
                callback=on_select,
                width=-1,
            )

    hide_dropdown()

    return input_tag

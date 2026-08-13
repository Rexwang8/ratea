"""References tab — curated collection of tea guides, blogs, and research.

Extracted from app.py to keep build_ui() manageable.
Contains the deeply nested DPG tab structure for:
- Getting Started (General, Buying)
- Drinking & Brewing (General, Puerh, Hongcha)
- Tea Knowledge (Puerh, Hongcha)
- Tea Blogs (Teadb, Marshaln)
- Research Library (Papers, Academic)
"""

import dearpygui.dearpygui as dpg
from config import Config
from ui.fonts import FontManager
from ui.modals.reference_reader_modal import show_reference_reader


def build_references_tab(fonts: FontManager, data_manager):
    """Construct the full References tab with all sub-tabs and article buttons."""
    with dpg.tab_bar():
        # ------------------------------------------------------------------
        # Getting Started
        # ------------------------------------------------------------------
        with dpg.tab(label="Getting Started"):
            with dpg.tab_bar():
                with dpg.tab(label="General"):
                    dpg.add_text("Beginner Guides")
                    _bind_font(fonts, dpg.last_item(), size=2, bold=True)
                    _make_ref_button(
                        fonts, data_manager,
                        "[Teadb] Puerh for Beginners",
                        "references\\teadb\\articles\\puerh_for_beginners.md",
                    )
                with dpg.tab(label="Buying"):
                    dpg.add_text("Beginner Buying Guides")
                    _bind_font(fonts, dpg.last_item(), size=2, bold=True)
                    _make_ref_button(
                        fonts, data_manager,
                        "[FILLER] First Sheng Purchase Guide",
                        r"references\getting_started\puerh\first_sheng_purchase.md",
                    )
                    _make_ref_button(
                        fonts, data_manager,
                        "[FILLER] Basic Gongfu Setup",
                        r"references\getting_started\general\basic_gongfu_setup.md",
                    )
        # ------------------------------------------------------------------
        # Drinking & Brewing
        # ------------------------------------------------------------------
        with dpg.tab(label="Drinking & Brewing"):
            with dpg.tab_bar():
                with dpg.tab(label="General"):
                    _make_ref_button(
                        fonts, data_manager,
                        "[External] Experience Huigan",
                        "references\\external\\orientalleaf\\experience_huigan\\experience_huigan.md",
                    )
                    _make_ref_button(
                        fonts, data_manager,
                        "[Teadb] Heat Retention Revisited",
                        "references\\teadb\\articles\\heat_retention.md",
                    )
                with dpg.tab(label="Puerh"):
                    _make_ref_button(
                        fonts, data_manager,
                        "[FILLER] Sheng Brewing Guide",
                        r"references\drinking\puerh\sheng_brewing_guide.md",
                    )
                    _make_ref_button(
                        fonts, data_manager,
                        "[FILLER] Shou Brewing Guide",
                        r"references\drinking\puerh\shou_brewing_guide.md",
                    )
                with dpg.tab(label="Hongcha"):
                    _make_ref_button(
                        fonts, data_manager,
                        "[FILLER] Gongfu Hongcha Guide",
                        r"references\drinking\hongcha\gongfu_hongcha_guide.md",
                    )
                    _make_ref_button(
                        fonts, data_manager,
                        "[FILLER] Western Hongcha Guide",
                        r"references\drinking\hongcha\western_hongcha_guide.md",
                    )
        # ------------------------------------------------------------------
        # Tea Knowledge
        # ------------------------------------------------------------------
        with dpg.tab(label="Tea Knowledge"):
            with dpg.tab_bar():
                with dpg.tab(label="Puerh"):
                    _make_ref_button(
                        fonts, data_manager,
                        "[Teadb] In Debt for Dayi Megareport",
                        "references\\teadb\\articles\\in_debt_for_dayi_megareport.md",
                    )

                    _make_ref_button(
                        fonts, data_manager,
                        "[Teadb] Yiwu-ish Enjoyers Mega Report. 103 Teas Reviewed!",
                        "references\\teadb\\articles\\yiwu_ish_enjoyers_mega_report_103_teas_reviewed.md",
                    )

                    _make_ref_button(
                        fonts, data_manager,
                        "[Teadb] Pu'erh Regions: Yunnan Overview",
                        "references\\teadb\\articles\\puerh_regions_yunnan_overview.md",
                    )
                with dpg.tab(label="Hongcha"):
                    _make_ref_button(
                        fonts, data_manager,
                        "[FILLER] Hongcha Types Overview",
                        r"references\knowledge\hongcha\types_overview.md",
                    )
        # ------------------------------------------------------------------
        # Tea Blogs
        # ------------------------------------------------------------------
        with dpg.tab(label="Tea Blogs"):
            with dpg.tab_bar():
                with dpg.tab(label="Teadb"):
                    dpg.add_text(
                        "teadb.org . Run by James and Denny, "
                        "experienced and grounded tea drinkers with a focus on puerh. Only a subset of their content is here. \n" \
                        "Let me know if you want a specific article added."
                    )
                    _make_ref_button(
                        fonts, data_manager,
                        "[Teadb] Puerh for Beginners",
                        "references\\teadb\\articles\\puerh_for_beginners.md",
                    )
                    _make_ref_button(
                        fonts, data_manager,
                        "[Teadb] 7542!!!! The Most Famous Digits in the Pu'erh World!",
                        "references\\teadb\\articles\\7542_the_most_famous_digits_in_the_puerh_world.md",
                    )
                    _make_ref_button(
                        fonts, data_manager,
                        "[Teadb] Heat Retention Revisited",
                        "references\\teadb\\articles\\heat_retention.md",
                    )
                    _make_ref_button(
                        fonts, data_manager,
                        "[Teadb] Four Reasons Why You Should Get Your Baseline in Mid 00s Factory Puerh",
                        "references\\teadb\\articles\\four_reasons_mid_00s_factory_puerh.md",
                    )
                    _make_ref_button(
                        fonts, data_manager,
                        "[Teadb] In Debt for Dayi Megareport",
                        "references\\teadb\\articles\\in_debt_for_dayi_megareport.md",
                    )

                    _make_ref_button(
                        fonts, data_manager,
                        "[Teadb] Yiwu-ish Enjoyers Mega Report. 103 Teas Reviewed!",
                        "references\\teadb\\articles\\yiwu_ish_enjoyers_mega_report_103_teas_reviewed.md",
                    )

                    _make_ref_button(
                        fonts, data_manager,
                        "[Teadb] Pu'erh Regions: Yunnan Overview",
                        "references\\teadb\\articles\\puerh_regions_yunnan_overview.md",
                    )
                with dpg.tab(label="Marshaln"):
                    dpg.add_text(
                        "marshaln.com . Run by Marshaln, a very experienced tea drinker."
                    )
                    _make_ref_button(
                        fonts, data_manager,
                        "[Marshaln] Wuyishan",
                        "references\\external\\marshaln\\wuyishan\\wuyishan.md",
                    )
                    _make_ref_button(
                        fonts, data_manager,
                        "[Marshaln] Objectively good tea",
                        "references\\external\\marshaln\\objectively_good_tea\\objectively_good_tea.md",
                    )
        # ------------------------------------------------------------------
        # Research Library
        # ------------------------------------------------------------------
        with dpg.tab(label="Research Library"):
            with dpg.tab_bar():
                with dpg.tab(label="Papers"):
                    _make_ref_button(
                        fonts, data_manager,
                        "[FILLER] Why Some Sheng Ages Better",
                        r"references\research\blogs\sheng_aging.md",
                    )
                with dpg.tab(label="Academic"):
                    _make_ref_button(
                        fonts, data_manager,
                        "[FILLER] Polyphenols and Aging",
                        r"references\research\academic\polyphenols.md",
                    )


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------


def _make_ref_button(fonts: FontManager, data_manager, label: str, filepath: str):
    """Create an 'Open' button for a reference document in the References tab."""
    dpg.add_button(
        label=label,
        width=-1,
        height=30 * Config.UI_SCALE,
        callback=lambda: show_reference_reader(
            filepath=filepath,
            fonts=fonts,
            data_manager=data_manager,
        ),
    )
    if fonts:
        fonts.dpg_preload_then_bind(dpg.last_item(), size=2, bold=False)
    dpg.add_spacer(height=3)


def _bind_font(fonts: FontManager, item, size=2, bold=False):
    """Bind a font to a DearPyGui item, ensuring the font is loaded first."""
    if fonts:
        fonts.dpg_preload_then_bind(item, size=size, bold=bold)
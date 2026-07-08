import dearpygui.dearpygui as dpg
import dearpypixl as dp
from config import Config
from models.tea import Tea
from services.data_manager import DataManager
from services.date_helper import datetime_to_dearpygui_dt, dearpygui_dt_to_datetime
from services.logger import Logger
from services.score_converter import ScoreConverter
import datetime as dt
from ui.widgets.dropdown_autocomplete import add_autocomplete_input


# Modal for viewing tea details
def _show_tea_modal(tea, data_manager, fonts=None, pre_populate=None):
    modal = TeaModal(tea=tea, data_manager=data_manager, fonts=fonts, pre_populate=pre_populate)
    modal.show()


class TeaModal:
    def __init__(self, tea, data_manager, fonts=None, pre_populate=None):
        self.tea: Tea = tea
        self.data_manager: DataManager = data_manager
        self.fonts = fonts
        self.win = None
        self.pre_populate = pre_populate

    def _bind_font(self, item, size=2, bold=False):
        if self.fonts:
            dpg.bind_item_font(item, self.fonts.get_font_name(size=size, bold=bold))


    def show(self):
        width = 550 * Config.UI_SCALE
        height = 650 * Config.UI_SCALE
        is_editing = self.tea is not None
        action = "Edit Tea" if is_editing else "Add Tea"

        self.win = dp.Window(label=action, modal=True, no_close=False, width=width, height=height)
        with self.win:
            dpg.add_text(action)
            self._bind_font(dpg.last_item(), size=3, bold=True)
            dpg.add_separator()

            fields = {}

            with dpg.child_window(width=-1, height=480 * Config.UI_SCALE, border=True):
                dpg.add_text("Tea Information")
                default_name = self.tea.name if is_editing else (self.pre_populate.name if self.pre_populate else "New Tea Name")
                default_vendor = self.tea.vendor if is_editing else (self.pre_populate.vendor if self.pre_populate else "New Vendor")
                default_type = self.tea.tea_type if is_editing else (self.pre_populate.tea_type if self.pre_populate else "New Tea Type")
                fields['name'] = dp.InputText(label="Tea Name", default_value=default_name)
                valid_vendors = [v[0] for v in self.data_manager.dropdown_tea_vendors]
                if default_vendor not in valid_vendors:
                    valid_vendors.insert(0, default_vendor)  # Add current vendor to the top of the list if it's not already there
                

                fields['vendor'] = add_autocomplete_input(
                    tag="vendor",
                    label="Vendor",
                    items=valid_vendors,
                    default_value=default_vendor,
                    width=250 * Config.UI_SCALE
                )

                validTypes = [t[0] for t in self.data_manager.dropdown_tea_types]
                if default_type not in validTypes:
                    validTypes.insert(0, default_type)  # Add current type to the top of the list if it's not already there
                
                fields['type'] = add_autocomplete_input(
                    tag="type",
                    label="Tea Type",
                    items=validTypes,
                    default_value=default_type,
                    width=250 * Config.UI_SCALE
                )
                
                
                default_year = self.tea.year if is_editing else (self.pre_populate.year if self.pre_populate else 2026)
                fields['year'] = dp.InputInt(label="Year", width=120 * Config.UI_SCALE, default_value=default_year)

                default_quantity = self.tea.quantity if is_editing else (self.pre_populate.quantity if self.pre_populate else 0)
                fields['quantity'] = dp.InputFloat(label="Quantity (g)", width=150 * Config.UI_SCALE, default_value=default_quantity, min_value=0.0, step=0.1, format="%.2f")
                
                # Add text blurb describing the cost input, and that it should be in USD. Add a button to set the cost to 0.01 for free samples.
                dpg.add_text("Cost (USD): Enter the actual cost you paid for this tea. For free samples, click the 'Free Sample' button to set the cost to $0.01.")
                default_cost = self.tea.cost if is_editing else (self.pre_populate.cost if self.pre_populate else 5.00)
                with dpg.group(horizontal=True):
                    fields['cost'] = dp.InputFloat(label="Actual Cost (USD)", width=150 * Config.UI_SCALE, default_value=default_cost, min_value=0.0, step=0.01, format="%.2f")
                    dpg.add_button(label="Free Sample", callback=lambda: fields['cost'].set_value(0.01), width=100 * Config.UI_SCALE, height=25 * Config.UI_SCALE)

                default_catalog_price = self.tea.catalog_price if is_editing else (self.pre_populate.catalog_price if self.pre_populate else 5.00)
                fields['catalog_price'] = dp.InputFloat(label="Catalog Cost (USD)", width=150 * Config.UI_SCALE, default_value=default_catalog_price, min_value=0.0, step=0.01, format="%.2f")

                date_default = datetime_to_dearpygui_dt(dt.datetime.now())
                if is_editing:
                    if self.tea.purchase_date:
                        date_default = datetime_to_dearpygui_dt(self.tea.purchase_date)
                elif self.pre_populate and self.pre_populate.purchase_date:
                     date_default = datetime_to_dearpygui_dt(self.pre_populate.purchase_date)
                


                fields['purchase_date'] = dp.DatePicker(label="Purchase Date", default_value=date_default)

                default_note = self.tea.purchase_note if is_editing else (self.pre_populate.purchase_note if self.pre_populate else "No specified notes.")
                fields['note'] = dp.InputText(label="Purchase Notes", multiline=True, width=-1, height=140 * Config.UI_SCALE, default_value=default_note)

            dpg.add_separator()
            with dpg.group(horizontal=True):
                bwidth = 120 * Config.UI_SCALE
                bheight = 40 * Config.UI_SCALE
                dpg.add_button(label=action, callback=self._execute_action, user_data=(fields, action), width=bwidth, height=bheight)
                dpg.add_button(label="Cancel", callback=self.close, width=bwidth, height=bheight)
    
    def _execute_action(self, sender=None, app_data=None, user_data=None):
        fields, action = user_data
        Logger.info(f"Executing action: {action}")

        if action == "Add Tea":
            self._add_new_tea(fields)
        elif action == "Edit Tea":
            self._edit_tea(fields)
        else:
            Logger.error(f"Unknown action: {action}")

        self.close()

    def _add_new_tea(self, f):
        cost = round(dpg.get_value(f['cost']), 2)
        Logger.info(f"Adding new tea with name: {dpg.get_value(f['name'])}, vendor: {dpg.get_value(f['vendor'])}, type: {dpg.get_value(f['type'])}, year: {dpg.get_value(f['year'])}, quantity: {dpg.get_value(f['quantity'])}, cost: {cost}, catalog_price: {dpg.get_value(f['catalog_price'])}, purchase_date: {dpg.get_value(f['purchase_date'])}, note: {dpg.get_value(f['note'])}")
        tea = Tea(
            name=dpg.get_value(f['name']),
            vendor=dpg.get_value(f['vendor']),
            tea_type=dpg.get_value(f['type']),
            year=dpg.get_value(f['year']),
            quantity=round(dpg.get_value(f['quantity']), 1),
            cost=cost,
            catalog_price=round(dpg.get_value(f['catalog_price']), 2),
            purchase_date=dearpygui_dt_to_datetime(dpg.get_value(f['purchase_date'])),
            purchase_note=dpg.get_value(f['note'])
        )

        Logger.info(f"New tea created: {tea.name}")
        self.data_manager.stash.add_tea(tea)
        self.data_manager.export_to_yaml(self.data_manager.data_save_path)

    def _edit_tea(self, f):
        Logger.info(f"Editing tea {self.tea.id}")
        cost = round(dpg.get_value(f['cost']), 2)
        Logger.info(f"Updating tea with name: {dpg.get_value(f['name'])}, vendor: {dpg.get_value(f['vendor'])}, type: {dpg.get_value(f['type'])}, year: {dpg.get_value(f['year'])}, quantity: {dpg.get_value(f['quantity'])}, cost: {cost}, catalog_price: {dpg.get_value(f['catalog_price'])}, purchase_date: {dpg.get_value(f['purchase_date'])}, note: {dpg.get_value(f['note'])}")

        self.tea.name = dpg.get_value(f['name'])
        self.tea.vendor = dpg.get_value(f['vendor'])
        self.tea.tea_type = dpg.get_value(f['type'])
        self.tea.year = dpg.get_value(f['year'])
        self.tea.quantity = round(dpg.get_value(f['quantity']), 1)
        self.tea.cost = cost
        self.tea.catalog_price = round(dpg.get_value(f['catalog_price']), 2)
        self.tea.purchase_date = dearpygui_dt_to_datetime(dpg.get_value(f['purchase_date']))
        self.tea.purchase_note = dpg.get_value(f['note'])

        Logger.info(f"Tea updated: {self.tea.name}")
        self.data_manager.export_to_yaml(self.data_manager.data_save_path)

    def close(self):
        if self.tea:
            Logger.info(("Closing tea view modal for:", self.tea.name))
        else:
            Logger.info("Closing tea view modal for: Unknown Tea")

        Logger.info(f"info for self.win: {self.win}")
        if self.win:
            self.win.delete()
            self.win = None

            


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
def show_tea_modal(tea, data_manager, fonts=None, pre_populate=None):
    modal = TeaModal(tea=tea, data_manager=data_manager, fonts=fonts, pre_populate=pre_populate)
    modal.show()


class TeaModal:
    def __init__(self, tea, data_manager, fonts=None, pre_populate=None):
        self.tea: Tea = tea
        self.data_manager: DataManager = data_manager
        self.fonts = fonts
        self.win = None
        self.pre_populate = pre_populate


    def show(self):
        width = 550 * Config.UI_SCALE
        height = 650 * Config.UI_SCALE
        is_editing = self.tea is not None
        action = "Edit Tea" if is_editing else "Add Tea"

        self.win = dp.Window(label=action, modal=True, no_close=False, width=width, height=height)
        with self.win:
            dpg.add_text(action)
            dpg.bind_item_font(dpg.last_item(), self.fonts.getFontName(size=3, bold=True) if self.fonts else 0)
            dpg.add_separator()

            fields = {}

            with dpg.child_window(width=-1, height=480 * Config.UI_SCALE, border=True):
                dpg.add_text("Tea Information")
                defaultName = self.tea.name if is_editing else (self.pre_populate.name if self.pre_populate else "New Tea Name")
                defaultVendor = self.tea.vendor if is_editing else (self.pre_populate.vendor if self.pre_populate else "New Vendor")
                defaultType = self.tea.tea_type if is_editing else (self.pre_populate.tea_type if self.pre_populate else "New Tea Type")
                fields['name'] = dp.InputText(label="Tea Name", default_value=defaultName)
                validVendors = [v[0] for v in self.data_manager.dropdownTeaVendors]
                if defaultVendor not in validVendors:
                    validVendors.insert(0, defaultVendor)  # Add current vendor to the top of the list if it's not already there
                

                fields['vendor'] = add_autocomplete_input(
                    tag="vendor",
                    label="Vendor",
                    items=validVendors,
                    default_value=defaultVendor,
                    width=250 * Config.UI_SCALE
                )

                validTypes = [t[0] for t in self.data_manager.dropdownTeaTypes]
                if defaultType not in validTypes:
                    validTypes.insert(0, defaultType)  # Add current type to the top of the list if it's not already there
                
                fields['type'] = add_autocomplete_input(
                    tag="type",
                    label="Tea Type",
                    items=validTypes,
                    default_value=defaultType,
                    width=250 * Config.UI_SCALE
                )
                
                
                defaultYear = self.tea.year if is_editing else (self.pre_populate.year if self.pre_populate else 2026)
                fields['year'] = dp.InputInt(label="Year", width=120 * Config.UI_SCALE, default_value=defaultYear)

                defaultQuantity = self.tea.quantity if is_editing else (self.pre_populate.quantity if self.pre_populate else 0)
                fields['quantity'] = dp.InputFloat(label="Quantity (g)", width=150 * Config.UI_SCALE, default_value=defaultQuantity, min_value=0.0, step=0.1, format="%.2f")
                
                # If free sample, cost is 0.01 to avoid issues with 0 cost teas being filtered out of stats and lists. Show in UI as 0.00 though.
                # Add checkbox
                fields['isFreeSample'] = dp.Checkbox(label="Free Sample", default_value=(self.tea.cost == 0.01 if is_editing else False))
                defaultCost = self.tea.cost if is_editing else (self.pre_populate.cost if self.pre_populate else 5.00)
                fields['cost'] = dp.InputFloat(label="Actual Cost (USD)", width=150 * Config.UI_SCALE, default_value=defaultCost, min_value=0.0, step=0.01, format="%.2f")

                defaultcatalogPrice = self.tea.catalogPrice if is_editing else (self.pre_populate.catalogPrice if self.pre_populate else 5.00)
                fields['catalogPrice'] = dp.InputFloat(label="Catalog Cost (USD)", width=150 * Config.UI_SCALE, default_value=defaultcatalogPrice, min_value=0.0, step=0.01, format="%.2f")

                date_default = datetime_to_dearpygui_dt(dt.datetime.now())
                if is_editing:
                    if self.tea.purchaseDate:
                        date_default = datetime_to_dearpygui_dt(self.tea.purchaseDate)
                elif self.pre_populate and self.pre_populate.purchaseDate:
                     date_default = datetime_to_dearpygui_dt(self.pre_populate.purchaseDate)
                


                fields['purchaseDate'] = dp.DatePicker(label="Purchase Date", default_value=date_default)

                defaultNote = self.tea.purchaseNote if is_editing else (self.pre_populate.purchaseNote if self.pre_populate else "No specified notes.")
                fields['note'] = dp.InputText(label="Purchase Notes", multiline=True, width=-1, height=140 * Config.UI_SCALE, default_value=defaultNote)

            dpg.add_separator()
            with dpg.group(horizontal=True):
                bwidth = 120 * Config.UI_SCALE
                bheight = 40 * Config.UI_SCALE
                dpg.add_button(label=action, callback=self.execute_action, user_data=(fields, action), width=bwidth, height=bheight)
                dpg.add_button(label="Cancel", callback=self.close, width=bwidth, height=bheight)
    
    def execute_action(self, sender=None, app_data=None, user_data=None):
        fields, action = user_data
        Logger.info(f"Executing action: {action}")

        if action == "Add Tea":
            self.add_new_tea(fields)
        elif action == "Edit Tea":
            self.edit_tea(fields)
        else:
            Logger.error(f"Unknown action: {action}")

        self.close()

    def add_new_tea(self, f):
        isFreeSample = dpg.get_value(f['isFreeSample'])
        cost = 0.01 if isFreeSample else round(dpg.get_value(f['cost']), 2)
        Logger.info(f"Adding new tea with name: {dpg.get_value(f['name'])}, vendor: {dpg.get_value(f['vendor'])}, type: {dpg.get_value(f['type'])}, year: {dpg.get_value(f['year'])}, quantity: {dpg.get_value(f['quantity'])}, cost: {cost}, catalogPrice: {dpg.get_value(f['catalogPrice'])}, purchaseDate: {dpg.get_value(f['purchaseDate'])}, note: {dpg.get_value(f['note'])}")
        tea = Tea(
            name=dpg.get_value(f['name']),
            vendor=dpg.get_value(f['vendor']),
            tea_type=dpg.get_value(f['type']),
            year=dpg.get_value(f['year']),
            quantity=round(dpg.get_value(f['quantity']), 1),
            cost=cost,
            catalogPrice=round(dpg.get_value(f['catalogPrice']), 2),
            purchaseDate=dearpygui_dt_to_datetime(dpg.get_value(f['purchaseDate'])),
            purchaseNote=dpg.get_value(f['note'])
        )

        Logger.info(f"New tea created: {tea.name}")
        self.data_manager.stash.add_tea(tea)
        self.data_manager.export_to_yaml(self.data_manager.data_save_path)

    def edit_tea(self, f):
        Logger.info(f"Editing tea {self.tea.id}")
        # if isFreeSample is checked, set cost to 0.01 to avoid issues with 0 cost teas being filtered out of stats and lists. Show in UI as 0.00 though.
        isFreeSample = dpg.get_value(f['isFreeSample'])
        cost = 0.01 if isFreeSample else round(dpg.get_value(f['cost']), 2)
        Logger.info(f"Updating tea with name: {dpg.get_value(f['name'])}, vendor: {dpg.get_value(f['vendor'])}, type: {dpg.get_value(f['type'])}, year: {dpg.get_value(f['year'])}, quantity: {dpg.get_value(f['quantity'])}, cost: {cost}, catalogPrice: {dpg.get_value(f['catalogPrice'])}, purchaseDate: {dpg.get_value(f['purchaseDate'])}, note: {dpg.get_value(f['note'])}")

        self.tea.name = dpg.get_value(f['name'])
        self.tea.vendor = dpg.get_value(f['vendor'])
        self.tea.tea_type = dpg.get_value(f['type'])
        self.tea.year = dpg.get_value(f['year'])
        self.tea.quantity = round(dpg.get_value(f['quantity']), 1)
        self.tea.cost = cost
        self.tea.catalogPrice = round(dpg.get_value(f['catalogPrice']), 2)
        self.tea.purchaseDate = dearpygui_dt_to_datetime(dpg.get_value(f['purchaseDate']))
        self.tea.purchaseNote = dpg.get_value(f['note'])

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

            


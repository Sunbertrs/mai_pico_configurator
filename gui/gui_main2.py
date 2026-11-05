import dearpygui.dearpygui as dpg
from screeninfo import get_monitors

from preset_var import PORT_LABELS, BASIC_INFO_LABEL, buttons

get_monitors()
class MainUI:
    def __init__(self):
        dpg.create_context()
        dpg.create_viewport(title="Mai_pico Configurator", width=820, height=900)

        width, height, channels, data = dpg.load_image("images/sensor.png")
        with dpg.texture_registry(show=True):
            dpg.add_static_texture(width=width, height=height, default_value=data, tag="background")

        with dpg.window(tag="GUI"):
            dpg.add_spacer()
            dpg.add_spacer()
            with dpg.group(tag="left_side", horizontal=True, horizontal_spacing=15):
                with dpg.group():
                    with dpg.group():
                        with dpg.group(horizontal=True):
                            dpg.add_button(label="Connect")
                            dpg.add_text("Disconnected")
                        with dpg.table(tag="port_info", width=450):
                            for i in PORT_LABELS:
                                dpg.add_table_column(label=i)
                            with dpg.table_row():
                                for _ in PORT_LABELS:
                                    dpg.add_text("N/A")
                    dpg.add_spacer()
                    with dpg.table(tag="feat_table", header_row=False, width=570):
                        for _ in range(4):
                            dpg.add_table_column()
                        for i in range(0, len(buttons), 4):
                            with dpg.table_row():
                                for name in list(buttons.keys())[i:i+4]:
                                    dpg.add_button(label=name, width=135)
                with dpg.group():
                    dpg.add_text(BASIC_INFO_LABEL[0])
                    with dpg.table(header_row=False, width=230, borders_outerV=True, borders_outerH=True, borders_innerH=True):
                        dpg.add_table_column()
                        dpg.add_table_column()
                        for i in BASIC_INFO_LABEL[1:]:
                            with dpg.table_row():
                                dpg.add_text(i)
                                dpg.add_text("N/A")
            with dpg.group():
                dpg.add_image("background", tag="sensor_background", width=600, height=600)

        dpg.set_viewport_resize_callback(self.view_resize)
        dpg.show_style_editor()
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("GUI", True)
        dpg.start_dearpygui()
        dpg.destroy_context()

    def set_view_zoom(self, zoom_type: str):
        with dpg.theme() as global_theme:
            with dpg.theme_component():
                if zoom_type == "normal":
                    dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0, 0)
                    dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 7)
                    dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 4, 5)
                    dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 10, 7)
                    dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0)
                    dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 1)
                    dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize, 0)
                else:
                    dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 10)
                    dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 6, 6)
                    dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 13, 8)
                #     dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0)
                #     dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 1)
                #     dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize, 0)

        with dpg.font_registry():
            default_font = dpg.add_font("fonts/NotoSans-Regular.ttf", 20)
            canvas_font = dpg.add_font("fonts/NotoSansMono-Regular.ttf", 20)

        dpg.bind_theme(global_theme)
        dpg.bind_font(default_font)
        dpg.set_global_font_scale(1 if zoom_type == "normal" else 1.5)

    def view_resize(self, sender, app_data):
        dpg.configure_item("sensor_background", width=app_data[2], height=app_data[2])
        print(app_data)
        if app_data[2] < app_data[3]:
            self.set_view_zoom("larger")
        else:
            self.set_view_zoom("normal")
        dpg.configure_item("port_info", width=app_data[2]*0.5)
        dpg.configure_item("feat_table", width=app_data[2]*0.7)
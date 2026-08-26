import flet as ft
import json
import os
import threading
import traceback

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "cbre_break_data.json")
LOG_FILE = os.path.join(SCRIPT_DIR, "cbre_break_log.txt")

TRANSLATIONS = {
    "de": {
        "app_title": "CBRE Break",
        "loading": "Lade...",
        "no_entries": "Keine Einträge vorhanden.",
        "total_price": "Gesamtpreis:",
        "settings": "Einstellungen",
        "edit": "Bearbeiten",
        "add_entry": "Eintrag hinzufügen",
        "products": "Produkte",
        "people": "Personen",
        "paid": "bezahlt",
        "unpaid": "offen",
        "dark_mode": "Dark Mode",
        "auto_add_products": "Auto-Produkte hinzufügen",
        "auto_add_persons": "Auto-Personen hinzufügen",
        "language": "English",
        "new_entry": "Neuer Eintrag",
        "name": "Name",
        "product": "Produkt",
        "price": "Preis",
        "quantity": "Menge",
        "continue": "Weiterer Artikel",
        "new_person": "Neue Person",
        "finish": "Fertig",
        "product_management": "Produkt verwalten",
        "person_management": "Person verwalten",
        "add": "Hinzufügen",
        "delete": "Löschen",
        "delete_group": "Gruppe löschen",
        "confirm_new_list_title": "Neue Liste",
        "confirm_new_list_text": "Alte Liste löschen? Personen und Produkte bleiben erhalten.",
        "no": "Nein",
        "yes": "Ja",
        "close": "Schließen",
        "add_product": "Produkt hinzufügen",
        "expand": "Aufklappen",
        "reset": "Reset",
        "price_required": "Preis erforderlich",
        "invalid_price": "Ungültiger Preis",
        "quantity_min": "Menge muss >= 1 sein",
        "name_required": "Name erforderlich",
        "product_required": "Produkt erforderlich",
        "beta": "Beta(Listen)",
        "list_1": "Liste 1",
        "list_2": "Liste 2",
        "list_3": "Liste 3",
    },
    "en": {
        "app_title": "CBRE Break",
        "loading": "Loading...",
        "no_entries": "No entries found.",
        "total_price": "Total price:",
        "settings": "Settings",
        "edit": "Edit",
        "add_entry": "Add entry",
        "products": "Products",
        "people": "People",
        "paid": "paid",
        "unpaid": "open",
        "dark_mode": "Dark Mode",
        "auto_add_products": "Auto-add products",
        "auto_add_persons": "Auto-add persons",
        "language": "English",
        "new_entry": "New entry",
        "name": "Name",
        "product": "Product",
        "price": "Price",
        "quantity": "Quantity",
        "continue": "Next item",
        "new_person": "New person",
        "finish": "Finish",
        "product_management": "Manage products",
        "person_management": "Manage persons",
        "add": "Add",
        "delete": "Delete",
        "delete_group": "Delete group",
        "confirm_new_list_title": "New list",
        "confirm_new_list_text": "Delete old list? Persons and products will be kept.",
        "no": "No",
        "yes": "Yes",
        "close": "Close",
        "add_product": "Add product",
        "expand": "Expand",
        "reset": "Reset",
        "price_required": "Price required",
        "invalid_price": "Invalid price",
        "quantity_min": "Quantity must be >= 1",
        "name_required": "Name required",
        "product_required": "Product required",
        "beta": "Beta(Lists)",
        "list_1": "List 1",
        "list_2": "List 2",
        "list_3": "List 3",
    },
}


def log(msg):
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"{msg}\n")
    except Exception:
        pass


class CBREBreakApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "CBRE Break"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window_width = 400
        self.page.window_height = 800
        self.page.padding = 10

        self.products = []
        self.people = []
        self._lists = {"1": [], "2": [], "3": []}
        self._active_list_id = "1"
        self.settings = {
            "theme_mode": "light",
            "auto_add_products": True,
            "auto_add_persons": True,
            "language": "de",
            "beta_enabled": False,
        }
        self.editing = False
        self._list_control = None
        self._total_label = None
        self._expanded_groups = set()
        self._save_timer = None
        self._item_toggle_active = False
        self._manager_from_settings = False
        self._current_view = "main"
        self._last_compact = self._compact()

        self.page.on_resize = self._on_page_resize

        self.show_loading()
        self.page.update()
        self.load_data()
        self.apply_theme()
        self.build_main_view()

    def t(self, key):
        lang = self.settings.get("language", "de")
        return TRANSLATIONS.get(lang, TRANSLATIONS["de"]).get(key, key)

    def load_data(self):
        log("load_data start")
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
                    self.products = data.get("products", [])
                    self.people = data.get("people", [])
                    if data.get("current_lists"):
                        self._lists = data["current_lists"]
                        self._active_list_id = str(data.get("active_list_id", "1"))
                    else:
                        old_list = data.get("current_list", [])
                        if self._is_flat_list(old_list):
                            old_list = self._migrate_to_grouped(old_list)
                        self._lists = {"1": old_list, "2": [], "3": []}
                        self._active_list_id = "1"
                    self.settings = data.get("settings", {"theme_mode": "light"})
            log("load_data end")
        except Exception:
            log(f"load_data error: {traceback.format_exc()}")

    def _current_list(self):
        return self._lists.get(self._active_list_id, [])

    def _switch_list(self, list_id):
        list_id = str(list_id)
        if list_id in self._lists and list_id != self._active_list_id:
            self._active_list_id = list_id
            self._expanded_groups.clear()
            self.save_data()
            self.build_main_view()

    def _is_flat_list(self, data):
        if not data:
            return False
        return isinstance(data[0], dict) and "items" not in data[0]

    def _migrate_to_grouped(self, flat_list):
        grouped = []
        for entry in flat_list:
            name = entry.get("name", "")
            item = {
                "product": entry.get("product", ""),
                "price": entry.get("price", 0),
                "quantity": entry.get("quantity", 1),
                "paid": entry.get("paid", False),
            }
            existing = next((g for g in grouped if g["name"] == name), None)
            if existing:
                existing["items"].append(item)
            else:
                grouped.append({"name": name, "items": [item]})
        return grouped

    def save_data(self):
        log("save_data start")
        try:
            with open(DATA_FILE, "w") as f:
                json.dump({
                    "products": self.products,
                    "people": self.people,
                    "current_lists": self._lists,
                    "active_list_id": self._active_list_id,
                    "settings": self.settings,
                }, f, indent=2)
            log("save_data end")
        except Exception:
            log(f"save_data error: {traceback.format_exc()}")

    def apply_theme(self):
        mode = self.settings.get("theme_mode", "light")
        self.page.theme_mode = ft.ThemeMode.LIGHT if mode == "light" else ft.ThemeMode.DARK

    def toggle_theme(self, e=None):
        current = self.page.theme_mode
        self.page.theme_mode = ft.ThemeMode.DARK if current == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        self.settings["theme_mode"] = "dark" if self.page.theme_mode == ft.ThemeMode.DARK else "light"
        self.save_data()
        self.build_main_view()

    def show_settings(self, e=None):
        self.page.clean()
        self._current_view = "settings"
        compact = self._compact()

        theme_switch = ft.Switch(label=self.t("dark_mode"), value=self.page.theme_mode == ft.ThemeMode.DARK, on_change=self._on_settings_theme_change, active_color=ft.Colors.BLUE_400)
        auto_products_switch = ft.Switch(label=self.t("auto_add_products"), value=bool(self.settings.get("auto_add_products", True)), on_change=self._on_settings_auto_products_change, active_color=ft.Colors.GREEN_400)
        auto_persons_switch = ft.Switch(label=self.t("auto_add_persons"), value=bool(self.settings.get("auto_add_persons", True)), on_change=self._on_settings_auto_persons_change, active_color=ft.Colors.PURPLE_400)
        language_switch = ft.Switch(label=self.t("language"), value=self.settings.get("language", "de") == "en", on_change=self._on_settings_language_change, active_color=ft.Colors.ORANGE_400)
        beta_switch = ft.Switch(label=self.t("beta"), value=bool(self.settings.get("beta_enabled", False)), on_change=self._on_settings_beta_change, active_color=ft.Colors.CYAN_400)

        products_btn = ft.ElevatedButton(self.t("products"), icon=ft.icons.Icons.INVENTORY_2, on_click=lambda e: self._open_manager_from_settings("produkt"), height=self._ui(48, 44), style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_100 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.ORANGE_900, shape=ft.RoundedRectangleBorder(radius=self._ui(14, 12))))
        persons_btn = ft.ElevatedButton(self.t("people"), icon=ft.icons.Icons.PEOPLE, on_click=lambda e: self._open_manager_from_settings("person"), height=self._ui(48, 44), style=ft.ButtonStyle(bgcolor=ft.Colors.PURPLE_100 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.PURPLE_900, shape=ft.RoundedRectangleBorder(radius=self._ui(14, 12))))

        settings_card = ft.Container(
            content=ft.Column(
                [
                    ft.Text(self.t("settings"), size=self._ui(20, 18), weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row([ft.Icon(ft.icons.Icons.DARK_MODE, color=ft.Colors.BLUE_400), theme_switch], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Divider(height=1, color=ft.Colors.TRANSPARENT),
                                ft.Row([ft.Icon(ft.icons.Icons.INVENTORY_2, color=ft.Colors.GREEN_400), auto_products_switch], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Divider(height=1, color=ft.Colors.TRANSPARENT),
                                ft.Row([ft.Icon(ft.icons.Icons.PEOPLE, color=ft.Colors.PURPLE_400), auto_persons_switch], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Divider(height=1, color=ft.Colors.TRANSPARENT),
                                ft.Row([ft.Icon(ft.icons.Icons.LANGUAGE, color=ft.Colors.ORANGE_400), language_switch], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Divider(height=1, color=ft.Colors.TRANSPARENT),
                                ft.Row([ft.Icon(ft.icons.Icons.BUG_REPORT, color=ft.Colors.CYAN_400), beta_switch], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ],
                            spacing=self._ui(12, 10),
                        ),
                        padding=self._ui(16, 12),
                        border_radius=self._ui(16, 12),
                        bgcolor=ft.Colors.BLUE_GREY_50 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_900,
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(self.t("product_management") + " / " + self.t("person_management"), size=self._ui(14, 12), color=ft.Colors.BLUE_GREY_600 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_300, text_align=ft.TextAlign.CENTER),
                                ft.Row([products_btn, persons_btn], spacing=self._ui(8, 6)),
                            ],
                            spacing=self._ui(8, 6),
                        ),
                        padding=self._ui(12, 10),
                        border_radius=self._ui(12, 10),
                        bgcolor=ft.Colors.BLUE_GREY_50 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_900,
                    ),
                    ft.ElevatedButton(self.t("finish"), on_click=lambda e: self.build_main_view(), height=self._ui(48, 44), expand=1, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_100 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.GREEN_900, shape=ft.RoundedRectangleBorder(radius=self._ui(14, 12)))),
                ],
                spacing=self._ui(16, 12),
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=self._ui(20, 12),
            border_radius=self._ui(20, 16),
            width=self.page.window_width - 24 if self.page.window_width and self.page.window_width > 240 else 376,
        )

        self.page.add(
            ft.Row([settings_card], alignment=ft.MainAxisAlignment.CENTER),
        )
        self.page.update()

    def _on_settings_theme_change(self, e):
        self.page.theme_mode = ft.ThemeMode.DARK if e.control.value else ft.ThemeMode.LIGHT
        self.settings["theme_mode"] = "dark" if e.control.value else "light"
        self.save_data()
        self.show_settings()

    def _on_settings_auto_products_change(self, e):
        self.settings["auto_add_products"] = bool(e.control.value)
        self.save_data()

    def _on_settings_auto_persons_change(self, e):
        self.settings["auto_add_persons"] = bool(e.control.value)
        self.save_data()

    def _on_settings_language_change(self, e):
        self.settings["language"] = "en" if e.control.value else "de"
        self.save_data()

    def _on_settings_beta_change(self, e):
        self.settings["beta_enabled"] = bool(e.control.value)
        self.save_data()
        self.show_settings()

    def show_loading(self):
        self.page.clean()
        self.page.add(
            ft.Column(
                [
                    ft.ProgressRing(width=40, height=40, stroke_width=4),
                    ft.Text(self.t("loading"), size=16),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

    def _ui(self, desktop_size, mobile_size):
        return mobile_size if getattr(self.page, 'window_width', 400) < 360 else desktop_size

    def _compact(self):
        return getattr(self.page, 'window_width', 400) < 360

    def _on_page_resize(self, e):
        compact = self._compact()
        if compact == self._last_compact:
            return
        self._last_compact = compact
        if self._current_view == "main":
            self.build_main_view()
        elif self._current_view == "settings":
            self.show_settings()
        elif self._current_view == "input":
            self.show_input_view()
        elif self._current_view == "manager":
            pass
        elif self._current_view == "confirm_new_list":
            self.show_confirm_new_list()
        elif self._current_view == "reset":
            self.reset_list(None)

    def build_main_view(self):
        log("build_main_view start")
        try:
            self.page.clean()
            self._expanded_groups.clear()
            self._current_view = "main"
            compact = self._compact()

            title_size = self._ui(22, 18)
            icon_size = self._ui(22, 18)
            header_spacing = self._ui(12, 8)
            section_spacing = self._ui(12, 8)
            card_spacing = self._ui(10, 6)
            total_size = self._ui(18, 16)

            header = ft.Row(
                [
                    ft.IconButton(
                        icon=ft.icons.Icons.SETTINGS,
                        on_click=self.show_settings,
                        tooltip=self.t("settings"),
                        icon_size=icon_size,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_200 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.GREY_700, shape=ft.CircleBorder()),
                    ),
                    ft.IconButton(
                        icon=ft.icons.Icons.EDIT,
                        on_click=self.edit_list,
                        tooltip=self.t("edit"),
                        icon_size=icon_size,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_50 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_800, shape=ft.CircleBorder()),
                    ),
                    ft.IconButton(
                        icon=ft.icons.Icons.ADD,
                        on_click=self.show_input_view,
                        tooltip=self.t("add_entry"),
                        icon_size=icon_size,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_50 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.GREEN_900, shape=ft.CircleBorder()),
                    ),
                ],
                spacing=header_spacing,
            )

            top_right = ft.Row(
                [
                    ft.IconButton(
                        icon=ft.icons.Icons.REFRESH,
                        on_click=self.reset_list,
                        tooltip=self.t("reset"),
                        icon_size=icon_size,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.RED_50 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.RED_900, shape=ft.CircleBorder()),
                    ),
                ],
                spacing=header_spacing,
            )

            title_row = ft.Row(
                [
                    ft.Text(self.t("app_title"), size=title_size, weight=ft.FontWeight.BOLD, expand=1),
                    top_right,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )

            if self.settings.get("beta_enabled"):
                def make_tab(num):
                    is_active = self._active_list_id == str(num)
                    tab_color = ft.Colors.CYAN_600 if is_active else ft.Colors.BLUE_GREY_200 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_700
                    text_color = ft.Colors.WHITE if is_active else ft.Colors.BLUE_GREY_800 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_200
                    return ft.Container(
                        content=ft.Text(str(num), size=16, weight=ft.FontWeight.BOLD, color=text_color),
                        padding=10,
                        bgcolor=tab_color,
                        on_click=lambda e, n=str(num): self._switch_list(n),
                        tooltip=self.t(f"list_{num}"),
                        width=120,
                        alignment="center",
                    )

                tab_row = ft.Row(
                    [make_tab(1), make_tab(2), make_tab(3)],
                    spacing=0,
                )

                header_col = ft.Column([header, title_row, tab_row], spacing=0)
            else:
                header_col = ft.Column([header, title_row], spacing=self._ui(8, 6))

            self._list_control = ft.Column(spacing=card_spacing, scroll=ft.ScrollMode.AUTO, expand=True)

            if not self._current_list():
                self._list_control.controls.append(
                    ft.Container(
                        content=ft.Text(self.t("no_entries"), size=self._ui(15, 13), text_align=ft.TextAlign.CENTER, color=ft.Colors.BLUE_GREY_500 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_400),
                        padding=self._ui(32, 24),
                        alignment="center",
                        expand=True,
                    )
                )
            else:
                for idx, group in enumerate(self._current_list()):
                    self._list_control.controls.append(self._build_group_card(group, idx))

            total = 0
            for group in self._current_list():
                for item in group.get("items", []):
                    if not item.get("paid", False):
                        total += item.get("price", 0) * item.get("quantity", 1)

            self._total_label = ft.Text(f"{self.t('total_price')} {total:.2f} €", size=total_size, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.END, expand=1)

            bottom_row = ft.Row(
                [
                    ft.IconButton(
                        icon=ft.icons.Icons.WB_SUNNY if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.icons.Icons.NIGHTLIGHT,
                        on_click=self.toggle_theme,
                        tooltip=self.t("dark_mode"),
                        icon_size=self._ui(24, 20),
                        style=ft.ButtonStyle(bgcolor=ft.Colors.AMBER_50 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.AMBER_900, shape=ft.CircleBorder()),
                    ),
                    ft.Text("By M.M", size=self._ui(11, 10), weight=ft.FontWeight.W_400, color=ft.Colors.GREY_400 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.GREY_500, expand=1, text_align=ft.TextAlign.RIGHT),
                ],
            )

            content_bg = ft.Colors.BLUE_GREY_50 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_900
            content_border = ft.Colors.BLUE_GREY_200 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_700
            content_container = ft.Container(
                content=self._list_control,
                expand=True,
                bgcolor=content_bg,
                border=ft.Border(left=ft.BorderSide(1, content_border), top=ft.BorderSide(1, ft.Colors.TRANSPARENT), right=ft.BorderSide(1, content_border), bottom=ft.BorderSide(1, content_border)),
                border_radius=ft.BorderRadius(bottom_left=16, bottom_right=16, top_left=0, top_right=0),
            )

            self.page.add(
                ft.Column(
                    [
                        header_col,
                        ft.Divider(height=1, color=ft.Colors.TRANSPARENT),
                        content_container,
                        ft.Divider(height=1, color=ft.Colors.TRANSPARENT),
                        ft.Row([self._total_label], alignment=ft.MainAxisAlignment.END),
                        bottom_row,
                    ],
                    spacing=section_spacing,
                    expand=True,
                )
            )
            log("build_main_view end")
        except Exception:
            log(f"build_main_view error: {traceback.format_exc()}")
            raise

    def _build_group_card(self, group, idx):
        name = group.get("name", "")
        items = group.get("items", [])
        group_paid = all(item.get("paid", False) for item in items) if items else False
        group_total = sum(item.get("price", 0) * item.get("quantity", 1) for item in items)
        is_expanded = idx in self._expanded_groups

        expand_icon = ft.icons.Icons.EXPAND_LESS if is_expanded else ft.icons.Icons.CHEVRON_RIGHT
        icon_color = ft.Colors.GREY_600 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.GREY_300

        border_color = ft.Colors.GREEN_200 if group_paid else ft.Colors.GREY_400
        bg_color = ft.Colors.GREEN_50 if group_paid else ft.Colors.WHITE
        if self.page.theme_mode == ft.ThemeMode.DARK:
            border_color = ft.Colors.GREEN_800 if group_paid else ft.Colors.GREY_600
            bg_color = ft.Colors.GREEN_900 if group_paid else ft.Colors.BLUE_GREY_900

        name_row = ft.Row(
            [
                ft.IconButton(icon=expand_icon, on_click=lambda e, i=idx: self.toggle_group_expand(i), icon_size=22, tooltip=self.t("expand"), style=ft.ButtonStyle(bgcolor=ft.Colors.TRANSPARENT), icon_color=icon_color),
                ft.Text(name, size=16, weight=ft.FontWeight.BOLD, expand=1),
                ft.Text(f"{group_total:.2f} €", size=15, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.END, color=ft.Colors.BLUE_GREY_700 if not group_paid else ft.Colors.GREEN_700 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.GREY_300 if not group_paid else ft.Colors.GREEN_400),
                ft.Text(self.t("paid") if group_paid else self.t("unpaid"), size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700 if group_paid else ft.Colors.ORANGE_700),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        if is_expanded:
            if self.editing:
                item_controls = []
                for item_idx, item in enumerate(items):
                    product = item.get("product", "")
                    price = item.get("price", 0)
                    quantity = item.get("quantity", 1)
                    paid = item.get("paid", False)

                    item_card = ft.Container(
                        content=ft.Column(
                            [
                                ft.TextField(value=product, label=self.t("product"), text_size=14, height=44, on_change=self._make_item_field_changer(group, item_idx, "product"), border_radius=12),
                                ft.Row(
                                    [
                                        ft.TextField(value=str(price), label=self.t("price"), text_size=14, height=44, keyboard_type=ft.KeyboardType.NUMBER, on_change=self._make_item_field_changer(group, item_idx, "price"), expand=1, border_radius=12),
                                        ft.TextField(value=str(quantity), label=self.t("quantity"), text_size=14, height=44, keyboard_type=ft.KeyboardType.NUMBER, on_change=self._make_item_field_changer(group, item_idx, "quantity"), expand=1, border_radius=12),
                                        ft.Checkbox(value=paid, on_change=lambda e, g=group, i=item_idx: self.toggle_item_paid(g, i, e.control.value)),
                                        ft.IconButton(icon=ft.icons.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_400, icon_size=20, on_click=lambda e, g=group, i=item_idx: self.delete_item(g, i)),
                                    ],
                                    spacing=6,
                                ),
                            ],
                            spacing=6,
                        ),
                        padding=10,
                        border_radius=12,
                        bgcolor=ft.Colors.BLUE_GREY_50 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_800,
                    )
                    item_controls.append(item_card)

                add_btn = ft.ElevatedButton(
                    self.t("add_product"),
                    icon=ft.icons.Icons.ADD,
                    on_click=lambda e, g=group: self.add_item_to_group(g),
                    height=44,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_100 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_700, shape=ft.RoundedRectangleBorder(radius=12)),
                )
                delete_group_btn = ft.ElevatedButton(
                    self.t("delete_group"),
                    icon=ft.icons.Icons.DELETE,
                    on_click=lambda e, g=group: self.delete_group(g),
                    height=44,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED_50 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.RED_900, color=ft.Colors.RED_600 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.RED_200, shape=ft.RoundedRectangleBorder(radius=12)),
                )
                content = ft.Column(item_controls + [add_btn, delete_group_btn], spacing=6)
                card = ft.Container(content=content, padding=12, border_radius=16, bgcolor=ft.Colors.BLUE_50 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_900, border=ft.Border(left=ft.BorderSide(1, ft.Colors.BLUE_GREY_200 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_700), top=ft.BorderSide(1, ft.Colors.BLUE_GREY_200 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_700), right=ft.BorderSide(1, ft.Colors.BLUE_GREY_200 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_700), bottom=ft.BorderSide(1, ft.Colors.BLUE_GREY_200 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_700)), shadow=ft.BoxShadow(blur_radius=10, spread_radius=0, color=ft.Colors.with_opacity(0.12, ft.Colors.BLACK), offset=ft.Offset(0, 3)))
            else:
                item_rows = []
                for item in items:
                    product = item.get("product", "")
                    price = item.get("price", 0)
                    quantity = item.get("quantity", 1)
                    paid = item.get("paid", False)
                    line_total = price * quantity

                    item_bg = ft.Colors.GREEN_50 if paid else ft.Colors.WHITE
                    if self.page.theme_mode == ft.ThemeMode.DARK:
                        item_bg = ft.Colors.BLUE_GREY_800 if paid else ft.Colors.BLUE_GREY_900

                    row = ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.icons.Icons.CHECK_CIRCLE if paid else ft.icons.Icons.CIRCLE_OUTLINED, color=ft.Colors.GREEN_600 if paid else ft.Colors.GREY_400, size=20),
                                ft.Text(f"{quantity}x {product}", expand=1, size=14, weight=ft.FontWeight.W_500 if paid else ft.FontWeight.NORMAL),
                                ft.Text(f"{line_total:.2f} €", size=14, text_align=ft.TextAlign.END, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700 if paid else ft.Colors.BLUE_GREY_700 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.GREY_300),
                            ],
                            spacing=10,
                        ),
                        padding=10,
                        border_radius=10,
                        bgcolor=item_bg,
                        ink=True,
                        on_click=lambda e, captured_item=item: self._toggle_item_paid_quick(group, captured_item, e),
                    )
                    item_rows.append(row)

                content = ft.Column(item_rows, spacing=4)
                opacity_val = 0.55 if group_paid else 1.0
                card = ft.Container(
                    content=content,
                    padding=0,
                    border_radius=12,
                    opacity=opacity_val,
                    ink=True,
                    bgcolor=bg_color,
                    border=ft.Border(left=ft.BorderSide(1.5, border_color), top=ft.BorderSide(1.5, border_color), right=ft.BorderSide(1.5, border_color), bottom=ft.BorderSide(1.5, border_color)),
                    shadow=ft.BoxShadow(blur_radius=10, spread_radius=0, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK), offset=ft.Offset(0, 3)),
                )
        else:
            content = ft.Container(padding=ft.Padding(left=36, top=0, right=0, bottom=0))
            card = ft.Container(content=content, padding=6, border_radius=12)

        outer = ft.Container(
            content=ft.Column([name_row, ft.Divider(height=1, color=ft.Colors.TRANSPARENT), card], spacing=6),
            padding=10,
            border_radius=16,
            bgcolor=bg_color,
            border=ft.Border(
                left=ft.BorderSide(4, border_color),
                top=ft.BorderSide(1, ft.Colors.TRANSPARENT),
                right=ft.BorderSide(1, ft.Colors.TRANSPARENT),
                bottom=ft.BorderSide(1, ft.Colors.TRANSPARENT),
            ),
            shadow=ft.BoxShadow(blur_radius=12, spread_radius=0, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK), offset=ft.Offset(0, 4)),
            ink=True,
            on_click=lambda e, g=group: self.toggle_group_paid(g),
        )
        return outer

    def toggle_group_expand(self, idx):
        if idx in self._expanded_groups:
            self._expanded_groups.discard(idx)
            self._sort_current_list()
        else:
            self._expanded_groups.add(idx)
        self._refresh_list()

    def delete_group(self, group):
        try:
            if group in self._current_list():
                self._current_list().remove(group)
                self.save_data()
                self._refresh_list()
        except Exception:
            log(f"delete_group error: {traceback.format_exc()}")

    def add_item_to_group(self, group):
        try:
            group.setdefault("items", []).append({
                "product": "",
                "price": 0,
                "quantity": 1,
                "paid": False,
            })
            self.save_data()
            self._refresh_list()
        except Exception:
            log(f"add_item_to_group error: {traceback.format_exc()}")

    def _normalize_entry_price(self, price, quantity):
        try:
            price_val = float(price)
            qty_val = max(1, int(quantity))
            if qty_val > 1:
                price_val = price_val / qty_val
            return price_val
        except (ValueError, TypeError):
            return 0.0

    def _ensure_product_in_catalog(self, name, unit_price):
        if not self.settings.get("auto_add_products", True):
            return
        name = name.strip()
        if not name:
            return
        if not any(p.get("name", "").lower() == name.lower() for p in self.products):
            self.products.append({"name": name, "price": float(unit_price)})

    def _debounced_save(self, delay=0.4):
        if self._save_timer:
            self._save_timer.cancel()
        self._save_timer = threading.Timer(delay, self.save_data)
        self._save_timer.daemon = True
        self._save_timer.start()

    def _make_item_field_changer(self, group, item_idx, field):
        def changer(e):
            try:
                item = group["items"][item_idx]
                if field == "price":
                    item[field] = float(e.control.value.replace(",", "."))
                elif field == "quantity":
                    val = int(e.control.value.replace(",", "."))
                    item[field] = max(1, val)
                else:
                    item[field] = e.control.value.strip()
                self._debounced_save()
                self._refresh_list()
            except ValueError:
                pass
        return changer

    def _refresh_list(self):
        if self._list_control:
            self._list_control.controls = []
            if not self._current_list():
                self._list_control.controls.append(
                    ft.Container(
                        content=ft.Text(self.t("no_entries"), size=15, text_align=ft.TextAlign.CENTER),
                        padding=16,
                    )
                )
            else:
                for idx, group in enumerate(self._current_list()):
                    self._list_control.controls.append(self._build_group_card(group, idx))
            if not self._expanded_groups:
                self._sort_current_list()
            self._update_total()
            self.page.update()

    def _group_sort_key(self, group):
        try:
            unpaid = sum(item.get("price", 0) * item.get("quantity", 1) for item in group.get("items", []) if not item.get("paid", False))
            group_paid = all(item.get("paid", False) for item in group.get("items", [])) if group.get("items") else False
            return (group_paid, -unpaid if not group_paid else 0)
        except Exception:
            return (False, 0)

    def _sort_current_list(self):
        self._current_list().sort(key=self._group_sort_key)

    def _update_total(self):
        if not self._total_label:
            return
        total = 0
        for group in self._current_list():
            for item in group.get("items", []):
                if not item.get("paid", False):
                    total += item.get("price", 0) * item.get("quantity", 1)
        self._total_label.value = f"{self.t('total_price')} {total:.2f} €"

    def _toggle_item_paid_quick(self, group, item, e=None):
        self._item_toggle_active = True
        try:
            item["paid"] = not item.get("paid", False)
            self.save_data()
            self._refresh_list()
        except Exception:
            log(f"_toggle_item_paid_quick error: {traceback.format_exc()}")
        finally:
            self._item_toggle_active = False

    def toggle_group_paid(self, group):
        if getattr(self, '_item_toggle_active', False):
            return
        try:
            all_paid = all(item.get("paid", False) for item in group.get("items", []))
            for item in group.get("items", []):
                item["paid"] = not all_paid
            self.save_data()
            self._refresh_list()
        except Exception:
            log(f"toggle_group_paid error: {traceback.format_exc()}")

    def toggle_item_paid(self, group, item_idx, paid):
        try:
            group["items"][item_idx]["paid"] = paid
            self.save_data()
            self._refresh_list()
        except Exception:
            log(f"toggle_item_paid error: {traceback.format_exc()}")

    def delete_item(self, group, item_idx):
        if not self.editing:
            return
        try:
            if 0 <= item_idx < len(group.get("items", [])):
                group["items"].pop(item_idx)
                if not group["items"]:
                    if group in self._current_list():
                        self._current_list().remove(group)
                self.save_data()
                self._refresh_list()
        except Exception:
            log(f"delete_item error: {traceback.format_exc()}")

    def reset_list(self, e):
        log("reset_list clicked")
        try:
            self.page.clean()
            self.page.add(
                ft.Column(
                    [
                        ft.Text("Reset", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text("Liste wirklich zurücksetzen? Alle Einträge werden gelöscht."),
                        ft.Row(
                            [
                                ft.ElevatedButton(self.t("no"), on_click=self._reset_cancel, height=48, expand=1, style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_200 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.GREY_700, shape=ft.RoundedRectangleBorder(radius=14))),
                                ft.ElevatedButton(self.t("yes"), on_click=self._reset_confirm, height=48, expand=1, style=ft.ButtonStyle(bgcolor=ft.Colors.RED_100 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.RED_900, shape=ft.RoundedRectangleBorder(radius=14))),
                            ],
                            spacing=12,
                        ),
                    ],
                    spacing=16,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
            self.page.update()
        except Exception:
            log(f"reset_list error: {traceback.format_exc()}")

    def _reset_cancel(self, e):
        self.build_main_view()

    def _reset_confirm(self, e):
        self._lists[self._active_list_id] = []
        self.save_data()
        self.build_main_view()

    def new_option(self, e):
        log("new_option clicked")
        try:
            self.show_confirm_new_list()
        except Exception:
            log(f"new_option error: {traceback.format_exc()}")

    def show_confirm_new_list(self):
        self.page.clean()
        self.page.add(
            ft.Column(
                [
                    ft.Text(self.t("confirm_new_list_title"), size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(self.t("confirm_new_list_text")),
                    ft.Row(
                        [
                            ft.ElevatedButton(self.t("no"), on_click=self._confirm_new_list_false, height=48, expand=1, style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_200 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.GREY_700, shape=ft.RoundedRectangleBorder(radius=14))),
                            ft.ElevatedButton(self.t("yes"), on_click=self._confirm_new_list_true, height=48, expand=1, style=ft.ButtonStyle(bgcolor=ft.Colors.RED_100 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.RED_900, shape=ft.RoundedRectangleBorder(radius=14))),
                        ],
                        spacing=12,
                    ),
                ],
                spacing=16,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        self.page.update()
        log("confirm view shown")

    def _confirm_new_list_false(self, e):
        log("confirm_new_list_false")
        self.build_main_view()

    def _confirm_new_list_true(self, e):
        log("confirm_new_list_true")
        self._lists[self._active_list_id] = []
        self.save_data()
        self.build_main_view()
        self.page.update()

    def edit_list(self, e):
        self.editing = not self.editing
        if self.editing:
            self._expanded_groups = set(range(len(self._current_list())))
        else:
            self._expanded_groups.clear()
        self._refresh_list()

    def finish_edit(self, e):
        if self._save_timer:
            self._save_timer.cancel()
            self._save_timer = None
        self.save_data()
        self.editing = False
        self._refresh_list()

    def show_input_view(self):
        log("show_input_view start")
        try:
            self.page.clean()
            compact = self._compact()

            field_height = self._ui(48, 44)
            field_text_size = self._ui(15, 13)
            border_radius = self._ui(14, 12)
            btn_height = self._ui(48, 44)
            card_spacing = self._ui(10, 8)
            card_padding = self._ui(16, 12)
            title_size = self._ui(18, 16)

            self.name_field = ft.TextField(label=self.t("name"), expand=True, height=field_height, text_size=field_text_size, on_change=self.on_name_change, border_radius=border_radius)
            self.product_field = ft.TextField(label=self.t("product"), expand=True, on_change=self.on_product_change, height=field_height, text_size=field_text_size, border_radius=border_radius)
            self.price_field = ft.TextField(label=self.t("price"), expand=True, keyboard_type=ft.KeyboardType.NUMBER, height=field_height, text_size=field_text_size, border_radius=border_radius)
            self.quantity_field = ft.TextField(label=self.t("quantity"), value="1", expand=True, keyboard_type=ft.KeyboardType.NUMBER, height=field_height, text_size=field_text_size, border_radius=border_radius)

            self.name_suggestion_list = ft.Column(spacing=self._ui(4, 3), visible=False)
            self.product_suggestion_list = ft.Column(spacing=self._ui(4, 3), visible=False)

            input_card = ft.Column(
                [
                    ft.Text(self.t("new_entry"), size=title_size, weight=ft.FontWeight.BOLD),
                    self.name_field,
                    self.name_suggestion_list,
                    self.product_field,
                    self.product_suggestion_list,
                    ft.Row([self.price_field, self.quantity_field], spacing=self._ui(8, 6), expand=True),
                    ft.Row(
                        [
                            ft.ElevatedButton(self.t("continue"), on_click=self.on_continue, height=btn_height, expand=1, style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_100 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_700, shape=ft.RoundedRectangleBorder(radius=border_radius))),
                            ft.ElevatedButton(self.t("new_person"), on_click=self.on_new_person, height=btn_height, expand=1, style=ft.ButtonStyle(bgcolor=ft.Colors.PURPLE_100 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.PURPLE_900, shape=ft.RoundedRectangleBorder(radius=border_radius))),
                        ],
                        spacing=self._ui(8, 6),
                    ),
                    ft.ElevatedButton(self.t("finish"), on_click=self.on_finish, height=btn_height, expand=1, style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_100 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.GREEN_900, shape=ft.RoundedRectangleBorder(radius=border_radius))),
                ],
                spacing=card_spacing,
                expand=True,
            )

            input_wrapper = ft.Container(
                content=input_card,
                padding=card_padding,
                border_radius=self._ui(16, 12),
                bgcolor=ft.Colors.BLUE_GREY_50 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_900,
                border=ft.Border(left=ft.BorderSide(1, ft.Colors.BLUE_GREY_200 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_700), top=ft.BorderSide(1, ft.Colors.BLUE_GREY_200 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_700), right=ft.BorderSide(1, ft.Colors.BLUE_GREY_200 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_700), bottom=ft.BorderSide(1, ft.Colors.BLUE_GREY_200 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_700)),
            )

            self.page.add(input_wrapper)
            self.page.update()
            log("show_input_view end")
        except Exception:
            log(f"show_input_view error: {traceback.format_exc()}")

    def on_name_change(self, e):
        value = self.name_field.value.strip()
        if not value:
            self.name_suggestion_list.visible = False
            self.name_suggestion_list.controls = []
            self.page.update()
            return

        matches = [p for p in self.people if p.lower().startswith(value.lower())]
        if matches:
            suggestion_bg = ft.Colors.BLUE_50 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_800
            text_color = ft.Colors.BLUE_GREY_900 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_100
            self.name_suggestion_list.controls = [
                ft.Container(
                    content=ft.Text(p, size=self._ui(14, 12), color=text_color),
                    padding=self._ui(12, 10),
                    border_radius=self._ui(10, 8),
                    bgcolor=suggestion_bg,
                    on_click=lambda e, p=p: self.select_name(p),
                )
                for p in matches
            ]
            self.name_suggestion_list.visible = True
        else:
            self.name_suggestion_list.visible = False
            self.name_suggestion_list.controls = []
        self.page.update()

    def select_name(self, name):
        try:
            self.name_field.value = name
            self.name_suggestion_list.visible = False
            self.name_suggestion_list.controls = []
            self.page.update()
        except Exception:
            log(f"select_name error: {traceback.format_exc()}")

    def on_product_change(self, e):
        value = self.product_field.value.strip()
        if not value:
            self.product_suggestion_list.visible = False
            self.product_suggestion_list.controls = []
            self.page.update()
            return

        matches = [p for p in self.products if p["name"].lower().startswith(value.lower())]
        if matches:
            suggestion_bg = ft.Colors.BLUE_50 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_800
            text_color = ft.Colors.BLUE_GREY_900 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_100
            self.product_suggestion_list.controls = [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(p["name"], size=self._ui(14, 12), expand=1, color=text_color),
                            ft.Text(f"{p['price']:.2f} €", size=self._ui(14, 12), color=text_color),
                        ],
                        spacing=self._ui(8, 6),
                    ),
                    padding=self._ui(12, 10),
                    border_radius=self._ui(10, 8),
                    bgcolor=suggestion_bg,
                    on_click=lambda e, p=p: self.select_product(p),
                )
                for p in matches
            ]
            self.product_suggestion_list.visible = True
        else:
            self.product_suggestion_list.visible = False
            self.product_suggestion_list.controls = []
        self.page.update()

    def select_product(self, product):
        try:
            self.product_field.value = product["name"]
            self.price_field.value = f"{product['price']:.2f}"
            self.product_suggestion_list.visible = False
            self.product_suggestion_list.controls = []
            self.page.update()
        except Exception:
            log(f"select_product error: {traceback.format_exc()}")

    def on_continue(self, e):
        log("on_continue start")
        try:
            if not self.validate_entry():
                return
            try:
                quantity = int(self.quantity_field.value.replace(",", "."))
            except ValueError:
                quantity = 1
            entry = {
                "product": self.product_field.value.strip(),
                "price": self._normalize_entry_price(self.price_field.value, quantity),
                "quantity": max(1, quantity),
                "paid": False,
            }
            name = self.name_field.value.strip()
            existing = next((g for g in self._current_list() if g["name"] == name), None)
            if existing:
                existing["items"].append(entry)
            else:
                self._current_list().append({"name": name, "items": [entry]})
            if self.settings.get("auto_add_persons", True) and name not in self.people:
                self.people.append(name)
            self._ensure_product_in_catalog(entry["product"], entry["price"])
            self.save_data()
            self.product_field.value = ""
            self.price_field.value = ""
            self.quantity_field.value = "1"
            self.product_field.error_text = ""
            self.price_field.error_text = ""
            self.quantity_field.error_text = ""
            self.product_suggestion_list.visible = False
            self.product_suggestion_list.controls = []
            self.page.update()
            log("on_continue end")
        except Exception:
            log(f"on_continue error: {traceback.format_exc()}")

    def on_new_person(self, e):
        log("on_new_person start")
        try:
            if self.name_field.value.strip():
                if not self.validate_entry():
                    return
                try:
                    quantity = int(self.quantity_field.value.replace(",", "."))
                except ValueError:
                    quantity = 1
                entry = {
                    "product": self.product_field.value.strip(),
                    "price": self._normalize_entry_price(self.price_field.value, quantity),
                    "quantity": max(1, quantity),
                    "paid": False,
                }
                name = self.name_field.value.strip()
                existing = next((g for g in self._current_list() if g["name"] == name), None)
                if existing:
                    existing["items"].append(entry)
                else:
                    self._current_list().append({"name": name, "items": [entry]})
                if self.settings.get("auto_add_persons", True) and name not in self.people:
                    self.people.append(name)
                self._ensure_product_in_catalog(entry["product"], entry["price"])
                self.save_data()
            self.name_field.value = ""
            self.product_field.value = ""
            self.price_field.value = ""
            self.quantity_field.value = "1"
            self.name_field.error_text = ""
            self.product_field.error_text = ""
            self.price_field.error_text = ""
            self.quantity_field.error_text = ""
            self.name_suggestion_list.visible = False
            self.name_suggestion_list.controls = []
            self.product_suggestion_list.visible = False
            self.product_suggestion_list.controls = []
            self.page.update()
            log("on_new_person end")
        except Exception:
            log(f"on_new_person error: {traceback.format_exc()}")

    def on_finish(self, e):
        log("on_finish start")
        try:
            if self.validate_entry():
                try:
                    quantity = int(self.quantity_field.value.replace(",", "."))
                except ValueError:
                    quantity = 1
                entry = {
                    "product": self.product_field.value.strip(),
                    "price": self._normalize_entry_price(self.price_field.value, quantity),
                    "quantity": max(1, quantity),
                    "paid": False,
                }
                name = self.name_field.value.strip()
                existing = next((g for g in self._current_list() if g["name"] == name), None)
                if existing:
                    existing["items"].append(entry)
                else:
                    self._current_list().append({"name": name, "items": [entry]})
                if self.settings.get("auto_add_persons", True) and name not in self.people:
                    self.people.append(name)
                self._ensure_product_in_catalog(entry["product"], entry["price"])
                self.save_data()
            self.build_main_view()
            self.page.update()
            log("on_finish end")
        except Exception:
            log(f"on_finish error: {traceback.format_exc()}")

    def validate_entry(self):
        try:
            if not self.name_field.value.strip():
                self.name_field.error_text = self.t("name_required")
                self.page.update()
                return False
            if not self.product_field.value.strip():
                self.product_field.error_text = self.t("product_required")
                self.page.update()
                return False
            if not self.price_field.value.strip():
                self.price_field.error_text = self.t("price_required")
                self.page.update()
                return False
            try:
                float(self.price_field.value.replace(",", "."))
            except ValueError:
                self.price_field.error_text = self.t("invalid_price")
                self.page.update()
                return False
            try:
                q = int(self.quantity_field.value.replace(",", "."))
                if q < 1:
                    raise ValueError
            except ValueError:
                self.quantity_field.error_text = self.t("quantity_min")
                self.quantity_field.value = "1"
                self.page.update()
                return False
            return True
        except Exception:
            log(f"validate_entry error: {traceback.format_exc()}")
            return False

    def add_product_dialog(self, e):
        log("open produkt verwalten")
        try:
            self.show_manager_view(self.t("product_management"), self.products, "produkt")
        except Exception:
            log(f"add_product_dialog error: {traceback.format_exc()}")

    def add_person_dialog(self, e):
        log("open person verwalten")
        try:
            self.show_manager_view(self.t("person_management"), self.people, "person")
        except Exception:
            log(f"add_person_dialog error: {traceback.format_exc()}")

    def show_manager_view(self, title, items, item_type):
        log(f"show_manager_view {title} start")
        try:
            self.page.clean()
            compact = self._compact()
            self.manager_view_active = True

            self.manager_item_type = item_type
            self.manager_items = list(items)

            header = ft.Row(
                [
                    ft.IconButton(icon=ft.icons.Icons.CLOSE, on_click=self._manager_close, tooltip=self.t("close"), icon_size=self._ui(20, 18)),
                    ft.Text(title, size=self._ui(18, 16), weight=ft.FontWeight.BOLD),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )

            self.manager_list = ft.Column(spacing=self._ui(6, 4), scroll=ft.ScrollMode.AUTO, expand=True)
            self.manager_input_name = ft.TextField(label=self.t("name"), expand=True, height=self._ui(48, 44), text_size=self._ui(15, 13), border_radius=self._ui(14, 12))
            if item_type == "produkt":
                self.manager_input_price = ft.TextField(label=self.t("price"), expand=True, height=self._ui(48, 44), text_size=self._ui(15, 13), keyboard_type=ft.KeyboardType.NUMBER, border_radius=self._ui(14, 12))

            add_btn = ft.ElevatedButton(self.t("add"), on_click=self._manager_add, height=self._ui(48, 44), style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_100 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_700, shape=ft.RoundedRectangleBorder(radius=self._ui(14, 12))))
            if item_type == "produkt":
                input_row = ft.Row([self.manager_input_name, self.manager_input_price], spacing=self._ui(8, 6))
                input_card = ft.Column([input_row, add_btn], spacing=self._ui(8, 6))
            else:
                input_row = ft.Row([self.manager_input_name])
                input_card = ft.Column([input_row, add_btn], spacing=self._ui(8, 6))

            main_col = ft.Column(
                [
                    header,
                    ft.Divider(),
                    ft.Container(content=self.manager_list, expand=True),
                    ft.Divider(),
                    input_card,
                ],
                spacing=self._ui(12, 8),
                expand=True,
            )

            self.page.add(main_col)
            self._refresh_manager_list()
            self.page.update()
            log("show_manager_view end")
        except Exception:
            log(f"show_manager_view error: {traceback.format_exc()}")
            raise

    def _manager_close(self, e):
        log("manager close")
        self.manager_view_active = False
        self.save_data()
        if self._manager_from_settings:
            self._manager_from_settings = False
            self.show_settings()
        else:
            self.build_main_view()

    def _open_manager_from_settings(self, item_type):
        self._manager_from_settings = True
        if item_type == "produkt":
            self.show_manager_view(self.t("product_management"), self.products, "produkt")
        else:
            self.show_manager_view(self.t("person_management"), self.people, "person")

    def _refresh_manager_list(self):
        log(f"_refresh_manager_list start, count={len(self.manager_items)}")
        try:
            self.manager_list.controls = []
            source = self.products if self.manager_item_type == "produkt" else self.people
            for idx, item in enumerate(source):
                if self.manager_item_type == "produkt":
                    row = ft.Row(
                        [
                            ft.Text(item.get("name", ""), expand=1, size=14),
                            ft.Text(f"{item.get('price', 0):.2f} €", size=14),
                            ft.IconButton(icon=ft.icons.Icons.DELETE, icon_color=ft.Colors.RED, icon_size=18, on_click=lambda e, i=idx: self._manager_delete(i)),
                        ],
                        spacing=6,
                    )
                else:
                    row = ft.Row(
                        [
                            ft.Text(item, expand=1, size=14),
                            ft.IconButton(icon=ft.icons.Icons.DELETE, icon_color=ft.Colors.RED, icon_size=18, on_click=lambda e, i=idx: self._manager_delete(i)),
                        ],
                        spacing=6,
                    )
                container = ft.Container(content=row, padding=12, border_radius=10, bgcolor=ft.Colors.BLUE_GREY_50 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_900)
                self.manager_list.controls.append(container)
            log("_refresh_manager_list end")
        except Exception:
            log(f"_refresh_manager_list error: {traceback.format_exc()}")

    def _manager_add(self, e):
        log("_manager_add start")
        try:
            name = self.manager_input_name.value.strip()
            if not name:
                return

            if self.manager_item_type == "produkt":
                try:
                    price = float(self.manager_input_price.value.replace(",", "."))
                except ValueError:
                    return
                self.products.append({"name": name, "price": price})
                self.manager_input_price.value = ""
            else:
                if self.settings.get("auto_add_persons", True) and name not in self.people:
                    self.people.append(name)

            self.manager_input_name.value = ""
            self.save_data()
            self._refresh_manager_list()
            self.page.update()
            log("_manager_add end")
        except Exception:
            log(f"_manager_add error: {traceback.format_exc()}")

    def _manager_delete(self, idx):
        log(f"_manager_delete {idx} start")
        try:
            if self.manager_item_type == "produkt":
                if 0 <= idx < len(self.products):
                    self.products.pop(idx)
            else:
                if 0 <= idx < len(self.people):
                    self.people.pop(idx)
            self.save_data()
            self._refresh_manager_list()
            self.page.update()
            log(f"_manager_delete {idx} end")
        except Exception:
            log(f"_manager_delete error: {traceback.format_exc()}")

    def _manager_save(self, e):
        log("_manager_save")
        try:
            self.save_data()
            self.manager_view_active = False
            self.build_main_view()
        except Exception:
            log(f"_manager_save error: {traceback.format_exc()}")


def main():
    log("=== APP START ===")
    try:
        ft.run(CBREBreakApp)
    except Exception:
        log(f"main error: {traceback.format_exc()}")


if __name__ == "__main__":
    main()

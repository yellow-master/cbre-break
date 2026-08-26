import flet as ft
import json
import os
import threading
import traceback

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "cbre_break_data.json")
LOG_FILE = os.path.join(SCRIPT_DIR, "cbre_break_log.txt")


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
        self.current_list = []
        self.settings = {"theme_mode": "light"}
        self.editing = False
        self._list_control = None
        self._total_label = None
        self._expanded_groups = set()
        self._save_timer = None

        self.show_loading()
        self.page.update()
        self.load_data()
        self.apply_theme()
        self.build_main_view()

    def load_data(self):
        log("load_data start")
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
                    self.products = data.get("products", [])
                    self.people = data.get("people", [])
                    self.current_list = data.get("current_list", [])
                    self.settings = data.get("settings", {"theme_mode": "light"})
                    if self._is_flat_list(self.current_list):
                        self.current_list = self._migrate_to_grouped(self.current_list)
            log("load_data end")
        except Exception:
            log(f"load_data error: {traceback.format_exc()}")

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
                    "current_list": self.current_list,
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
        self.page.update()

    def show_loading(self):
        self.page.clean()
        self.page.add(
            ft.Column(
                [
                    ft.ProgressRing(width=40, height=40, stroke_width=4),
                    ft.Text("Lade...", size=16),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

    def build_main_view(self):
        log("build_main_view start")
        try:
            self.page.clean()

            header = ft.Row(
                [
                    ft.IconButton(icon=ft.icons.Icons.EDIT, on_click=self.edit_list, tooltip="Bearbeiten", icon_size=20),
                    ft.IconButton(icon=ft.icons.Icons.ADD, on_click=self.show_input_view, tooltip="Eintrag hinzufügen", icon_size=20),
                ],
                spacing=4,
            )

            top_right = ft.Row(
                [
                    ft.IconButton(icon=ft.icons.Icons.INVENTORY_2, on_click=self.add_product_dialog, tooltip="Produkte", icon_size=20),
                    ft.IconButton(icon=ft.icons.Icons.PEOPLE, on_click=self.add_person_dialog, tooltip="Personen", icon_size=20),
                ],
                spacing=4,
            )

            title_row = ft.Row(
                [
                    ft.Text("CBRE Break", size=18, weight=ft.FontWeight.BOLD, expand=1),
                    top_right,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )

            header_col = ft.Column([header, title_row], spacing=4)

            self._list_control = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)

            if not self.current_list:
                self._list_control.controls.append(
                    ft.Container(
                        content=ft.Text("Keine Einträge vorhanden.", size=14, text_align=ft.TextAlign.CENTER),
                        padding=16,
                    )
                )
            else:
                for idx, group in enumerate(self.current_list):
                    self._list_control.controls.append(self._build_group_card(group, idx))

            total = 0
            for group in self.current_list:
                for item in group.get("items", []):
                    if not item.get("paid", False):
                        total += item.get("price", 0) * item.get("quantity", 1)

            self._total_label = ft.Text(f"Gesamtpreis: {total:.2f} €", size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.END, expand=1)

            bottom_row = ft.Row(
                [
                    ft.IconButton(
                        icon=ft.icons.Icons.WB_SUNNY if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.icons.Icons.NIGHTLIGHT,
                        on_click=self.toggle_theme,
                        tooltip="Dark Mode",
                        icon_size=22,
                    ),
                ],
            )

            self.page.add(
                ft.Column(
                    [
                        header_col,
                        ft.Divider(height=1),
                        ft.Container(content=self._list_control, expand=True),
                        ft.Divider(height=1),
                        ft.Row([self._total_label], alignment=ft.MainAxisAlignment.END),
                        bottom_row,
                    ],
                    spacing=8,
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

        name_row = ft.Row(
            [
                ft.IconButton(icon=expand_icon, on_click=lambda e, i=idx: self.toggle_group_expand(i), icon_size=18, tooltip="Aufklappen"),
                ft.Text(name, size=15, weight=ft.FontWeight.BOLD, expand=1),
                ft.Text(f"{group_total:.2f} €", size=14, text_align=ft.TextAlign.END),
                ft.Text("bezahlt" if group_paid else "offen", size=11, color=ft.Colors.GREEN_600 if group_paid else ft.Colors.ORANGE_600),
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
                                ft.TextField(value=product, label="Produkt", text_size=13, height=40, on_change=self._make_item_field_changer(group, item_idx, "product")),
                                ft.Row(
                                    [
                                        ft.TextField(value=str(price), label="Preis", text_size=13, height=40, keyboard_type=ft.KeyboardType.NUMBER, on_change=self._make_item_field_changer(group, item_idx, "price"), expand=1),
                                        ft.TextField(value=str(quantity), label="Menge", text_size=13, height=40, keyboard_type=ft.KeyboardType.NUMBER, on_change=self._make_item_field_changer(group, item_idx, "quantity"), width=70),
                                        ft.Checkbox(value=paid, on_change=lambda e, g=group, i=item_idx: self.toggle_item_paid(g, i, e.control.value)),
                                        ft.IconButton(icon=ft.icons.Icons.DELETE, icon_color=ft.Colors.RED, icon_size=18, on_click=lambda e, g=group, i=item_idx: self.delete_item(g, i)),
                                    ],
                                    spacing=4,
                                ),
                            ],
                            spacing=4,
                        ),
                        padding=6,
                        border_radius=6,
                    )
                    item_controls.append(item_card)

                add_btn = ft.ElevatedButton(
                    "Produkt hinzufügen",
                    icon=ft.icons.Icons.ADD,
                    on_click=lambda e, g=group: self.add_item_to_group(g),
                    height=40,
                    style=ft.ButtonStyle(padding=8),
                )
                content = ft.Column(item_controls + [add_btn], spacing=4)
                card = ft.Container(content=content, padding=8, border_radius=8, bgcolor=ft.Colors.BLUE_50 if self.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_GREY_900)
            else:
                item_rows = []
                for item in items:
                    product = item.get("product", "")
                    price = item.get("price", 0)
                    quantity = item.get("quantity", 1)
                    paid = item.get("paid", False)
                    line_total = price * quantity

                    row = ft.Row(
                        [
                            ft.Checkbox(value=paid, disabled=True, check_color=ft.Colors.GREEN_600),
                            ft.Text(f"{quantity}x {product}", expand=1, size=13),
                            ft.Text(f"{line_total:.2f} €", size=13, text_align=ft.TextAlign.END),
                        ],
                        spacing=6,
                    )
                    item_rows.append(row)

                content = ft.Column(item_rows, spacing=2)
                opacity_val = 0.5 if group_paid else 1.0
                card = ft.Container(
                    content=content,
                    padding=6,
                    border_radius=8,
                    opacity=opacity_val,
                    on_click=lambda e, g=group: self.toggle_group_paid(g),
                    ink=True,
                )
        else:
            content = ft.Container(padding=ft.Padding(left=36, top=0, right=0, bottom=0))
            card = ft.Container(content=content, padding=6, border_radius=8)

        return ft.Container(content=ft.Column([name_row, ft.Divider(height=1, color=ft.Colors.TRANSPARENT), card], spacing=4), padding=8, border_radius=10)

    def toggle_group_expand(self, idx):
        if idx in self._expanded_groups:
            self._expanded_groups.discard(idx)
        else:
            self._expanded_groups.add(idx)
        self._refresh_list()

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
            if not self.current_list:
                self._list_control.controls.append(
                    ft.Container(
                        content=ft.Text("Keine Einträge vorhanden.", size=14, text_align=ft.TextAlign.CENTER),
                        padding=16,
                    )
                )
            else:
                for idx, group in enumerate(self.current_list):
                    self._list_control.controls.append(self._build_group_card(group, idx))
            self._sort_current_list()
            self._update_total()
            self.page.update()

    def _group_sort_key(self, group):
        try:
            unpaid = sum(item.get("price", 0) * item.get("quantity", 1) for item in group.get("items", []) if not item.get("paid", False))
            return -unpaid
        except Exception:
            return 0

    def _sort_current_list(self):
        self.current_list.sort(key=self._group_sort_key)

    def _update_total(self):
        if not self._total_label:
            return
        total = 0
        for group in self.current_list:
            for item in group.get("items", []):
                if not item.get("paid", False):
                    total += item.get("price", 0) * item.get("quantity", 1)
        self._total_label.value = f"Gesamtpreis: {total:.2f} €"

    def toggle_group_paid(self, group):
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
                    if group in self.current_list:
                        self.current_list.remove(group)
                self.save_data()
                self._refresh_list()
        except Exception:
            log(f"delete_item error: {traceback.format_exc()}")

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
                    ft.Text("Neue Liste", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text("Alte Liste löschen? Personen und Produkte bleiben erhalten."),
                    ft.Row(
                        [
                            ft.ElevatedButton("Nein", on_click=self._confirm_new_list_false, height=44, expand=1),
                            ft.ElevatedButton("Ja", on_click=self._confirm_new_list_true, height=44, expand=1),
                        ],
                        spacing=8,
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
        self.current_list = []
        self.save_data()
        self.build_main_view()
        self.page.update()

    def edit_list(self, e):
        self.editing = not self.editing
        if self.editing:
            self._expanded_groups = set(range(len(self.current_list)))
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

            self.name_field = ft.TextField(label="Name", expand=True, height=44, text_size=15, on_change=self.on_name_change)
            self.product_field = ft.TextField(label="Produkt", expand=True, on_change=self.on_product_change, height=44, text_size=15)
            self.price_field = ft.TextField(label="Preis", expand=True, keyboard_type=ft.KeyboardType.NUMBER, height=44, text_size=15)
            self.quantity_field = ft.TextField(label="Menge", value="1", expand=True, keyboard_type=ft.KeyboardType.NUMBER, height=44, text_size=15)

            self.name_suggestion_list = ft.Column(spacing=2, visible=False)
            self.product_suggestion_list = ft.Column(spacing=2, visible=False)

            input_card = ft.Column(
                [
                    ft.Text("Neuer Eintrag", size=18, weight=ft.FontWeight.BOLD),
                    self.name_field,
                    self.name_suggestion_list,
                    self.product_field,
                    self.product_suggestion_list,
                    ft.Row([self.price_field, self.quantity_field], spacing=6),
                    ft.Row(
                        [
                            ft.ElevatedButton("Weiterer Artikel", on_click=self.on_continue, height=44, expand=1),
                            ft.ElevatedButton("Neue Person", on_click=self.on_new_person, height=44, expand=1),
                        ],
                        spacing=6,
                    ),
                    ft.ElevatedButton("Fertig", on_click=self.on_finish, height=44, expand=1),
                ],
                spacing=6,
                width=360,
            )

            self.page.add(
                ft.Row([input_card], alignment=ft.MainAxisAlignment.CENTER),
            )
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
            self.name_suggestion_list.controls = [
                ft.Container(
                    content=ft.Text(p, size=14),
                    padding=10,
                    border_radius=6,
                    bgcolor=ft.Colors.BLUE_50,
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
            self.product_suggestion_list.controls = [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(p["name"], size=14, expand=1),
                            ft.Text(f"{p['price']:.2f} €", size=14),
                        ],
                        spacing=6,
                    ),
                    padding=10,
                    border_radius=6,
                    bgcolor=ft.Colors.BLUE_50,
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
            existing = next((g for g in self.current_list if g["name"] == name), None)
            if existing:
                existing["items"].append(entry)
            else:
                self.current_list.append({"name": name, "items": [entry]})
            if name not in self.people:
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
                existing = next((g for g in self.current_list if g["name"] == name), None)
                if existing:
                    existing["items"].append(entry)
                else:
                    self.current_list.append({"name": name, "items": [entry]})
                if name not in self.people:
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
                existing = next((g for g in self.current_list if g["name"] == name), None)
                if existing:
                    existing["items"].append(entry)
                else:
                    self.current_list.append({"name": name, "items": [entry]})
                if name not in self.people:
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
                self.name_field.error_text = "Name erforderlich"
                self.page.update()
                return False
            if not self.product_field.value.strip():
                self.product_field.error_text = "Produkt erforderlich"
                self.page.update()
                return False
            if not self.price_field.value.strip():
                self.price_field.error_text = "Preis erforderlich"
                self.page.update()
                return False
            try:
                float(self.price_field.value.replace(",", "."))
            except ValueError:
                self.price_field.error_text = "Ungültiger Preis"
                self.page.update()
                return False
            try:
                q = int(self.quantity_field.value.replace(",", "."))
                if q < 1:
                    raise ValueError
            except ValueError:
                self.quantity_field.error_text = "Menge muss >= 1 sein"
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
            self.show_manager_view("Produkt verwalten", self.products, "produkt")
        except Exception:
            log(f"add_product_dialog error: {traceback.format_exc()}")

    def add_person_dialog(self, e):
        log("open person verwalten")
        try:
            self.show_manager_view("Person verwalten", self.people, "person")
        except Exception:
            log(f"add_person_dialog error: {traceback.format_exc()}")

    def show_manager_view(self, title, items, item_type):
        log(f"show_manager_view {title} start")
        try:
            self.page.clean()
            self.manager_view_active = True

            self.manager_item_type = item_type
            self.manager_items = list(items)

            header = ft.Row(
                [
                    ft.IconButton(icon=ft.icons.Icons.CLOSE, on_click=self._manager_close, tooltip="Schließen", icon_size=20),
                    ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )

            self.manager_list = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO, expand=True)
            self.manager_input_name = ft.TextField(label="Name", expand=True, height=44, text_size=15)
            if item_type == "produkt":
                self.manager_input_price = ft.TextField(label="Preis", expand=True, height=44, text_size=15, keyboard_type=ft.KeyboardType.NUMBER)

            add_btn = ft.ElevatedButton("Hinzufügen", on_click=self._manager_add, height=44)
            if item_type == "produkt":
                input_row = ft.Row([self.manager_input_name, self.manager_input_price], spacing=6)
                input_card = ft.Column([input_row, add_btn], spacing=6)
            else:
                input_row = ft.Row([self.manager_input_name])
                input_card = ft.Column([input_row, add_btn], spacing=6)

            main_col = ft.Column(
                [
                    header,
                    ft.Divider(),
                    ft.Container(content=self.manager_list, expand=True),
                    ft.Divider(),
                    input_card,
                ],
                spacing=8,
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
        self.build_main_view()

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
                container = ft.Container(content=row, padding=10, border_radius=6)
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
                if name not in self.people:
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

import flet as ft
import json
import os
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
        self.editing = False

        self.show_loading()
        self.page.update()
        self.load_data()
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
            log("load_data end")
        except Exception:
            log(f"load_data error: {traceback.format_exc()}")

    def save_data(self):
        log("save_data start")
        try:
            with open(DATA_FILE, "w") as f:
                json.dump({
                    "products": self.products,
                    "people": self.people,
                    "current_list": self.current_list
                }, f, indent=2)
            log("save_data end")
        except Exception:
            log(f"save_data error: {traceback.format_exc()}")

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

            app_bar = ft.Row(
                [
                    ft.Button("Bearbeiten", on_click=self.edit_list, height=44, expand=1),
                    ft.Button("Neue Liste", on_click=self.new_option, height=44, expand=1),
                ],
                alignment=ft.MainAxisAlignment.START,
            )

            top_right = ft.Row(
                [
                    ft.Button("Produkt verwalten", on_click=self.add_product_dialog, height=40),
                    ft.Button("Person verwalten", on_click=self.add_person_dialog, height=40),
                ],
                alignment=ft.MainAxisAlignment.END,
            )

            header = ft.Row([app_bar, top_right], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

            self.list_view = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)

            if not self.current_list:
                self.list_view.controls.append(ft.Text("Keine Einträge vorhanden.", size=16))
            else:
                for idx, entry in enumerate(self.current_list):
                    paid = entry.get("paid", False)
                    quantity = entry.get("quantity", 1)
                    product_text = entry.get("product", "")
                    if quantity > 1:
                        product_text = f"{quantity}x {product_text}"
                    if self.editing:
                        row = ft.Row(
                            [
                                ft.Checkbox(value=paid, on_change=lambda e, i=idx: self.toggle_paid(i, e.control.value)),
                                ft.TextField(value=entry.get("name", ""), expand=1, text_size=14, height=44, on_change=self._make_field_changer(idx, "name")),
                                ft.TextField(value=entry.get("product", ""), expand=1, text_size=14, height=44, on_change=self._make_field_changer(idx, "product")),
                                ft.TextField(value=str(entry.get("price", 0)), expand=1, text_size=14, height=44, keyboard_type=ft.KeyboardType.NUMBER, on_change=self._make_field_changer(idx, "price")),
                                ft.TextField(value=str(quantity), width=70, text_size=14, height=44, keyboard_type=ft.KeyboardType.NUMBER, on_change=self._make_field_changer(idx, "quantity")),
                                ft.IconButton(icon=ft.icons.Icons.DELETE, icon_color=ft.Colors.RED, on_click=lambda e, i=idx: self.delete_entry(i)),
                            ],
                            spacing=6,
                        )
                    else:
                        row = ft.Row(
                            [
                                ft.Checkbox(value=paid, disabled=True),
                                ft.Text(entry.get("name", ""), expand=1, size=16),
                                ft.Text(product_text, expand=1, size=16),
                                ft.Text(f"{entry.get('price', 0) * quantity:.2f} €", expand=1, size=16),
                            ],
                            spacing=10,
                        )
                    if paid and not self.editing:
                        row.opacity = 0.4
                    if self.editing:
                        container = ft.Container(content=row, padding=8, border_radius=8)
                    else:
                        container = ft.Container(content=row, padding=8, border_radius=8, on_click=lambda e, i=idx: self.toggle_paid(i))
                    self.list_view.controls.append(container)

            total = sum(entry.get("price", 0) * entry.get("quantity", 1) for entry in self.current_list if not entry.get("paid", False))
            total_row = ft.Row(
                [
                    ft.Text("Gesamtpreis:", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(f"{total:.2f} €", size=18, weight=ft.FontWeight.BOLD),
                ],
                alignment=ft.MainAxisAlignment.END,
            )

            if self.editing:
                bottom_row = ft.Row(
                    [
                        ft.Button("Fertig", on_click=self.finish_edit, height=50, expand=1),
                    ],
                )
            else:
                bottom_row = ft.Row(
                    [
                        ft.Button("Eintrag hinzufügen", on_click=self.show_input_view, height=50, expand=1),
                    ],
                )

            self.page.add(header, ft.Divider(), self.list_view, ft.Divider(), total_row, bottom_row, ft.Text("Made by M.M", size=12, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER, expand=True))
            log("build_main_view end")
        except Exception:
            log(f"build_main_view error: {traceback.format_exc()}")
            raise

    def _make_field_changer(self, idx, field):
        def changer(e):
            try:
                if field == "price":
                    self.current_list[idx][field] = float(e.control.value.replace(",", "."))
                elif field == "quantity":
                    val = int(e.control.value.replace(",", "."))
                    self.current_list[idx][field] = max(1, val)
                else:
                    self.current_list[idx][field] = e.control.value.strip()
                self.save_data()
            except ValueError:
                pass
        return changer

    def toggle_paid(self, idx, paid=None):
        log(f"toggle_paid {idx} current={self.current_list[idx].get('paid', False)}")
        try:
            if paid is None:
                self.current_list[idx]["paid"] = not self.current_list[idx].get("paid", False)
            else:
                self.current_list[idx]["paid"] = paid
            self.save_data()
            self.build_main_view()
            self.page.update()
        except Exception:
            log(f"toggle_paid error: {traceback.format_exc()}")

    def delete_entry(self, idx):
        log(f"delete_entry {idx}")
        try:
            if 0 <= idx < len(self.current_list):
                self.current_list.pop(idx)
                self.save_data()
                self.build_main_view()
                self.page.update()
        except Exception:
            log(f"delete_entry error: {traceback.format_exc()}")

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
                    ft.Text("Neue Liste", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text("Alte Liste löschen? Personen und Produkte bleiben erhalten."),
                    ft.Row(
                        [
                            ft.Button("Nein", on_click=self._confirm_new_list_false, height=44, expand=1),
                            ft.Button("Ja", on_click=self._confirm_new_list_true, height=44, expand=1),
                        ],
                        spacing=10,
                    ),
                ],
                spacing=20,
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
        self.editing = True
        self.build_main_view()
        self.page.update()

    def finish_edit(self, e):
        self.editing = False
        self.build_main_view()
        self.page.update()

    def show_input_view(self):
        log("show_input_view start")
        try:
            self.page.clean()

            self.name_field = ft.TextField(label="Name", expand=True, height=50, text_size=16, on_change=self.on_name_change)
            self.product_field = ft.TextField(label="Produkt", expand=True, on_change=self.on_product_change, height=50, text_size=16)
            self.price_field = ft.TextField(label="Preis", expand=True, keyboard_type=ft.KeyboardType.NUMBER, height=50, text_size=16)
            self.quantity_field = ft.TextField(label="Menge", value="1", expand=True, keyboard_type=ft.KeyboardType.NUMBER, height=50, text_size=16)

            self.name_suggestion_list = ft.Column(spacing=4, visible=False)
            self.product_suggestion_list = ft.Column(spacing=4, visible=False)

            input_card = ft.Column(
                [
                    ft.Text("Neuer Eintrag", size=20, weight=ft.FontWeight.BOLD),
                    self.name_field,
                    self.name_suggestion_list,
                    self.product_field,
                    self.product_suggestion_list,
                    ft.Row([self.price_field, self.quantity_field], spacing=10),
                    ft.Row(
                        [
                            ft.Button("Weiter", on_click=self.on_continue, height=50, expand=1),
                            ft.Button("Fertig", on_click=self.on_finish, height=50, expand=1),
                        ],
                    ),
                ],
                spacing=10,
                width=350,
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
                    content=ft.Text(p, size=16),
                    padding=12,
                    border_radius=8,
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
                            ft.Text(p["name"], size=16, expand=1),
                            ft.Text(f"{p['price']:.2f} €", size=16),
                        ],
                        spacing=10,
                    ),
                    padding=12,
                    border_radius=8,
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
                "name": self.name_field.value.strip(),
                "product": self.product_field.value.strip(),
                "price": float(self.price_field.value.replace(",", ".")),
                "quantity": max(1, quantity),
                "paid": False,
            }
            self.current_list.append(entry)
            if entry["name"] not in self.people:
                self.people.append(entry["name"])
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
            log("on_continue end")
        except Exception:
            log(f"on_continue error: {traceback.format_exc()}")

    def on_finish(self, e):
        log("on_finish start")
        try:
            if self.validate_entry():
                try:
                    quantity = int(self.quantity_field.value.replace(",", "."))
                except ValueError:
                    quantity = 1
                entry = {
                    "name": self.name_field.value.strip(),
                    "product": self.product_field.value.strip(),
                    "price": float(self.price_field.value.replace(",", ".")),
                    "quantity": max(1, quantity),
                    "paid": False,
                }
                self.current_list.append(entry)
                if entry["name"] not in self.people:
                    self.people.append(entry["name"])
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
                    ft.IconButton(icon=ft.icons.Icons.CLOSE, on_click=self._manager_close),
                    ft.Text(title, size=20, weight=ft.FontWeight.BOLD),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )

            self.manager_list = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO)
            self.manager_input_name = ft.TextField(label="Name", expand=True, height=44, text_size=16)
            if item_type == "produkt":
                self.manager_input_price = ft.TextField(label="Preis", expand=True, height=44, text_size=16, keyboard_type=ft.KeyboardType.NUMBER)

            add_btn = ft.Button("Hinzufügen", on_click=self._manager_add, height=44)
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
                spacing=10,
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
                            ft.Text(item.get("name", ""), expand=1, size=16),
                            ft.Text(f"{item.get('price', 0):.2f} €", size=16),
                            ft.IconButton(icon=ft.icons.Icons.DELETE, icon_color=ft.Colors.RED, on_click=lambda e, i=idx: self._manager_delete(i)),
                        ],
                        spacing=6,
                    )
                else:
                    row = ft.Row(
                        [
                            ft.Text(item, expand=1, size=16),
                            ft.IconButton(icon=ft.icons.Icons.DELETE, icon_color=ft.Colors.RED, on_click=lambda e, i=idx: self._manager_delete(i)),
                        ],
                        spacing=6,
                    )
                container = ft.Container(content=row, padding=8, border_radius=8)
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

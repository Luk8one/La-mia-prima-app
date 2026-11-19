import json
import os
import uuid
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle


# Colori dell'interfaccia
BG = (0.965, 0.957, 0.933, 1)
PANEL = (1, 1, 1, 1)
INK = (0.16, 0.17, 0.18, 1)
MUTED = (0.48, 0.49, 0.50, 1)
ACCENT = (0.25, 0.39, 0.31, 1)
ACCENT_LIGHT = (0.88, 0.92, 0.87, 1)
LINE = (0.89, 0.88, 0.85, 1)
DANGER = (0.68, 0.25, 0.22, 1)


def rounded_background(widget, color, radius=12):
    """Disegna uno sfondo arrotondato che segue le dimensioni del widget."""
    with widget.canvas.before:
        Color(*color)
        widget._bg_rect = RoundedRectangle(
            pos=widget.pos, size=widget.size, radius=[dp(radius)]
        )
    widget.bind(
        pos=lambda instance, value: setattr(widget._bg_rect, "pos", value),
        size=lambda instance, value: setattr(widget._bg_rect, "size", value),
    )


class FlatButton(Button):
    def __init__(self, bg_color=PANEL, fg_color=INK, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = bg_color
        self.color = fg_color
        self.font_size = "14sp"
        self.bold = True
        self.padding = (dp(10), dp(8))


class NoteRow(Button):
    def __init__(self, note, selected=False, callback=None, **kwargs):
        super().__init__(**kwargs)
        self.note = note
        self.background_normal = ""
        self.background_down = ""
        self.background_color = ACCENT_LIGHT if selected else PANEL
        self.color = INK
        self.halign = "left"
        self.valign = "middle"
        self.text_size = (None, None)
        title = note.get("title", "").strip() or "Senza titolo"
        body = note.get("body", "").strip().replace("\n", " ")
        preview = body[:66] + ("…" if len(body) > 66 else "")
        self.text = f"[b]{title}[/b]\n[size=12sp][color=777A78]{preview or 'Nessun testo'}[/color][/size]"
        self.markup = True
        self.padding = (dp(14), dp(10))
        self.size_hint_y = None
        self.height = dp(76)
        if callback:
            self.bind(on_release=lambda *_: callback(note["id"]))


class NotesApp(App):
    title = "Quaderno"

    def build(self):
        Window.minimum_width = 720
        Window.minimum_height = 520
        Window.size = (1100, 720)
        Window.clearcolor = BG

        self.data_file = os.path.join(self.user_data_dir, "notes.json")
        self.notes = self.load_notes()
        self.current_id = None
        self.save_event = None
        self._loading_editor = False

        root = BoxLayout(orientation="horizontal", padding=dp(16), spacing=dp(14))

        # Colonna laterale: elenco delle note
        sidebar = BoxLayout(
            orientation="vertical", size_hint_x=None, width=dp(330),
            padding=dp(14), spacing=dp(10)
        )
        rounded_background(sidebar, PANEL, 18)

        header = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        brand = Label(
            text="[b]Quaderno[/b]", markup=True, color=ACCENT,
            font_size="23sp", halign="left", valign="middle"
        )
        brand.bind(size=lambda w, s: setattr(w, "text_size", s))
        header.add_widget(brand)
        new_btn = FlatButton(
            text="+ Nuova", bg_color=ACCENT, fg_color=(1, 1, 1, 1),
            size_hint_x=None, width=dp(105)
        )
        new_btn.bind(on_release=lambda *_: self.new_note())
        header.add_widget(new_btn)
        sidebar.add_widget(header)

        self.search = TextInput(
            hint_text="Cerca nelle note…", multiline=False,
            size_hint_y=None, height=dp(42), padding=(dp(12), dp(10)),
            background_normal="", background_active="",
            background_color=BG, foreground_color=INK,
            cursor_color=ACCENT, hint_text_color=MUTED
        )
        self.search.bind(text=lambda *_: self.refresh_note_list())
        sidebar.add_widget(self.search)

        self.note_count = Label(
            text="", color=MUTED, font_size="12sp",
            size_hint_y=None, height=dp(22), halign="left", valign="middle"
        )
        self.note_count.bind(size=lambda w, s: setattr(w, "text_size", s))
        sidebar.add_widget(self.note_count)

        from kivy.uix.scrollview import ScrollView
        self.list_scroll = ScrollView(do_scroll_x=False, bar_width=dp(4))
        self.list_box = BoxLayout(
            orientation="vertical", spacing=dp(7), size_hint_y=None
        )
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        self.list_scroll.add_widget(self.list_box)
        sidebar.add_widget(self.list_scroll)

        # Pannello editor
        editor_panel = BoxLayout(
            orientation="vertical", padding=dp(22), spacing=dp(12)
        )
        rounded_background(editor_panel, PANEL, 18)

        topbar = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        self.status = Label(
            text="Le tue idee, sempre a portata di mano",
            color=MUTED, font_size="12sp", halign="left", valign="middle"
        )
        self.status.bind(size=lambda w, s: setattr(w, "text_size", s))
        topbar.add_widget(self.status)
        self.delete_btn = FlatButton(
            text="Elimina", bg_color=(0.97, 0.92, 0.91, 1),
            fg_color=DANGER, size_hint_x=None, width=dp(95)
        )
        self.delete_btn.bind(on_release=lambda *_: self.delete_note())
        topbar.add_widget(self.delete_btn)
        editor_panel.add_widget(topbar)

        self.title_input = TextInput(
            hint_text="Titolo della nota", multiline=False,
            size_hint_y=None, height=dp(58),
            font_size="25sp",
            background_normal="", background_active="",
            background_color=PANEL, foreground_color=INK,
            cursor_color=ACCENT, hint_text_color=(0.65, 0.65, 0.63, 1),
            padding=(dp(4), dp(12))
        )
        self.title_input.bind(text=lambda *_: self.schedule_save())
        editor_panel.add_widget(self.title_input)

        separator = Widget(size_hint_y=None, height=dp(1))
        with separator.canvas:
            Color(*LINE)
            separator._line = RoundedRectangle(pos=separator.pos, size=(1, 1))
        separator.bind(
            pos=lambda w, p: setattr(w._line, "pos", p),
            size=lambda w, s: setattr(w._line, "size", (s[0], dp(1)))
        )
        editor_panel.add_widget(separator)

        self.body_input = TextInput(
            hint_text="Inizia a scrivere qui…",
            multiline=True, background_normal="", background_active="",
            background_color=PANEL, foreground_color=INK,
            cursor_color=ACCENT, hint_text_color=(0.65, 0.65, 0.63, 1),
            font_size="17sp", padding=(dp(5), dp(10)),
            size_hint_y=1
        )
        self.body_input.bind(text=lambda *_: self.schedule_save())
        editor_panel.add_widget(self.body_input)

        bottom = BoxLayout(size_hint_y=None, height=dp(28))
        self.updated_label = Label(
            text="", color=MUTED, font_size="11sp",
            halign="left", valign="middle"
        )
        self.updated_label.bind(size=lambda w, s: setattr(w, "text_size", s))
        bottom.add_widget(self.updated_label)
        editor_panel.add_widget(bottom)

        root.add_widget(sidebar)
        root.add_widget(editor_panel)

        self.refresh_note_list()
        if self.notes:
            self.select_note(self.notes[0]["id"])
        else:
            self.new_note()
        return root

    def load_notes(self):
        try:
            with open(self.data_file, "r", encoding="utf-8") as file:
                notes = json.load(file)
            return notes if isinstance(notes, list) else []
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return []

    def write_notes(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        temp_file = self.data_file + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as file:
            json.dump(self.notes, file, ensure_ascii=False, indent=2)
        os.replace(temp_file, self.data_file)

    def refresh_note_list(self):
        if not hasattr(self, "list_box"):
            return
        self.list_box.clear_widgets()
        query = self.search.text.lower().strip() if hasattr(self, "search") else ""
        filtered = [
            n for n in self.notes
            if query in (n.get("title", "") + " " + n.get("body", "")).lower()
        ]
        self.note_count.text = f"{len(filtered)} note"
        for note in sorted(filtered, key=lambda n: n.get("updated", ""), reverse=True):
            self.list_box.add_widget(
                NoteRow(
                    note, selected=(note["id"] == self.current_id),
                    callback=self.select_note
                )
            )

    def new_note(self):
        self.flush_save()
        note = {
            "id": str(uuid.uuid4()),
            "title": "",
            "body": "",
            "updated": datetime.now().isoformat(timespec="seconds")
        }
        self.notes.insert(0, note)
        self.current_id = note["id"]
        self.write_notes()
        self.load_editor(note)
        self.refresh_note_list()
        self.title_input.focus = True

    def select_note(self, note_id):
        self.flush_save()
        note = next((n for n in self.notes if n["id"] == note_id), None)
        if note:
            self.current_id = note_id
            self.load_editor(note)
            self.refresh_note_list()

    def load_editor(self, note):
        self._loading_editor = True
        self.title_input.text = note.get("title", "")
        self.body_input.text = note.get("body", "")
        self._loading_editor = False
        self.updated_label.text = self.format_updated(note.get("updated", ""))
        self.status.text = "Modifica la nota: le modifiche vengono salvate automaticamente"
        self.delete_btn.disabled = False

    def schedule_save(self):
        if self._loading_editor or not self.current_id:
            return
        if self.save_event:
            self.save_event.cancel()
        self.status.text = "Modifiche in attesa di salvataggio…"
        self.save_event = Clock.schedule_once(lambda dt: self.save_current_note(), 0.7)

    def flush_save(self):
        if self.save_event:
            self.save_event.cancel()
            self.save_event = None
        if self.current_id and hasattr(self, "title_input"):
            self.save_current_note()

    def save_current_note(self):
        self.save_event = None
        note = next((n for n in self.notes if n["id"] == self.current_id), None)
        if not note or self._loading_editor:
            return
        note["title"] = self.title_input.text
        note["body"] = self.body_input.text
        note["updated"] = datetime.now().isoformat(timespec="seconds")
        self.write_notes()
        self.updated_label.text = "Ultima modifica: " + datetime.now().strftime("%d/%m/%Y %H:%M")
        self.status.text = "Salvato automaticamente"
        self.refresh_note_list()

    def delete_note(self):
        if not self.current_id:
            return
        self.flush_save()
        self.notes = [n for n in self.notes if n["id"] != self.current_id]
        self.current_id = None
        self.write_notes()
        if self.notes:
            self.select_note(self.notes[0]["id"])
        else:
            self.new_note()
        self.refresh_note_list()

    @staticmethod
    def format_updated(value):
        try:
            dt = datetime.fromisoformat(value)
            return "Ultima modifica: " + dt.strftime("%d/%m/%Y %H:%M")
        except (ValueError, TypeError):
            return ""

    def on_stop(self):
        self.flush_save()


if __name__ == "__main__":
    NotesApp().run()

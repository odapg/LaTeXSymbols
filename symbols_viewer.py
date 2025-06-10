import sublime
import sublime_plugin
import os
import shutil
import json
import base64
import threading
from collections import OrderedDict
from sublime_plugin import TextCommand
from .utils.icon_generator import ls_refresh_database


# ------------------------------- Configuration -----------------------------

st_pkgs_dir = sublime.packages_path()
PKG_NAME = "LaTeXSymbols"
METADATA_FILE = "symbols_data.json"
popup_width = 2000
popup_height = 600
icon_size = 16
column_base_length = 21
ls_settings = sublime.load_settings('LaTeXSymbols.sublime-settings')


# ------------------------------- Style sheets -------------------------------

background_dark = ls_settings.get('background_dark', '#354551')
title_dark = ls_settings.get('title_dark', '#edab26')
symbols_dark = ls_settings.get('symbols_dark', '#81c184')
package_dark = ls_settings.get('package_dark', '#d7bdff')
b_dark = ls_settings.get('b_dark', '#7bcf78')
t_dark = ls_settings.get('t_dark', '#aed7ff')
m_dark = ls_settings.get('m_dark', '#ffcbd8')
insert_dark = ls_settings.get('insert_dark', '#807e44')

background_light = ls_settings.get('background_light', '#f7fdff')
title_light = ls_settings.get('title_light', '#edab26')
symbols_light = ls_settings.get('symbols_light', '#4f7751')
package_light = ls_settings.get('package_light', '#d7bdff')
b_light = ls_settings.get('b_light', '#377f3b')
t_light = ls_settings.get('t_light', '#2d2eda')
m_light = ls_settings.get('m_light', '#db3f43')
insert_light = ls_settings.get('insert_light', '#75742b')


DARK_STYLE = f"""<style>
html {{background-color: {background_dark}; padding: 3px; 
    border: 1px solid white; margin-bottom: 1;}}
h1 {{color: {title_dark}; font-size: 1.2em; text-align: center; 
    margin-top: 0; margin-bottom: 1;}}
h3 {{color: {package_dark}; font-size: 1.1em; text-align: left; 
    margin-top: 0; margin-bottom: 1;}}
a {{ text-decoration: none; }}
type-b {{ color: {b_dark}; font-size: 0.6em; padding-left: 4px; padding-right: 3px; }}
type-t {{ color: {t_dark}; font-size: 0.6em; padding-left: 4px; padding-right: 3px; }}
type-m {{ color: {m_dark}; font-size: 0.6em; padding-left: 4px; padding-right: 3px; }}
insert {{ color: {insert_dark};}}
.latex-sym {{ text-align: left; color: {symbols_dark}; }}
</style>"""

LIGHT_STYLE = f"""<style>
html {{background-color: {background_light}; padding: 3px; 
    border: 1px solid white; margin-bottom: 1;}}
h1 {{color: {title_light}; font-size: 1.2em; text-align: center; 
    margin-top: 0; margin-bottom: 1;}}
h3 {{color: {package_dark}; font-size: 1.1em; text-align: left; 
    margin-top: 0; margin-bottom: 1;}}
a {{ text-decoration: none; }}
type-b {{ color: {b_light}; font-size: 0.6em; padding-left: 4px; padding-right: 3px; }}
type-t {{ color: {t_light}; font-size: 0.6em; padding-left: 4px; padding-right: 3px; }}
type-m {{ color: {m_light}; font-size: 0.6em; padding-left: 4px; padding-right: 3px; }}
insert {{ color: {insert_light};}}
.latex-sym {{ text-align: left; color: {symbols_light}; }}
</style>"""


# ------------------------------------  Helpers  ------------------------------------

def load_symbols():
    user_symbols_data = os.path.join(st_pkgs_dir, "User", PKG_NAME, METADATA_FILE)
    ls_symbols_data = os.path.join(st_pkgs_dir, PKG_NAME, METADATA_FILE)
    if os.path.isfile(user_symbols_data):
        data_path = user_symbols_data
    else:
        data_path = ls_symbols_data
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------

def image_to_base64(pkg_path):
    abs_path = os.path.join(st_pkgs_dir, PKG_NAME, pkg_path)
    try:
        with open(abs_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"Error loading image: {abs_path}", e)
        return None

# ---------

def generate_html(grouped):

    max_per_row = ls_settings.get('columns_number')
    if max_per_row < 1 or max_per_row > 6:
        max_per_row = 4

    theme = ls_settings.get('popup_theme')
    if theme == "dark":
        color = "white"
        STYLE = DARK_STYLE
    else:
        color = "black"
        STYLE = LIGHT_STYLE

    html = "<html><body><h1>LaTeX Symbols</h1><br>"
    html += STYLE

    for package in sorted(grouped.keys(), key=sort_key):
        symbols = grouped[package]
        html += f'<h3><a href="{package}">📦 {package}</a></h3>'

        for i in range(0, len(symbols), max_per_row):
            row = symbols[i:i + max_per_row]
            html += "<div><li>"

            for j, s in enumerate(row):
                name = s["name"]
                if j < max_per_row -1:
                    spaces = "&nbsp;" * (column_base_length - len(name))
                else:
                    spaces = ""
                icon_path = os.path.join(st_pkgs_dir, s["path"][color])
                encoded = image_to_base64(icon_path)
                if s["type"] == "both":
                    type = "<type-b>Ⓑ</type-b>"
                elif s["type"] == "math":
                    type = "<type-m>Ⓜ</type-m>"
                else:
                    type = "<type-t>Ⓣ</type-t>"
                html += f'''&nbsp;{type}
                            <img src="data:image/png;base64,{encoded}" 
                            width="{icon_size}" height="{icon_size}">
                            <a href="{name}"><span class="latex-sym">
                            {name}</span></a>
                            <a href="ins-{name}" ><insert>⎀</insert></a>{spaces}
                            '''
            html += "</li></div>"
        html += "<br>"
    html += "</body></html>"
    return html

# ---------

def grouped_symbols(filtered):
    grouped = OrderedDict()
    for symbol in filtered:
        package = symbol.get("package", "Unknown")
        if package not in grouped:
            grouped[package] = []
        grouped[package].append(symbol)
    return grouped

# ---------

def sort_key(package_name):
    return (0, "") if package_name == "latex" else (1, package_name.lower())

# ---------

def mid_point(view):
    '''Locate mid-window (actually a tiny bit higher)'''
    visible_reg = view.visible_region()
    row_a = view.rowcol(visible_reg.a)[0]
    row_b = view.rowcol(visible_reg.b)[0]
    middle_row = (row_a + row_b) / 2 - 3
    return view.text_point(middle_row, 10)

# ----------------------------  Session state  --------------------------------

class SymbolSearchSession:

    def __init__(self, view):
        self.view = view
        self.symbols = load_symbols()
        self.last_filter_text = ""
        at_caret = ls_settings.get('at_caret')
        if at_caret:
            self.fixed_location = -1
        else:    
            visible_reg = view.visible_region()
            # self.fixed_location = visible_reg.a
            row_a = view.rowcol(visible_reg.a)[0]
            self.fixed_location = view.text_point(row_a, 20)

# ---------

    def on_change(self, text):
        self.last_filter_text = text.strip().lower()
        self.update_popup(self.last_filter_text)

# ---------

    def update_popup(self, filter_text):

        def matches(s):
            if (
                filter_text in s.get("name", "").lower() 
                or filter_text.strip() == s.get("name", "").lower().lstrip('\\')
                ):
                return True
            if filter_text in s.get("package", "").lower(): 
                return True
            keywords = s.get("keywords", [])
            if isinstance(keywords, list):
                for kw in keywords:
                    if isinstance(kw, str) and filter_text in kw.lower():
                        return True
            return False

        filtered = [s for s in self.symbols if matches(s)]

        grouped = grouped_symbols(filtered)
        html = generate_html(grouped)

        self.view.show_popup(
            html,
            location= self.fixed_location,
            max_width=popup_width,
            max_height=popup_height,
            on_navigate=self.on_click
        )

# ---------

    def on_click(self, href):
        if href.startswith("ins-"):
            self.view.run_command('ls_insert_in_view', 
                                 {'text': href[4:]})
            self.view.hide_popup()
            self.view.window().run_command("hide_panel", {"panel": "input"})

        else:
            sublime.set_clipboard(href)
            sublime.status_message(f"LaTeX symbol copied to the clipboard: {href}")

# ---------

    def on_done(self, text):
        pass

    def on_cancel(self):
        pass


# -------------  Command to display symbols and start filtering --------------

class LiveFilterLatexSymbolsCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.session = SymbolSearchSession(self.window.active_view())

        sublime.set_timeout(lambda: self.session.update_popup(""), 100)
        self.window.show_input_panel(
            "Filter LaTeX Symbols:", "",
            self.on_done,
            self.on_change,
            self.on_cancel
        )

    def on_change(self, input_text):
        self.session.update_popup(input_text)

    def on_done(self, input_text):
        self.session.update_popup(input_text)

    def on_cancel(self):
        self.window.active_view().hide_popup()


# ----------- Command to display symbols corresponding to a keyword ------------

class LatexSymbolsByKeywordCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.symbols = load_symbols()
        keywords = set()
        for s in self.symbols:
            kws = s.get("keywords", [])
            if isinstance(kws, list):
                for kw in kws:
                    if isinstance(kw, str): keywords.add(kw)

        self.keywords = sorted(keywords)

        self.window.show_quick_panel(
            self.keywords,
            self.on_done,
            on_highlight=self.on_highlight,
            placeholder="[LaTeXSymbols] Select a keyword"
        )

    def on_highlight(self, index):
        if index == -1:
            return

        selected_keyword = self.keywords[index]
        view = self.window.active_view()
        popup_loc = mid_point(view)
        self.preview_keyword(selected_keyword, popup_loc)

    def on_done(self, index):
        if index == -1:
            self.window.active_view().hide_popup()
            return

        selected_keyword = self.keywords[index]
        popup_loc = self.session.fixed_location
        self.preview_keyword(selected_keyword, popup_loc)

    def preview_keyword(self, keyword, popup_loc):
        view = self.window.active_view()
        self.session = SymbolSearchSession(view)

        def matches(symbol):
            kws = symbol.get("keywords", [])
            if isinstance(kws, list):
                return keyword.lower() in [k.lower() for k in kws if isinstance(k, str)]
            return False

        filtered = [s for s in self.session.symbols if matches(s)]
        grouped = grouped_symbols(filtered)
        html = generate_html(grouped)

        view.show_popup(
            html,
            location=popup_loc,
            max_width=popup_width,
            max_height=popup_height,
            on_navigate=self.session.on_click
        )


# ---------- Command to display symbols corresponding to a package -----------

class LatexSymbolsByPackageCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.symbols = load_symbols()
        self.packages = sorted(set(
            s.get("package", "").strip()
            for s in self.symbols
            if isinstance(s.get("package"), str) and s.get("package").strip()
        ))

        self.window.show_quick_panel(
            self.packages,
            self.on_done,
            on_highlight=self.on_highlight,
            placeholder="[LaTeXSymbols] Select a LaTeX package"
        )

    def on_highlight(self, index):
        if index == -1:
            return

        selected_package = self.packages[index]
        # Locate popup at mid-window
        view = self.window.active_view()
        popup_loc = mid_point(view)

        self.preview_package(selected_package, popup_loc)

    def on_done(self, index):
        if index == -1:
            self.window.active_view().hide_popup()
            return

        selected_package = self.packages[index]

        view = self.window.active_view()
        self.session = SymbolSearchSession(view)
        popup_loc = self.session.fixed_location
        self.preview_package(selected_package, popup_loc)

    def preview_package(self, package, popup_loc):
        view = self.window.active_view()
        self.session = SymbolSearchSession(view)

        def matches(symbol):
            return symbol.get("package", "").lower() == package.lower()

        filtered = [s for s in self.session.symbols if matches(s)]
        grouped = grouped_symbols(filtered)
        html = generate_html(grouped)

        view.show_popup(
            html,
            location=popup_loc,
            max_width=popup_width,
            max_height=popup_height,
            on_navigate=self.session.on_click
        )


# --------------------------  Refresh database  -------------------------------

class RunIconGeneratorThread(threading.Thread):
    def __init__(self, window):
        threading.Thread.__init__(self)
        self.window = window

    def run(self):
        try:
            ls_refresh_database(),
        except Exception as e:
            sublime.error_message(f"[LaTeXSymbols] Error running script:\n{e}")


class LatexSymbolsRefreshCommand(sublime_plugin.WindowCommand):
    def run(self):
        thread = RunIconGeneratorThread(self.window)
        thread.start()

    def is_enabled(self):
        return True


# --------------- Command to customize the symbols.yaml file -----------------

class EditSymbolsFileCommand(sublime_plugin.WindowCommand):
    def run(self):
        
        file_name = "symbols.yaml"
        symbols_path = os.path.join(st_pkgs_dir, PKG_NAME, file_name)
        user_symbols_dir = os.path.join(st_pkgs_dir, "User", PKG_NAME)
        user_symbols_path = os.path.join(user_symbols_dir, file_name)

        if os.path.exists(user_symbols_path):
            self.window.open_file(user_symbols_path)
        else:
            os.makedirs(user_symbols_dir, exist_ok=True)

            if os.path.exists(symbols_path):
                shutil.copyfile(symbols_path, user_symbols_path)
                self.window.open_file(user_symbols_path)
            else:
                sublime.error_message(
                    f"[LaTeXSymbols] Source file does not exist:\n{symbols_path}")


# ----------------- Text command to insert text in the view -------------------

class LsInsertInView(TextCommand):
    def run(self, edit, text):
        for s in self.view.sel(): 
            point = s.a
            self.view.insert(edit, point, text)


import sublime
import sublime_plugin
import os
import shutil
import json
import base64
import subprocess
import threading
from collections import OrderedDict
from sublime_plugin import TextCommand


# ---------------------------------- Style sheets ----------------------------------

DARK_STYLE = """<style>
html {background-color: #354551; padding: 3px; border: 1px solid white; margin-bottom: 1;}
h1 {color: #edab26; font-size: 1.2em; text-align: center; margin-top: 0; margin-bottom: 1;}
h3 {color: #d7bdff; font-size: 1.1em; text-align: left; margin-top: 0; margin-bottom: 1;}
a { text-decoration: none; }
type-b { color: #7bcf78; font-size: 0.6em; padding-left: 4px; padding-right: 3px; }
type-t { color: #aed7ff; font-size: 0.6em; padding-left: 4px; padding-right: 3px; }
type-m { color: #ffcbd8; font-size: 0.6em; padding-left: 4px; padding-right: 3px; }
insert { color: #807e44;}
.latex-sym { text-align: left; color: #81c184; }
</style>"""

LIGHT_STYLE = """<style>
html {background-color: #f0fff6; padding: 3px; border: 1px solid white; margin-bottom: 1;}
h1 {color: #edab26; font-size: 1.2em; text-align: center; margin-top: 0; margin-bottom: 1;}
h3 {color: #d7bdff; font-size: 1.1em; text-align: left; margin-top: 0; margin-bottom: 1;}
a { text-decoration: none; }
type-b { color: #00d542; font-size: 0.6em; padding-left: 4px; padding-right: 3px; }
type-t { color: #2d2eda; font-size: 0.6em; padding-left: 4px; padding-right: 3px; }
type-m { color: #db3f43; font-size: 0.6em; padding-left: 4px; padding-right: 3px; }
insert { color: #75742b;}
.latex-sym { text-align: left; color: #4f7751; }
</style>"""


# ------------------------------------  Helpers  ------------------------------------

def load_symbols():
    user_symbols_data = os.path.join(
        sublime.packages_path(), "User", "LaTeXSymbols", "symbols_data.json")
    ls_symbols_data = os.path.join(
        sublime.packages_path(), "LaTeXSymbols", "symbols_data.json")
    if os.path.isfile(user_symbols_data):
        data_path = user_symbols_data
    else:
        data_path = ls_symbols_data
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)

# -------------

def image_to_base64(pkg_path):
    abs_path = os.path.join(sublime.packages_path(), "LaTeXSymbols", pkg_path)
    try:
        with open(abs_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"Error loading image: {abs_path}", e)
        return None

# -------------

def generate_html(grouped):
    icon_size = 16

    ls_settings = sublime.load_settings('LaTeXSymbols.sublime-settings')

    max_per_row = ls_settings.get('columns_number')
    if max_per_row < 2 or max_per_row > 5:
        max_per_row = 4

    theme = ls_settings.get('background_color')
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
                ws = "&nbsp;" * (21 - len(name)) if j < max_per_row -1 else ""
                icon_path = os.path.join(sublime.packages_path(), s["path"][color])
                print(icon_path)
                encoded = image_to_base64(icon_path)
                if s["type"] == "both":
                    type = "<type-b>Ⓑ</type-b>"
                elif s["type"] == "math":
                    type = "<type-m>Ⓜ</type-m>"
                else:
                    type = "<type-t>Ⓣ</type-t>"
                html += f'''&nbsp;{type}
                            <img src="data:image/png;base64,{encoded}" 
                            width="16" height="16">
                            <a href="{name}"><span class="latex-sym">
                            {name}</span></a>
                            <a href="ins-{name}" ><insert>⎀</insert></a>{ws}
                            '''
            html += "</li></div>"
        html += "<br>"
    html += "</body></html>"
    return html

# -------------

def grouped_symbols(filtered):
    grouped = OrderedDict()
    for symbol in filtered:
        package = symbol.get("package", "Unknown")
        if package not in grouped:
            grouped[package] = []
        grouped[package].append(symbol)
    return grouped

# -------------

def sort_key(package_name):
    return (0, "") if package_name == "latex" else (1, package_name.lower())


# ----------------------------  Session state  --------------------------------

class SymbolSearchSession:

    def __init__(self, view):
        self.view = view
        self.symbols = load_symbols()
        self.last_filter_text = ""
        ls_settings = sublime.load_settings('LaTeXSymbols.sublime-settings')
        at_caret = ls_settings.get('at_caret')
        if at_caret:
            self.fixed_location = -1
        else:    
            visible_region = self.view.visible_region()
            self.fixed_location = visible_region.a

# -------------

    def on_change(self, text):
        self.last_filter_text = text.strip().lower()
        self.update_popup(self.last_filter_text)

# -------------

    def update_popup(self, filter_text):

        def matches(s):
            if filter_text in s.get("name", "").lower(): return True
            if filter_text in s.get("package", "").lower(): return True
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
            max_width=1500,
            max_height=600,
            on_navigate=self.on_click
        )

# -------------

    def on_click(self, href):
        if href.startswith("ins-"):
            self.view.run_command('ls_insert_in_view', 
                        {'text': href[4:]})
            self.view.hide_popup()
            self.view.window().run_command("hide_panel", {"panel": "input"})

        else:
            sublime.set_clipboard(href)
            sublime.status_message(f"LaTeX symbol copied: {href}")

# -------------

    def on_done(self, text):
        pass

    def on_cancel(self):
        pass


# -------------  Command to display symbols and start filtering ---------------------

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


# ------------ Command to display symbols corresponding to a keyword --------------

class LatexSymbolsByKeywordCommand(sublime_plugin.WindowCommand):
    def run(self, keyword):
        view = self.window.active_view()
        self.session = SymbolSearchSession(view)

        def matches(symbol):
            keywords = symbol.get("keywords", [])
            if isinstance(keywords, list):
                lower_keywords = [kw.lower() for kw in keywords if isinstance(kw, str)]
                return keyword.lower() in lower_keywords
            return False

        filtered = [s for s in self.session.symbols if matches(s)]

        grouped = grouped_symbols(filtered)
        html = generate_html(grouped)

        view.show_popup(
            html,
            location=self.session.fixed_location,
            max_width=1500,
            max_height=600,
            on_navigate=self.session.on_click
        )

    def input(self, args):
        if "keyword" in args:
            return None
        return KeywordInputHandler()


class KeywordInputHandler(sublime_plugin.ListInputHandler):
    def list_items(self):
        symbols = load_symbols()
        keywords = set()
        for s in symbols:
            kws = s.get("keywords", [])
            if isinstance(kws, list):
                for kw in kws:
                    if isinstance(kw, str):
                        keywords.add(kw)
        return sorted(keywords)


# ------------ Command to display symbols corresponding to a package --------------

class LatexSymbolsByPackageCommand(sublime_plugin.WindowCommand):
    def run(self, package):
        view = self.window.active_view()
        self.session = SymbolSearchSession(view)

        def matches(symbol):
            return symbol.get("package", "").lower() == package.lower()

        filtered = [s for s in self.session.symbols if matches(s)]

        grouped = grouped_symbols(filtered)
        html = generate_html(grouped)

        view.show_popup(
            html,
            location=self.session.fixed_location,
            max_width=1500,
            max_height=600,
            on_navigate=self.session.on_click
        )

    def input(self, args):
        if "package" in args:
            return None
        return PackageInputHandler()


class PackageInputHandler(sublime_plugin.ListInputHandler):
    def list_items(self):
        symbols = load_symbols()
        packages = set()
        for s in symbols:
            pkg = s.get("package", "")
            if isinstance(pkg, str) and pkg.strip():
                packages.add(pkg.strip())
        return sorted(packages)


# -----------------------------  Refresh database  ----------------------------------

class RunIconGeneratorThread(threading.Thread):
    def __init__(self, window):
        threading.Thread.__init__(self)
        self.window = window

    def run(self):
        LS_dir = os.path.join(sublime.packages_path(), "LaTeXSymbols") 
        script_path = os.path.join(LS_dir, "utils", "icon_generator.py")

        if not os.path.isfile(script_path):
            sublime.error_message("Script not found:\n" + script_path)
            return

        try:
            process = subprocess.Popen(
                ["python3", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                cwd=LS_dir
            )

            output = ""
            for line in process.stdout:
                print("[icon-generator] " + line.strip())
                output += line

            process.wait()
            if process.returncode != 0:
                print(f"[icon-generator] Process exited with code {process.returncode}")
            else:
                print("[icon-generator] ✅ Done")

        except Exception as e:
            sublime.error_message("Error running script:\n" + str(e))


class LatexSymbolsRefreshCommand(sublime_plugin.WindowCommand):
    def run(self):
        thread = RunIconGeneratorThread(self.window)
        thread.start()

    def is_enabled(self):
        return True


# ------------------- Text command to insert text in the view ---------------------

class LsInsertInView(TextCommand):
    def run(self, edit, text):
        for s in self.view.sel(): 
            point = s.a
            self.view.insert(edit, point, text)


# ----------------- Command to customize the symbols.yaml file -------------------

class EditSymbolsFileCommand(sublime_plugin.WindowCommand):
    def run(self):
        
        file_name = "symbols.yaml"


        # Define source and destination paths
        symbols_path = os.path.join(sublime.packages_path(), "LaTeXSymbols", file_name)
        user_symbols_dir = os.path.join(sublime.packages_path(), "User", "LaTeXSymbols")
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
                    "Source file does not exist:\n{}".format(symbols_path))


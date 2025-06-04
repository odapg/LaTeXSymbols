import os
import yaml
import hashlib
import json
import tempfile
import subprocess
import shlex
from pathlib import Path
from functools import partial

# --------------------------------- Configuration ---------------------------------

st_pkgs_dir = Path(__file__).resolve().parent.parent.parent
INPUT_YAML = "symbols.yaml"
PKG_NAME = "LaTeXSymbols"
ICONS_DIR = "icons"
METADATA_FILE = "symbols_data.json"

pkg_icon_dir = os.path.join(PKG_NAME, ICONS_DIR)
user_symbols_dir = os.path.join(st_pkgs_dir, "User", PKG_NAME)
user_icon_dir = os.path.join("User", PKG_NAME, ICONS_DIR)
user_icon_dir_fullpath = os.path.join(st_pkgs_dir, user_icon_dir)
user_yaml_file = os.path.join(user_symbols_dir, INPUT_YAML)
metadata_file = os.path.join(user_symbols_dir, METADATA_FILE)

COLORS = ["white", "black"]
ICON_SIZE = "64x64"
DPI = "600"
GAMMA = "1"

TEMPLATE = r"""
\documentclass[10pt]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage{{color}}
{packages}
\pagestyle{{empty}}
\begin{{document}}
\color{{{color}}}
{command}
\end{{document}}
"""

# -------------------

# Force real-time print output (for Sublime Text console)
print = partial(print, flush=True)

# ------------------------------------ Helpers ------------------------------------

# Ensure output and log directories exist
Path(user_icon_dir_fullpath).mkdir(parents=True, exist_ok=True)
for color in COLORS:
    Path(os.path.join(user_icon_dir_fullpath,color)).mkdir(parents=True, exist_ok=True)

# ------------

def hash_filename(command, color, package=None):
    key = f"{command}-{color}-{package or 'latex'}"
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return h[:16] + ".png"

# ------------

def run_command(command, log_path=None):
    result = subprocess.run(
        command, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        shell=False,
        text=True
    )
    if result.returncode != 0 and log_path:
        with open(log_path, "wb") as f:
            f.write(result.stdout + b"\n" + result.stderr)
    return result.returncode == 0


# -------------------------------- Icon generator --------------------------------

def generate_icon(symbol, color):
    command = symbol["command"]
    package = symbol.get("package")
    fontenc = symbol.get("fontenc")
    latex_command = f"${command}$" if symbol.get("type") == "math" else command
    filename = hash_filename(command, color, package)
    
    output_path_ls = os.path.join(pkg_icon_dir, color, filename)
    output_fullpath_ls = os.path.join(st_pkgs_dir, output_path_ls)
    output_path_user = os.path.join(user_icon_dir, color, filename)
    output_fullpath_user = os.path.join(st_pkgs_dir, output_path_user)
    
    if os.path.isfile(output_fullpath_ls):
        return output_path_ls, "exists"
    elif os.path.isfile(output_fullpath_user):
        return output_path_user, "exists"

    output_path = output_fullpath_user
    
    with tempfile.TemporaryDirectory() as tmpdir:
        basename = "symbol"
        tex_path = Path(tmpdir) / f"{basename}.tex"
        dvi_path = Path(tmpdir) / f"{basename}.dvi"
        # log_path = USER_LOG_DIR / f"{filename}.log"

        packages = ""
        if package and package.lower() != "latex":
            packages += f"\\usepackage{{{package}}}\n"
        if fontenc:
            packages += f"\\usepackage[{fontenc}]{{fontenc}}\n"

        tex_content = TEMPLATE.format(packages=packages, color=color, 
                                      command=latex_command)
        tex_path.write_text(tex_content)

        # Compile LaTeX
        success = run_command([ "latex",
                                "-interaction=batchmode",
                                f"-output-directory={tmpdir}",
                                tex_path
                              ],
                            )
                    # log_path=log_path
        if not success or not dvi_path.exists():
            return None, "latex_failed"

        # Convert to PNG
        success = run_command([ "dvipng",
                                "-bg", "Transparent",
                                "-T", "tight",
                                "-D", f"{DPI}",
                                "--gamma", f"{GAMMA}",
                                "-o", f"{output_path}",
                                f"{dvi_path}"
                                ]
                            )
                     # log_path=log_path,
        if not success:
            return None, "dvipng_failed"

        # Resize with mogrify
        success = run_command( ["mogrify",
                                "-resize", f'{ICON_SIZE}',
                                "-extent", f'{ICON_SIZE}',
                                "-background", "transparent",
                                "-gravity", "South", #"center",
                                f'{output_path}',
                                ]
                            )
                     # log_path=log_path,
        if not success:
            output_path.unlink(missing_ok=True)
            return None, "mogrify_failed"

    return output_path_user, "generated"


# -------------------------------- Main Command --------------------------------

def main():

    if os.path.exists(user_yaml_file):
        yaml_file = user_yaml_file
    else:
        print(f"❌ No user symbol file.")
        return
    try:
        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        metadata = []
        all_symbols = [
            (table, symbol)
            for table in data.get("tables", [])
            for symbol in table.get("symbols", [])
        ]
        total = len(all_symbols)
        new_icon = 0

        for index, (table, command) in enumerate(all_symbols):
            package = table.get("package")
            type_ = table.get("type")
            keywords = table.get("keywords", [])
            if isinstance(keywords, str):
                keywords = [keywords]

            symbol_data = {
                "command": command,
                "package": package,
                "type": type_,
                "keywords": keywords,
            }
            if "fontenc" in table:
                symbol_data["fontenc"] = table["fontenc"]

            paths = {}
            icon_folder =os.path.join("LaTeXSymbols", "icons")

            for color in COLORS:
                icon_name, status = generate_icon(symbol_data, color)
                msg = f"[{index+1}/{total}] {command.ljust(20)} ({color}) : "
                if status == "exists":
                    print(msg + "⏩ Already exists")
                    paths[color] = icon_name
                elif status == "generated":
                    print(msg + f"✅ {icon_name}")
                    paths[color] = icon_name
                    new_icon += 1
                elif status == "latex_failed":
                    print(msg + f"❌ LaTeX failed")
                elif status == "dvipng_failed":
                    print(msg + f"❌ dvipng failed")
                elif status == "mogrify_failed":
                    print(msg + f"❌ mogrify failed")

            if paths:
                metadata.append( {
                    "name": command, 
                    "package": package,
                    "type": type_,
                    "keywords": keywords,
                    "path": paths,
                } )

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Done. {new_icon} new icons generated. \n Data saved to {metadata_file}.")

    except Exception as e:
        print(f"""❌ There was an error when updating the data:\n{e}\n 
                    User's symbols_data.json file was not generated.""")

# ------------------------

if __name__ == "__main__":
    main()

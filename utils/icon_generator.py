import os
import yaml
import hashlib
import json
import tempfile
import subprocess
from pathlib import Path

# Configuration
INPUT_YAML = "symbols.yaml"
OUTPUT_DIR = Path("./icons")
LOG_DIR = Path("./logs")
METADATA_PATH = "symbols_data.json"
COLORS = ["white", "black"]
ICON_SIZE = "64x64"
DPI = os.getenv("DPI", "600")
GAMMA = os.getenv("GAMMA", "1")

# Ensure output and log directories exist
# for path in [OUTPUT_DIR, LOG_DIR] + [OUTPUT_DIR / color for color in COLORS]:
#     path.mkdir(parents=True, exist_ok=True)

# LaTeX template with escaped braces for .format()
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

def hash_filename(command, color, package=None):
    key = f"{command}-{color}-{package or 'latex'}"
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return h[:16] + ".png"

def run_command(command, log_path=None):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    # if result.returncode != 0 and log_path:
    #     with open(log_path, "wb") as f:
    #         f.write(result.stdout + b"\n" + result.stderr)
    return result.returncode == 0

def generate_icon(symbol, color):
    command = symbol["command"]
    package = symbol.get("package")
    fontenc = symbol.get("fontenc")
    latex_command = f"${command}$" if symbol.get("type") == "math" else command
    filename = hash_filename(command, color, package)
    output_path = OUTPUT_DIR / color / filename

    if output_path.exists():
        return output_path.name, "exists"

    with tempfile.TemporaryDirectory() as tmpdir:
        basename = "symbol"
        tex_path = Path(tmpdir) / f"{basename}.tex"
        dvi_path = Path(tmpdir) / f"{basename}.dvi"
        log_path = LOG_DIR / f"{filename}.log"

        packages = ""
        if package and package.lower() != "latex":
            packages += f"\\usepackage{{{package}}}\n"
        if fontenc:
            packages += f"\\usepackage[{fontenc}]{{fontenc}}\n"

        tex_content = TEMPLATE.format(packages=packages, color=color, command=latex_command)
        tex_path.write_text(tex_content)

        # Compile LaTeX
        success = run_command(
            f"latex -interaction=batchmode -output-directory={tmpdir} {tex_path}",
            # log_path=log_path,
        )
        if not success or not dvi_path.exists():
            return None, "latex_failed"

        # Convert to PNG
        success = run_command(
            f"dvipng -bg Transparent -T tight -D {DPI} --gamma {GAMMA} {dvi_path} -o {output_path}",
            # log_path=log_path,
        )
        if not success:
            return None, "dvipng_failed"

        # Resize with mogrify
        success = run_command(
            f"mogrify -resize '{ICON_SIZE}>' -extent '{ICON_SIZE}' "
            f"-background transparent -gravity center {output_path}",
            # log_path=log_path,
        )
        if not success:
            output_path.unlink(missing_ok=True)
            return None, "mogrify_failed"

    return output_path.name, "generated"

def main():
    with open(INPUT_YAML, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    metadata = []
    all_symbols = [
        (table, symbol)
        for table in data.get("tables", [])
        for symbol in table.get("symbols", [])
    ]
    total = len(all_symbols)

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
        for color in COLORS:
            icon_name, status = generate_icon(symbol_data, color)
            symbol_name = command.strip("\\")
            msg = f"[{index+1}/{total}] {command.ljust(20)} ({color}) : "
            if status == "exists":
                print(msg + "⏩ Already exists")
                paths[color] = icon_name
            elif status == "generated":
                print(msg + f"✅ {icon_name}")
                paths[color] = icon_name
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

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Done. Data saved to {METADATA_PATH}")

if __name__ == "__main__":
    main()

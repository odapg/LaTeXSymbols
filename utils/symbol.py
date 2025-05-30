import os
import json
import re

class LatexSymbol:
    def __init__(self, command, filename, package=None, fontenc=None, mathmode=True):
        self.command = command
        self.filename = filename
        self.package = package
        self.fontenc = fontenc
        self.mathmode = mathmode

def sanitize_filename(command):
    """
    Transforme une commande LaTeX en un nom de fichier sûr.
    Exemple : '\\textasciicircum' devient 'textasciicircum'
    """
    command = re.sub(r'[^a-zA-Z0-9]+', '_', command)
    return command.strip('_').lower()

def load_symbols_from_json(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    symbols = []
    for table_entry in data.get('tables', []):
        package = table_entry.get('package', None)
        symbol_type = table_entry.get('type', 'math')
        mathmode = symbol_type in ('math', 'both')

        for command in table_entry.get('symbols', []):
            filename = sanitize_filename(command)
            symbols.append(LatexSymbol(command, filename, package=package, mathmode=mathmode))

    return symbols

# Charger les symboles depuis le fichier JSON
JSON_SYMBOLS_FILE = 'symbols.json'
LatexSymbolList = load_symbols_from_json(JSON_SYMBOLS_FILE)

# Préparer les répertoires de sortie
for color in ['white', 'black']:
    os.makedirs(os.path.join('./icons', color), exist_ok=True)

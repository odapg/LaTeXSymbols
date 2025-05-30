## LaTeX Symbols for Sublime Text

### Overview

LaTeX Symbols for Sublime Text is a simple ST4 package displaying a popup to help finding a LaTeX Symbol.
It opens an input panel to search symbols by name/keyword/package.


#### Manual installation

1. Clone or download this repository using the green `Clone or download` button.
2. Move the `LaTeXSymbols` folder to your Sublime Text's `Packages` folder. 
3. Restart Sublime Text.

### Usage

1. Use the command-palette entry `LaTeXSymbols: show popup and search` and start typing to filter the results.
Alternatively, use the commands `LaTeXSymbols: Show symbols by Keyword` or `LaTeXSymbols: Show symbols by Package`.
Use `Esc` to close the popup.

2. Click on a command to copy it to the clipboard and on `⎀` to insert it directly to your text and close the popup.
You can also copy a package name by clicking on it. 

3. About the icons:

- Ⓣ is for text-mode commands
- Ⓜ is for math-mode commands
- Ⓑ is for both modes commands

4. Dark or light theme can be chosen in `LaTeXSymbols.sublime-settings`.

### Completing the symbols list

LaTeX Symbols is designed to let the user customize the symbols list. For that:

1. Modify the `symbols.yaml` file to add symbols, keywords, etc.
The yaml syntax should be sufficiently self-explanatory. 
A `table for symbols.yaml` snippet is included to facilitate the procedure.
Check that the yaml syntax is respected (be careful about tabs and spaces).

2. Use the command-palette entry `LaTeXSymbols: Update database and icons` to update the database.
For new symbols, the compilation process is run in the background and can be slow: check the console.

### Remark

A lot of other symbols could be added to the current list.
Do not hesitate to make a pull request!

### Acknowledgements

LaTeX Symbols for Sublime Text is adapted from @wookayin's [Alfred](https://www.alfredapp.com/) workflow [alfred-latex-symbols-workflow](https://github.com/wookayin/alfred-latex-symbols-workflow). 
Symbols were taken from there and completed (a little bit) thanks to S. Pakin's [Comprehensive LaTeX Symbol List](https://ctan.org/pkg/comprehensive).

alfred-latex-symbols-workflow is © 2015-2021 Jongwook Choi under the MIT License.

The Comprehensive LaTeX Symbol List is © Scott Pakin under the LaTeX Project Public License 1.3c.



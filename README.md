# LaTeX Symbols for Sublime Text

## Overview

LaTeX Symbols for Sublime Text is a simple ST4 package displaying a popup to help finding
a LaTeX symbol. It opens an input panel to search symbols by name/keyword/package.

![LaTeXSymbols example](./images/example.png)

## Manual installation

1. Clone or download this repository using the `Clone or download` button. 

2. Move the folder to your Sublime Text's `Packages` folder. Make sure it is called 
`LaTeXSymbols`.

3. Restart Sublime Text.


## Usage

1. Use the command-palette entry `LaTeXSymbols: show popup and search` and start typing to
filter the results. Alternatively, use the commands `LaTeXSymbols: Show symbols by
Keyword` or `LaTeXSymbols: Show symbols by Package`. Use `Esc` to close the popup.

2. Click on a command to copy it to the clipboard and on `⎀` to insert it directly to your
text and close the popup. You can also copy a package name by clicking on it. 

3. About the icons:

- Ⓣ is for text-mode commands
- Ⓜ is for math-mode commands
- Ⓑ is for both modes commands

4. Dark or light theme can be chosen in `LaTeXSymbols.sublime-settings`.


## Customizing the symbols list

LaTeX Symbols is designed to let the user customize the symbols list. For that:

1. Use the command `LaTeXSymbols: Customize Symbols YAML list` to open your copy
of the original `symbols.yaml` file, put in the `User/LaTeXSymbols/` folder. 

2. Add symbols, modify the keywords, comment useless tables, etc. directly in the new
`symbols.yaml` file. The YAML syntax is intended to be self-explanatory. A `Snippet:
table for symbols.yaml` is included with the package to facilitate the procedure (use at
the beginning of line). Check that the yaml syntax is respected (be careful about
spaces).

3. Use the command-palette entry `LaTeXSymbols: Update database and icons` to update the
database. For new symbols, the compilation process to generate thumbnails is run in the
background and can be slow: check the console.

This requires (for new symbols):
- `dvipng` (usually coming with TeX distributions)
- `mogrify` (coming with [`ImageMagick`](https://imagemagick.org/index.php))

## License

This package is licensed under the MIT license. In particular, it is provided "as is",
without warranty of any kind!


## Remark

A lot of other symbols could be added to the current list. Do not hesitate to make a pull
request!


## Acknowledgements

LaTeX Symbols for Sublime Text is adapted from [@wookayin](https://github.com/wookayin/)'s
[Alfred](https://www.alfredapp.com/) workflow 
[alfred-latex-symbols-workflow](https://github.com/wookayin/alfred-latex-symbols-workflow). 
Symbols were taken from there and completed (a bit) thanks to S. Pakin's 
[Comprehensive LaTeX Symbol List](https://ctan.org/pkg/comprehensive).
Inspiration also came from this 
[post](https://forum.sublimetext.com/t/plugin-which-shows-a-popup-with-all-keybindings/69493)
by [@giampaolo](https://github.com/giampaolo/) in 
[Sublime forum](https://forum.sublimetext.com/).

alfred-latex-symbols-workflow is © 2015-2021 Jongwook Choi under the MIT License.

The Comprehensive LaTeX Symbol List is © Scott Pakin under the LaTeX Project Public
License 1.3c.



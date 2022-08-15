#!/bin/bash

# Generate html documentation
pdoc --html -f -o doc sqlite_integrated

# Generate markdown documentation
pdoc --pdf -f -o doc sqlite_integrated 1> "doc/sqlite_integrated/doc.md"

# convert to pdf
pandoc --metadata=title:"Sqlite-Integrated Documentation"               \
           --from=markdown+abbreviations+tex_math_single_backslash  \
           --pdf-engine=xelatex \
           --toc --toc-depth=4 --output=doc/sqlite_integrated/doc.pdf  doc/sqlite_integrated/doc.md

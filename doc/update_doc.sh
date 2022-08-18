#!/bin/bash

src_path="src/sqlite_integrated"
doc_path="doc"

echo "updating docs..."

# Generate html documentation
echo "Generating html..."
pdoc --html -f -o doc "$src_path" 1> /dev/null

# Generate markdown documentation
echo "Generating markdown..."
pdoc --pdf -f -o doc "$src_path" 1> "$doc_path/sqlite_integrated/doc.md" 2> /dev/null
sed -i 's/{#id}//' "$doc_path/sqlite_integrated/doc.md" # delete {id} tags
sed -i -z 's/\n\n\+/\n\n/g' "$doc_path/sqlite_integrated/doc.md" # Not as many newlines
sed -i -z 's/\n\n\+/\n\n/g' "$doc_path/sqlite_integrated/doc.md" # Delete description lines
sed -i '1,15d' "$doc_path/sqlite_integrated/doc.md"

# convert to pdf
echo "Converting markdown to pdf..."
pandoc --metadata=title:"Sqlite-Integrated Documentation"               \
           --from=markdown+abbreviations+tex_math_single_backslash  \
           --pdf-engine=xelatex \
           --toc --toc-depth=4 --output="$doc_path/sqlite_integrated/doc.pdf"  "$doc_path/sqlite_integrated/doc.md" #2> /dev/null

echo "DONE"

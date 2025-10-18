#!/bin/bash
echo "Scanning project source for duplicates (excluding .venv, system, and library folders)..."

# Scan only core app directories
find . -type f \( -name "*.py" -o -name "*.html" -o -name "*.css" -o -name "*.js" \) \
  ! -path "*/.venv/*" \
  ! -path "*/venv/*" \
  ! -path "*/__pycache__/*" \
  ! -path "*/migrations/*" \
  ! -path "*/site-packages/*" \
  ! -path "*/dist-packages/*" \
  ! -path "*/config/*" \
  ! -name "__init__.py" > all_files.txt

awk -F/ '{print $NF}' all_files.txt | sort | uniq -d > duplicate_names.txt

mkdir -p cleanup_reports
> cleanup_reports/cleanup_plan.csv
echo "file_type,filename,keep_path,delete_paths,reasoning" >> cleanup_reports/cleanup_plan.csv

while read name; do
  echo "Analyzing $name..."
  grep "/$name$" all_files.txt > tmp_list.txt

  # Pick longest file (most complete)
  keep=$(while read path; do wc -l < "$path" | awk -v f="$path" '{print $1, f}'; done < tmp_list.txt | sort -nr | head -1 | cut -d' ' -f2-)
  delete_paths=$(grep -v "$keep" tmp_list.txt | tr '\n' ';')
  reason="Longest version retained (most code or HTML richness)"
  file_type="${name##*.}"
  echo "$file_type,$name,$keep,$delete_paths,$reason" >> cleanup_reports/cleanup_plan.csv

done < duplicate_names.txt

> cleanup_keep_only.sh
echo "#!/bin/bash" >> cleanup_keep_only.sh
echo "echo 'Running Gorilla-Link cleanup (safe mode)...'" >> cleanup_keep_only.sh

awk -F, 'NR>1 {split($4, delims, ";"); for (i in delims) if (length(delims[i])>0) print "rm -f \""delims[i]"\""}' cleanup_reports/cleanup_plan.csv >> cleanup_keep_only.sh

echo "echo 'Cleanup complete ✅'" >> cleanup_keep_only.sh
chmod +x cleanup_keep_only.sh

echo "✅ Done! See cleanup_reports/cleanup_plan.csv for the new filtered results."

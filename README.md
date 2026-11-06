# CSV Cleaner

A small Python script that cleans messy CSV files (customer lists, contact exports, order data). It fixes common formatting problems and removes empty and duplicate rows, so the file is ready for Excel, Google Sheets, or an import.

This is a personal concept project built to practice Python and data cleaning.

## What it does

- Trims extra spaces in every cell
- Fixes name capitalisation (`JOHN SMITH` becomes `John Smith`; names like `McDonald` are left alone)
- Lowercases emails and warns about invalid ones
- Standardises phone numbers (`+38 (050) 123-45-67` becomes `+380501234567`)
- Converts dates from many formats to `YYYY-MM-DD` and warns about dates it cannot read
- Removes completely empty rows
- Removes duplicates (by email when there is an email column, otherwise by the whole row)
- Detects comma, semicolon, or tab separators automatically

Columns are recognised by their header: names containing `name`, `email`, `phone`/`tel`/`mobile`, and `date`. Any other column only gets its spaces trimmed.

## Requirements

Python 3.8 or newer. No extra packages are needed.

## Usage

```
python clean_csv.py sample_data.csv
```

The result is saved next to the original as `sample_data_cleaned.csv`. To choose another file name:

```
python clean_csv.py sample_data.csv -o result.csv
```

Dates written with slashes, like `03/04/2025`, are read as month/day/year by default. For day/month/year add `--day-first`:

```
python clean_csv.py sample_data.csv --day-first
```

## Example

Input (`sample_data.csv`):

```
name,email,phone,signup_date,city
 anna kovalenko ,Anna.Kovalenko@Example.com,+38 (050) 123-45-67,2025-03-14,Kyiv
JOHN SMITH,john.smith@example.com,(555) 014-2290,03/15/2025,  Portland
...
```

Output (`sample_data_cleaned.csv`):

```
name,email,phone,signup_date,city
Anna Kovalenko,anna.kovalenko@example.com,+380501234567,2025-03-14,Kyiv
John Smith,john.smith@example.com,5550142290,2025-03-15,Portland
...
```

Summary printed in the terminal:

```
Rows read:          12
Empty rows removed: 2
Duplicates removed: 2
Rows written:       8
Warning: 1 row(s) have an invalid email (kept, please check).
Warning: 1 date(s) could not be recognised (left as they were).
Saved to: sample_data_cleaned.csv
```

## Limitations

- Ambiguous dates such as `03/04/2025` depend on the `--day-first` option.
- Phone numbers are cleaned but not checked against a country format.
- Rows with an invalid email are kept and reported, not deleted.

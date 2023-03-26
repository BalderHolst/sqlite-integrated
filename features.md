# Version 0.0.6

## Features and Changes

### Tables are Generators!
Now tables are returned as generators instead of lists. This is essential for large tables. To restore the old behavior, just wrap your table with `list` like this:
```python
old_table = list(db.get_table("table_name"))
```
### `silent` removed in favor of `verbose`
The `Database` and all other classes no longer use the `silent` flag, now the flag is called `verbose`. `verbose` is `False` by default, and enables prints when doing operations.

### Memory Database Constructor
You can now simply create a database in memory like this:
```python
db = Database.in_memory()
```
### Ensure Primary Key Columns Type
The database will now complain if you try to crate a primary column this a sqlite3 datatype other than "INTEGER".

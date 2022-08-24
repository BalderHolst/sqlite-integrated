# What is this?

This package provides classes to make handling of sqlite3 databases easier. I have strived to make this package as simple as possible, and the error messages as helpful as possible. The main Database class handles reading from, and writing to the database. The DatabaseEntry class represents a single database entry. It can be used like a dictionary to assign new values to the entry. Ex: ´entry['name'] = "New Name"´. The Query can be used to create sql-queries with or without an attached Database to run it on.

# How to use it!

### Creating a new database
Start by importing the class and creating our NEW database (remember to put in a valid path to the database file)
```python
from sqlite_integrated import Database
db = Database("path/to/database.db", new=True)
```

We pass `new=True` to create a new database file.

We can now create a table with sql

```python
db.cursor.execute("""CREATE TABLE people (
id integer PRIMARY KEY,
first_name text,
last_name text
)""")
```

We can see an overview of the tables in the database and their table fields with the method `overview`.

```python
db.overview()
```

*Output*:
```
Tables
	people
		id
		first_name
		last_name
```

To add an entry use the `add_table_entry` method
```python
db.add_table_entry({"first_name": "John", "last_name": "Smith"}, "people")
```

Let's add a few more
```python
db.add_table_entry({"first_name": "Tom", "last_name": "Builder"}, "people")
db.add_table_entry({"first_name": "Eva", "last_name": "Larson"}, "people")
```

To view to database we can use the `table_overview` method.
```python
db.table_overview("people")
```


### Opening an existing database

Start by importing the class and opening our database
```python
from sqlite_integrated import Database
db = Database("path/to/database.db")
```

Just to check you can now run
```python
print(db.get_table_names())
```

This will output the names of all tables in the database

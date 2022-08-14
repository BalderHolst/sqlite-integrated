This package provides a class to make handeling of sqlite3 databases easier. It makes it possible to add/update database entries with python dictionaries. Database requestes also return tables that can easily be manipulated.

### How to use it!

##### Creating a new database
Start by importing the class and creating our NEW database
```python
from sqlite_integrated import Database
db = Database("path/to/database.db", new=True)
```

we pass `new=True` to create a new database file.

We can now create a table with sql



```python
db.cursor.execute("""CREATE TABLE people (
id integer PRIMARY KEY,
first_name text,
last_name text,
)""")
```

To add an entry use the `add_table_entry` method
```python
db.add_table_entry("people", {"first_name": "John", "last_name": "Smith"})
```

Let's add a few more
```python
db.add_table_entry("people", {"first_name": "Tom", "last_name": "Builder"})
db.add_table_entry("people", {"first_name": "Eva", "last_name": "Larson"})
```

To look at this table we can run someting like this
```python
for person in db.get_table("people"):
    print(person)
```


##### Opening an existing database

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

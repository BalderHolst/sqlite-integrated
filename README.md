# What is this?

This package provides classes to make handling of sqlite3 databases easier. I have strived to make it as simple as possible, and the error messages as helpful as possible. The main `Database` class handles reading from and writing to the database. The `DatabaseEntry` class represents a single database entry. It can be used like a dictionary to assign new values to the entry. Ex: `entry['name'] = "New Name"`. The `Query` class can be used to create sql-queries with or without an attached Database to run it on.

# Installation
Install with pip
```bash
pip install sqlite-integrated
```

# Read the documentation
The documentation can be found [here](https://htmlpreview.github.io/?https://github.com/BalderHolst/sqlite-integrated/blob/main/docs/sqlite_integrated/index.html).

# Github Repo
If you are interested in the open source code, click [here](https://github.com/BalderHolst/sqlite-integrated).

# How to use it!

### Creating a new database
Start by importing the class and creating our NEW database (remember to put in a valid path to the database file).
```python
from sqlite_integrated import Database
db = Database("path/to/database.db", new=True)
```

We pass `new=True` to create a new database file.

We can now create a table with sql. Note that we create a column assigned as "PRIMARY KEY". Every table should have one of these columns. It makes sure that every entry has a unique id, so that we can keep track of it.

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

To add an entry use the `add_entry` method.
```python
db.add_entry({"first_name": "John", "last_name": "Smith"}, "people")
```

Let's add a few more!

```python
db.add_entry({"first_name": "Tom", "last_name": "Builder"}, "people")
db.add_entry({"first_name": "Eva", "last_name": "Larson"}, "people")
```

To view to database we can use the `table_overview` method.
```python
db.table_overview("people")
```

*Output:*
```
id ║ first_name ║ last_name
═══╬════════════╬═══════════
1  ║ John       ║ Smith    
2  ║ Tom        ║ Builder  
3  ║ Eva        ║ Larson   
```


### Opening an existing database

Start by importing the class and opening our database.
```python
from sqlite_integrated import Database
db = Database("path/to/database.db")
```

Just to check you can now run.
```python
print(db.overview())
```
This will print list of all tables in the database.


### Editing an entry

We start by getting the entry. In this case the 3rd entry in the table "customers".
```python
entry = db.get_entry_by_id("customers", 3)
```

Now edit as much as you desire!
```python
entry["FirstName"] = "John"
entry["LastName"] = "Newname"
entry["City"] = "Atlantis"
```

To update our table we can simply use the `update_entry` method.

```python
db.update_entry(entry)
```

To save these changes to the database file, use the `save` method.



## More examples

### Viewing a table
```python
from sqlite_integrated import Database

# Loading an existing database
db = Database("path/to/database.db")

db.table_overview("customers", max_len=15, get_only=["FirstName", "LastName", "Address", "City"])
```

*Output:*
```
FirstName ║ LastName     ║ Address                                  ║ City               
══════════╬══════════════╬══════════════════════════════════════════╬════════════════════
Luís      ║ Gonçalves    ║ Av. Brigadeiro Faria Lima, 2170          ║ São José dos Campos
Leonie    ║ Köhler       ║ Theodor-Heuss-Straße 34                  ║ Stuttgart          
François  ║ Tremblay     ║ 1498 rue Bélanger                        ║ Montréal           
Bjørn     ║ Hansen       ║ Ullevålsveien 14                         ║ Oslo               
František ║ Wichterlová  ║ Klanova 9/506                            ║ Prague             
Helena    ║ Holý         ║ Rilská 3174/6                            ║ Prague             
Astrid    ║ Gruber       ║ Rotenturmstraße 4, 1010 Innere Stadt     ║ Vienne             
Daan      ║ Peeters      ║ Grétrystraat 63                          ║ Brussels           
Kara      ║ Nielsen      ║ Sønder Boulevard 51                      ║ Copenhagen         
Eduardo   ║ Martins      ║ Rua Dr. Falcão Filho, 155                ║ São Paulo          
    .
    .
    .
Mark      ║ Taylor       ║ 421 Bourke Street                        ║ Sidney             
Diego     ║ Gutiérrez    ║ 307 Macacha Güemes                       ║ Buenos Aires       
Luis      ║ Rojas        ║ Calle Lira, 198                          ║ Santiago           
Manoj     ║ Pareek       ║ 12,Community Centre                      ║ Delhi              
Puja      ║ Srivastava   ║ 3,Raj Bhavan Road                        ║ Bangalore          

```

### Using queries

#### Select Statement
```python
from sqlite_integrated import Database

# Loading an existing database
db = Database("path/to/database.db")

# Select statement
query = db.SELECT(["FirstName"]).FROM("customers").WHERE("FirstName").LIKE("T%")

# Printing the query
print(f"query: {query}")

# Running the query and printing the results
print(f"Results: {query.run()}")
```

*Output:*
```
query: > SELECT FirstName FROM customers WHERE FirstName LIKE 'T%' <
Executed sql: SELECT FirstName FROM customers WHERE FirstName LIKE 'T%' 
Results: [DatabaseEntry(table: customers, data: {'FirstName': 'Tim'}), DatabaseEntry(table: customers, data: {'FirstName': 'Terhi'})]
```

We can see that there are only two customers with a first name that starts with 't'.

By default the database prints the sql that is executed in the database, to the terminal. This can be disabled by passing `silent=True` to the `run` method.

#### Insert Statement
```python
from sqlite_integrated import Database

# Loading an existing database
db = Database("path/to/database.db")

# Metadata for the entry we are adding
entry = {"FirstName": "Test", "LastName": "Testing", "Email": "test@testing.com"}

# Adding the entry to the table called "customers"
db.INSERT_INTO("customers").VALUES(entry).run()

# A little space
print("\n")

# Print the table 
db.table_overview("customers", get_only=["CustomerId", "FirstName", "LastName", "Email", "Company", "City"], max_len=10)
```

*Output:*
```
Executed sql: INSERT INTO customers (FirstName, LastName, Email) VALUES ('Test', 'Testing', 'test@testing.com') 


CustomerId ║ FirstName ║ LastName     ║ Email                         ║ Company                                          ║ City               
═══════════╬═══════════╬══════════════╬═══════════════════════════════╬══════════════════════════════════════════════════╬══════════════════
1          ║ Luís      ║ Gonçalves    ║ luisg@embraer.com.br          ║ Embraer - Empresa Brasileira de Aeronáutica S.A. ║ São José dos Campos
2          ║ Leonie    ║ Köhler       ║ leonekohler@surfeu.de         ║ None                                             ║ Stuttgart          
3          ║ François  ║ Tremblay     ║ ftremblay@gmail.com           ║ None                                             ║ Montréal           
4          ║ Bjørn     ║ Hansen       ║ bjorn.hansen@yahoo.no         ║ None                                             ║ Oslo               
5          ║ František ║ Wichterlová  ║ frantisekw@jetbrains.com      ║ JetBrains s.r.o.                                 ║ Prague             
    .
    .
    .
56         ║ Diego     ║ Gutiérrez    ║ diego.gutierrez@yahoo.ar      ║ None                                             ║ Buenos Aires       
57         ║ Luis      ║ Rojas        ║ luisrojas@yahoo.cl            ║ None                                             ║ Santiago           
58         ║ Manoj     ║ Pareek       ║ manoj.pareek@rediff.com       ║ None                                             ║ Delhi              
59         ║ Puja      ║ Srivastava   ║ puja_srivastava@yahoo.in      ║ None                                             ║ Bangalore          
60         ║ Test      ║ Testing      ║ test@testing.com              ║ None                                             ║ None               

```

#### Update Statement
```python
from sqlite_integrated import Database

# Loading an existing database
db = Database("path/to/database.db")

# Printing an overview of the customers table
db.table_overview("customers", get_only=["CustomerId", "FirstName", "LastName", "Email", "Company", "City"], max_len=10)

# Some space
print()

# Update all customers with a first name that starts with 'L', so that all their names are now Brian Brianson. 
db.UPDATE("customers").SET({"FirstName": "Brian", "LastName": "Brianson"}).WHERE("FirstName").LIKE("L%").run()

# Some more space
print()

# Printing an overview of the updated customers table
db.table_overview("customers", get_only=["CustomerId", "FirstName", "LastName", "Email", "Company", "City"], max_len=10)
```

*Output:*
```
CustomerId ║ FirstName ║ LastName     ║ Email                         ║ Company                                          ║ City               
═══════════╬═══════════╬══════════════╬═══════════════════════════════╬══════════════════════════════════════════════════╬══════════════════
1          ║ Luís      ║ Gonçalves    ║ luisg@embraer.com.br          ║ Embraer - Empresa Brasileira de Aeronáutica S.A. ║ São José dos Campos
2          ║ Leonie    ║ Köhler       ║ leonekohler@surfeu.de         ║ None                                             ║ Stuttgart          
3          ║ François  ║ Tremblay     ║ ftremblay@gmail.com           ║ None                                             ║ Montréal           
4          ║ Bjørn     ║ Hansen       ║ bjorn.hansen@yahoo.no         ║ None                                             ║ Oslo               
5          ║ František ║ Wichterlová  ║ frantisekw@jetbrains.com      ║ JetBrains s.r.o.                                 ║ Prague             
    .
    .
    .
55         ║ Mark      ║ Taylor       ║ mark.taylor@yahoo.au          ║ None                                             ║ Sidney             
56         ║ Diego     ║ Gutiérrez    ║ diego.gutierrez@yahoo.ar      ║ None                                             ║ Buenos Aires       
57         ║ Luis      ║ Rojas        ║ luisrojas@yahoo.cl            ║ None                                             ║ Santiago           
58         ║ Manoj     ║ Pareek       ║ manoj.pareek@rediff.com       ║ None                                             ║ Delhi              
59         ║ Puja      ║ Srivastava   ║ puja_srivastava@yahoo.in      ║ None                                             ║ Bangalore          


Executed sql: UPDATE customers SET FirstName = 'Brian', LastName = 'Brianson' WHERE FirstName LIKE 'L%' 

CustomerId ║ FirstName ║ LastName     ║ Email                         ║ Company                                          ║ City               
═══════════╬═══════════╬══════════════╬═══════════════════════════════╬══════════════════════════════════════════════════╬══════════════════
1          ║ Brian     ║ Brianson     ║ luisg@embraer.com.br          ║ Embraer - Empresa Brasileira de Aeronáutica S.A. ║ São José dos Campos
2          ║ Brian     ║ Brianson     ║ leonekohler@surfeu.de         ║ None                                             ║ Stuttgart          
3          ║ François  ║ Tremblay     ║ ftremblay@gmail.com           ║ None                                             ║ Montréal           
4          ║ Bjørn     ║ Hansen       ║ bjorn.hansen@yahoo.no         ║ None                                             ║ Oslo               
5          ║ František ║ Wichterlová  ║ frantisekw@jetbrains.com      ║ JetBrains s.r.o.                                 ║ Prague             
    .
    .
    .
55         ║ Mark      ║ Taylor       ║ mark.taylor@yahoo.au          ║ None                                             ║ Sidney             
56         ║ Diego     ║ Gutiérrez    ║ diego.gutierrez@yahoo.ar      ║ None                                             ║ Buenos Aires       
57         ║ Brian     ║ Brianson     ║ luisrojas@yahoo.cl            ║ None                                             ║ Santiago           
58         ║ Manoj     ║ Pareek       ║ manoj.pareek@rediff.com       ║ None                                             ║ Delhi              
59         ║ Puja      ║ Srivastava   ║ puja_srivastava@yahoo.in      ║ None                                             ║ Bangalore          

```

#### Unattached queries
```python
from sqlite_integrated import Database
from sqlite_integrated import Query

# Loading an existing database
db1 = Database("path/to/database.db")

# Loading the same database to a different variable
db2 = Database("path/to/database.db")

# Updating the first entry in the first database only
db1.UPDATE("customers").SET({"FirstName": "Allan", "LastName": "Changed"}).WHERE("CustomerId", 1).run()

# This query gets the first entry in the customers table
query = Query().SELECT().FROM("customers").WHERE("CustomerId = 1")

# Running the query on each database and printing the output.
out1 = query.run(db1)
out2 = query.run(db2)

# Printing the outputs
print(f"\ndb1 output: {out1}")
print(f"\ndb2 output: {out2}")
```

*Output:*
```
Executed sql: UPDATE customers SET FirstName = 'Allan', LastName = 'Changed' WHERE CustomerId = 1
Executed sql: SELECT * FROM customers WHERE CustomerId = 1 
Executed sql: SELECT * FROM customers WHERE CustomerId = 1 

db1 output: [DatabaseEntry(table: customers, data: {'CustomerId': 1, 'FirstName': 'Allan', 'LastName': 'Changed', 'Company': 'Embraer - Empresa Brasileira de Aeronáutica S.A.', 'Address': 'Av. Brigadeiro Faria Lima, 2170', 'City': 'São José dos Campos', 'State': 'SP', 'Country': 'Brazil', 'PostalCode': '12227-000', 'Phone': '+55 (12) 3923-5555', 'Fax': '+55 (12) 3923-5566', 'Email': 'luisg@embraer.com.br', 'SupportRepId': 3})]

db2 output: [DatabaseEntry(table: customers, data: {'CustomerId': 1, 'FirstName': 'Luís', 'LastName': 'Gonçalves', 'Company': 'Embraer - Empresa Brasileira de Aeronáutica S.A.', 'Address': 'Av. Brigadeiro Faria Lima, 2170', 'City': 'São José dos Campos', 'State': 'SP', 'Country': 'Brazil', 'PostalCode': '12227-000', 'Phone': '+55 (12) 3923-5555', 'Fax': '+55 (12) 3923-5566', 'Email': 'luisg@embraer.com.br', 'SupportRepId': 3})]
```

# Contributing
I would be more than happy if anyone finds this useful enough to add to, or modify this code.

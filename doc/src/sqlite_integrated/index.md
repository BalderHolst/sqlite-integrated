Module src.sqlite_integrated
============================

Functions
---------

    
`dict_to_sql(data: dict) ‑> str`
:   Converts a dict into sql key value pairs. Ex: "key1 = value1, key2 = value2..."

    
`raw_table_to_table(raw_table: list, fields: list, table_name: str, id_field)`
:   Convert a raw table (list of tuples) to a table (table of dictionaries)
    
    :param raw_entry: A tuple with the data for the entry. Ex: ´(2, "Tom", "Builder", 33)´
    :param fields: A list of column names for the data. Ex: ´["id", "FirstName", "LastName", "Age"]´
    :param table_name: The name of the table (in the database) that the data belongs to. Ex: "people"
    :param id_field: The name of the column which stores the id. Ex: "id". This can be set to ´None´ but needs to be provided when writing entries back into the database.

    
`string_to_list(string: str) ‑> list`
:   Tankes a string with comma seperated values, returns a list of the values. (spaces are ignored)

    
`value_to_sql_value(value) ‑> str`
:   Converts python values to sql values. Basically just puts quotes around strings and not ints or floats. Also converts None to null

Classes
-------

`Database(path: str, new=False, default_id_field='id', silent=False)`
:   Main database class for manipulating sqlite3 databases
    
    Constructor for Database
    
    :param path:               Path to the database file
    :param new:                A new blank database will be created where the ´self.path´ is pointing
    :param default_id_field:   The default name for the id field in tables
    :param silent:             Disables all feedback in the form of prints

    ### Instance variables

    `conn`
    :   The sqlite3 connection.

    `cursor`
    :   The sqlite3 cursor. Use ´cursor.execute(cmd)´ to execute raw sql

    `default_id_field`
    :   The default name for the id_field in returned DatabaseEntry.

    `path`
    :   Path to the database file.

    `silent`
    :   Disables all feedback in the form of prints.

    ### Methods

    `INSERT_INTO(self, table_name)`
    :   Start sql INSERT INTO query from the database. Returns a Query to build from.
        
        :param table_name: Name of the table.

    `SELECT(self, pattern='*')`
    :   Start sql SELECT query from the database. Returns a Query to build from.
        
        :param pattern: Either a python list or sql list of table names.

    `UPDATE(self, table_name)`
    :   Start sql UPDATE query from the database. Returns a Query to build from.
        
        :param table_name: Name of the table.

    `add_table_entry(self, entry: src.sqlite_integrated.DatabaseEntry, fill_null=False, silent=False)`
    :   Add an entry to the database. The entry must have values for all fields in the table. You can pass ´fill_null=True´ to fill remaining fields with None/null. Use ´silent=True´ to suppress warnings and messages.
        
        :param entry: The entry. The entry must NOT have an id_field (it has to be ´None´: ´entry.id_field = None´).
        :param fill_null: Fill in unpopulated fields with null values.
        :param silent: If True: disables prints.

    `close(self)`
    :   saves and closes the database. If you want to explicitly close without saving use: ´self.conn.close()´

    `fill_null(self, entry: src.sqlite_integrated.DatabaseEntry)`
    :   Fills out any unpopulated fields in a DatabaseEntry (fields that exist in the database but not in the entry).
        
        :param entry: The DatabaseEntry.

    `get_entry_by_id(self, table, ID, id_field=None)`
    :   Get table entry by id.
        
        :param table: Name of the table.
        :param ID: The entry id.
        :param id_field: The field that holds the id value. Will use default if not set.

    `get_table(self, name: str, id_field='', get_only=None, silent=False) ‑> list`
    :   Returns all entries in a table as python dictionaries. This function loops over all entries in the table, so it is not the best in big databases.
        
        :param name: Name of the table.
        :param id_field: The id_field of the table. Will be set to the database default if not set.
        :param get_only: Can be set to a list of column/field names, to only retrieve those columns/fields.

    `get_table_columns(self, name: str)`
    :   Returns the column names for a given table
        
        :param name: Name of the table.

    `get_table_info(self, name: str)`
    :   Returns sql information about a table (runs ´PRAGMA TABLE_INFO(name)´).
        
        :param name: Name of the table.

    `get_table_names(self) ‑> list`
    :   Returns the names of all tables in the database.

    `get_table_raw(self, name: str, get_only=None) ‑> list`
    :   Returns all entries in a table as a list of tuples
        
        :param name: Name of the table.
        :param get_only: Can be set to a list of column/field names, to only retrieve those columns/fields.

    `is_table(self, table_name: str) ‑> bool`
    :   Check if database has a table with a certain name.
        
        :param table_name: Name to check.

    `overview(self)`
    :   Prints an overview of all the tables in the database with their fields.

    `reconnect(self)`
    :   Reopen database after closing it

    `save(self)`
    :   Writes any changes to the database file

    `table_overview(self, name: str, max_len: int = 40, get_only=None)`
    :   Prints a pretty table (with a name).
        
        :param name: Name of the table.
        :param max_len: The max number of rows shown.
        :param get_only: If given a list of column/field names: only shows those

    `update_entry(self, entry: dict, table=None, id_field: str = None, part=False, fill_null=False, silent=False)`
    :   Update entry in database with a DatabaseEntry, or with a dictionary + the name of the table you want to update.
        
        :param entry: DatabaseEntry or dictionary, if dictionary you also need to provide table and id_field.
        :param table: The table name.
        :param id_field: The field that holds the entry id.
        :param part: If True: Only updates the provided fields.
        :param fill_null: Fill in unpopulated fields with null values.
        :param silent: If True: disables prints.

`DatabaseEntry(entry_dict: dict, table: str, id_field)`
:   A python dictionary that keeps track of the table where it came from, and the name and value of its id field. This class is not supposed to be created manually
    
    "
    Constructs the entry by saving the table and id_field as attributes. The ´entry_dict´ is used to populate this object with data.
    
    :param id_field: The column name for the entry's id
    :param table: The name of the table the entry is a part of
    :param entry_dict: A dictionary containing all the information. This information can be accesed just like any other python dict with ´my_entry[my_key]´.

    ### Ancestors (in MRO)

    * builtins.dict

    ### Static methods

    `from_raw_entry(raw_entry: tuple, table_fields: list, table_name: str, id_field)`
    :   Alternative constructor for converting a raw entry to a DatabaseEntry.
        
        :param raw_entry: A tuple with the data for the entry. Ex: ´(2, "Tom", "Builder", 33)´
        :param table_fields: A list of column names for the data. Ex: ´["id", "FirstName", "LastName", "Age"]´
        :param table_name: The name of the table (in the database) that the data belongs to. Ex: "people"
        :param id_field: The name of the column which stores the id. Ex: "id". This can be set to ´None´ but needs to be provided when writing this entry back into the database.

`DatabaseException(*args, **kwargs)`
:   Raised when the database fails to execute command

    ### Ancestors (in MRO)

    * builtins.Exception
    * builtins.BaseException

`Query(db=None)`
:   A class for writing sql queries. Queries can be run on the attached database or a seperate one with the ´run´ method
    
    Initialize query
    
    :param db: The attached Database. This is the default database to run queries on.

    ### Instance variables

    `fields`
    :   The selected fields

    `history`
    :   The history of commandmethods run on this object

    `sql`
    :   The current raw sql command

    `table`
    :   The table the sql query is interacting with

    ### Methods

    `FROM(self, table_name)`
    :   Sql FROM statement. Has to be preceded by a SELECT statement.
        
        :param table_name: Name of the table you are selecting from.

    `INSERT_INTO(self, table_name)`
    :   Sql INSERT INTO statement.
        
        :param table_name: Name of the table you want to insert into.

    `LIKE(self, pattern)`
    :   Sql WHERE statement. Has to be preceded by a WHERE statement.
        
        :param pattern: A typical sql LIKE pattern with % and _.

    `SELECT(self, selection='*')`
    :   Sql SELECT statement.
            
        :param selection: Either a python list or sql list of table names.

    `SET(self, data: dict)`
    :   Sql SET statement. Must be preceded by an UPDATE statement.
        
        :param data: A dictionaty with key and value pairs.

    `UPDATE(self, table_name: str)`
    :   Sql UPDATE statement.
        
        :param table_name: Name of the table you are updating.

    `VALUES(self, data: dict)`
    :   Sql VALUES statement. Must be preceded by INSERT_INTO statement.
        
        :param data: Dictionary with key value pairs.

    `WHERE(self, col_name: str, value='')`
    :   Sql WHERE statement.
        
        :param col_name: The name of the column. You can also just pass it a statement like: ´"id" = 4´ instead of providing a value.
        :param value: The value of the column.

    `run(self, db=None, raw=False)`
    :   Execute the query in the attached database or in a seperate one. Returns the results in a table (list of DatabaseEntry) or ´None´ if no results.
        
        :param db: The database to execute to query on.
        :param raw: If True: returns the raw table (list of tuples) instead of the normal table.

    `valid_prefixes(self, prefixes: list)`
    :   Check if a statement is valid given its prefix
        
        :param prefixs: A list of valid prefixes.

`QueryException(*args, **kwargs)`
:   Raised when trying to create an invalid or unsupperted query

    ### Ancestors (in MRO)

    * builtins.Exception
    * builtins.BaseException
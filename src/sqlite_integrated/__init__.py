__docformat__ = "numpy"

import sqlite3
import os

# TODO testing! (pytest)

def string_to_list(string: str) -> list:
    """Tankes a string with comma seperated values, returns a list of the values. (spaces are ignored)"""

    return(string.replace(" ", "").split(","))

def value_to_sql_value(value) -> str:
    """Converts python values to sql values. Basically just puts quotes around strings and not ints or floats. Also converts None to null"""

    if isinstance(value, str):
        return(value.__repr__())
    elif isinstance(value, int):
        return(str(value))
    elif isinstance(value, float):
        return(str(value))
    elif value == None:
        return("null")
    elif isinstance(value, list):
        try:
            return(",".join(value))
        except TypeError:
            raise TypeError("Cannot convert list on non-string objects to sql")
    else:
        raise TypeError(f"Cannot convert value of type {type(value)} to sql")

def raw_table_to_table(raw_table: list, fields: list, table_name: str, id_field):
    """
    Convert a raw table (list of tuples) to a table (table of dictionaries)

    Parameters
    ----------
    raw_entry
        A tuple with the data for the entry. Ex: ´(2, "Tom", "Builder", 33)´
    fields
        A list of column names for the data. Ex: ´["id", "FirstName", "LastName", "Age"]´
    table_name
        The name of the table (in the database) that the data belongs to. Ex: "people"
    id_field
        The name of the column which stores the id. Ex: "id". This can be set to ´None´ but needs to be provided when writing entries back into the database.
    """

    table = []

    if len(raw_table) == 0:
        return([])
    if len(raw_table[0]) != len(fields):
        raise DatabaseException(f"There must be one raw column per field. {raw_table[0] = }, {fields = }")
    
    for raw_entry in raw_table:
        entry = {}
        for n, field in enumerate(fields):
            entry[field] = raw_entry[n]
        table.append(DatabaseEntry(entry, table_name, id_field))
    return(table)

def dict_to_sql(data: dict) -> str:
    """Converts a dict into sql key value pairs. Ex: \"key1 = value1, key2 = value2...\""""
    
    set_list = []
    for field in data:
        set_list.append(f"{field} = {value_to_sql_value(data[field])}")
    return(", ".join(set_list))


class DatabaseException(Exception):
    """Raised when the database fails to execute command"""

class QueryException(Exception):
    """Raised when trying to create an invalid or unsupperted query"""

# TODO implement JOIN and LEFTJOIN (RIGHTJOIN?): https://www.w3schools.com/sql/sql_join.asp
class Query:
    """A class for writing sql queries. Queries can be run on the attached database or a seperate one with the ´run´ method"""

    def __init__(self, db=None) -> None:
        """
        Initialize query

        :param db: The attached Database. This is the default database to run queries on.
        """
        
        self._db = db
        """The attached Database"""

        self.sql = ""
        """The current raw sql command"""

        self.history = []
        """The history of commandmethods run on this object"""
        
        self.fields = None
        """The selected fields"""

        self.table = None
        """The table the sql query is interacting with"""

    def valid_prefixes(self, prefixes: list):
        """
        Check if a statement is valid given its prefix

        :param prefixs: A list of valid prefixes.
        """

        prefix = None
        if len(self.history) > 0:
            prefix = self.history[-1]
        if prefix in prefixes:
            return(True)
        raise QueryException(f"Query syntax incorrect or not supported. Prefix: \"{prefix}\" is not a part of the valid prefixes: {prefixes}")

    def SELECT(self, selection="*"):
        """
        Sql SELECT statement.
            
        :param selection: Either a python list or sql list of table names.
        """
        
        self.valid_prefixes([None])
        self.history.append("SELECT")

        if isinstance(selection, str):
            if selection == "*":
                self.fields = "*"
            else:
                self.fields = string_to_list(selection)
            self.sql += f"SELECT {selection} "
        elif isinstance(selection, list):
            self.fields = selection
            self.sql += f"SELECT {', '.join(selection)} "
        else:
            raise QueryException("SELECT statement selection must be either ´str´ or ´list´")
        return(self)

    def FROM(self, table_name):
        """
        Sql FROM statement. Has to be preceded by a SELECT statement.

        :param table_name: Name of the table you are selecting from.
        """

        self.valid_prefixes(["SELECT"])
        self.table = table_name

        if self._db:
            table_fields = set(self._db.get_table_columns(table_name)) # check if selected fields are in table

        if not set(self.fields).issubset(table_fields) and self.fields != "*":
            raise QueryException(f"Some selected field(s): {set(self.fields) - table_fields} are not fields/columns in the table: {table_name!r}. The table has the following fields: {table_fields}")

        self.history.append("FROM")
        self.sql += f"FROM {table_name} "
        return(self)

    def WHERE(self, col_name:str, value = ""):
        """
        Sql WHERE statement.

        :param col_name: The name of the column. You can also just pass it a statement like: ´"id" = 4´ instead of providing a value.
        :param value: The value of the column.

        """

        self.valid_prefixes(["FROM", "SET"])
        self.history.append("WHERE")
        if value != "":
            if value == None:
                self.sql += f"WHERE {col_name} is null"
            else:
                self.sql += f"WHERE {col_name} = {value_to_sql_value(value)}"
        else:
            self.sql += f"WHERE {col_name} "
            if col_name.find("=") == -1: # expects LIKE statement
                self.col = col_name.replace(" ", "")
        return(self)

    def LIKE(self, pattern):
        """
        Sql WHERE statement. Has to be preceded by a WHERE statement.

        :param pattern: A typical sql LIKE pattern with % and _.
        """

        self.valid_prefixes(["WHERE"])
        self.history.append("LIKE")
        self.sql += f"LIKE {value_to_sql_value(pattern)} "
        return(self)

    def UPDATE(self, table_name: str):
        """
        Sql UPDATE statement.

        :param table_name: Name of the table you are updating.
        """

        self.valid_prefixes([None])
        self.history.append("UPDATE")
        if self._db:
            if not self._db.is_table(table_name):
                raise QueryException(f"Database has no table called {table_name!r}")
            self.fields = self._db.get_table_columns(table_name)
        self.table = table_name
        self.sql += f"UPDATE {table_name} "
        return(self)

    def SET(self, data: dict):
        """
        Sql SET statement. Must be preceded by an UPDATE statement.

        :param data: A dictionaty with key and value pairs.
        """

        self.valid_prefixes(["UPDATE"])
        self.history.append("SET")

        if not set(data).issubset(self.fields):
            raise DatabaseException(f"Data keys: {set(data)} are not a subset of table fields/columns. Table fields/columns: {set(self.fields)}")
        
        self.sql += f"SET {dict_to_sql(data)} "

        return(self)

    def INSERT_INTO(self, table_name):
        """
        Sql INSERT INTO statement.

        :param table_name: Name of the table you want to insert into.
        """

        self.valid_prefixes([None])
        self.history.append("INSERT_INTO")
        self.table = table_name
        if self._db:
            self.fields = self._db.get_table_columns(table_name)
        self.sql += f"INSERT INTO {table_name} "
        return(self)

    def VALUES(self, data: dict):
        """
        Sql VALUES statement. Must be preceded by INSERT_INTO statement.

        :param data: Dictionary with key value pairs.
        """

        self.valid_prefixes(["INSERT_INTO"])
        self.history.append("VALUES")

        if not set(data).issubset(self.fields):
            raise DatabaseException(f"Data keys: {set(data)} are not a subset of table fields/columns. Unknown keys: {set(data) - set(self.fields)}. Table fields/columns: {set(self.fields)}")

        self.sql += f"({', '.join([str(v) for v in list(data)])}) VALUES ({', '.join([str(value_to_sql_value(v)) for v in data.values()])}) "
        return(self)


    def run(self, db=None, raw = False):
        """
        Execute the query in the attached database or in a seperate one. Returns the results in a table (list of DatabaseEntry) or ´None´ if no results.

        :param db: The database to execute to query on.
        :param raw: If True: returns the raw table (list of tuples) instead of the normal table.
        """

        
        if not db:
            db = self._db

        if not db:
            raise DatabaseException("Query does not have a database to execute")

        try:
            db.cursor.execute(self.sql)
        except sqlite3.OperationalError as e:
            raise QueryException(f"\n\n{e}\n\nError while running following sql: {self.sql}")

        if not db.silent:
            print(f"Executed sql: {self.sql}")

        results = db.cursor.fetchall()

        if len(results) == 0:
            return(None)
        if raw:
            return(results)

        if self.fields == "*":
            self.fields = db.get_table_columns(self.table)

        return(raw_table_to_table(results, self.fields, self.table, None))
    
    def __repr__(self) -> str:
        return(f"> {self.sql.strip()} <")


class DatabaseEntry(dict):
    """A python dictionary that keeps track of the table where it came from, and the name and value of its id field. This class is not supposed to be created manually"""

    def __init__(self, entry_dict: dict, table: str, id_field):
        """"
        Constructs the entry by saving the table and id_field as attributes. The ´entry_dict´ is used to populate this object with data.

        :param id_field: The column name for the entry's id
        :param table: The name of the table the entry is a part of
        :param entry_dict: A dictionary containing all the information. This information can be accesed just like any other python dict with ´my_entry[my_key]´.
        """

        self.id_field = id_field
        self.table = table
        self.update(entry_dict)

        # # check that id_field is in entry
        # if isinstance(id_field, str):
        #     if not id_field in self:
        #         raise DatabaseException(f"id_field: {id_field!r} is not a field in the entry. Entry fields are: {self.keys()}")


    @classmethod
    def from_raw_entry(cls, raw_entry: tuple, table_fields: list, table_name: str, id_field):
        """
        Alternative constructor for converting a raw entry to a DatabaseEntry.
        
        :param raw_entry: A tuple with the data for the entry. Ex: ´(2, "Tom", "Builder", 33)´
        :param table_fields: A list of column names for the data. Ex: ´["id", "FirstName", "LastName", "Age"]´
        :param table_name: The name of the table (in the database) that the data belongs to. Ex: "people"
        :param id_field: The name of the column which stores the id. Ex: "id". This can be set to ´None´ but needs to be provided when writing this entry back into the database.
        """

        entry_dict = {}

        if isinstance(table_fields, str):
            table_fields = string_to_list(table_fields)
        elif not isinstance(table_fields, list):
            raise ValueError(f"table_fields must be either ´list´ or ´str´. Got: {table_fields}")

        if len(raw_entry) != len(table_fields):
            raise DatabaseException(f"There must be as many names for table fields as there are fields in the entry: len({raw_entry}) != len({table_fields}) => {len(raw_entry)} != {len(table_fields)}")
        
        for n, field in enumerate(table_fields):
            entry_dict[field] = raw_entry[n]
        entry = DatabaseEntry(entry_dict, table_name, id_field)
        return(entry)
        

    def __repr__(self) -> str:
        """Represent a Database entry"""

        return f"DatabaseEntry(table: {self.table}, data: {super().__repr__()})"


# TODO implement export to csv
# TODO implement import from csv
class Database:
    """Main database class for manipulating sqlite3 databases"""

    def __init__(self, path: str, new = False, default_id_field="id", silent=False):
        """
        Constructor for Database

        :param path:               Path to the database file
        :param new:                A new blank database will be created where the ´self.path´ is pointing
        :param default_id_field:   The default name for the id field in tables
        :param silent:             Disables all feedback in the form of prints 
        """

        if not new and not os.path.isfile(path):
            raise(DatabaseException(f"no database file at \"{path}\". If you want to create one, pass \"new=True\""))

        self.path = path
        """Path to the database file."""

        self.conn = sqlite3.connect(path)
        """The sqlite3 connection."""

        self.cursor = self.conn.cursor()
        """The sqlite3 cursor. Use ´cursor.execute(cmd)´ to execute raw sql"""

        self.default_id_field = default_id_field
        """The default name for the id_field in returned DatabaseEntry."""

        self.silent=silent
        """Disables all feedback in the form of prints."""

        self.conn.execute("PRAGMA foregin_keys = ON")

    def get_table_names(self) -> list:
        """Returns the names of all tables in the database."""

        res = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        names = []
        for name in res:
            names.append(name[0])
        return(names)
    
    def is_table(self, table_name: str) -> bool:
        """
        Check if database has a table with a certain name.
        
        :param table_name: Name to check.

        """

        if table_name in self.get_table_names():
            return True
        return False

    def get_table_raw(self, name: str, get_only = None) -> list:
        """
        Returns all entries in a table as a list of tuples
        
        :param name: Name of the table.
        :param get_only: Can be set to a list of column/field names, to only retrieve those columns/fields.
        """

        selected = "*"
        
        if get_only:
            if isinstance(get_only, list):
                fields = self.get_table_columns(name)
                for field in get_only:
                    if not field in fields:
                        raise DatabaseException(f"Table \"{name}\" contains no field/column with the name: \"{field}\". Available fields are: {fields}")
                selected = ','.join(get_only)
            else:
                raise ValueError(f"get_only can either be ´None´ or ´list´. Got: {get_only}")
        
        self.cursor.execute(f"SELECT {selected} FROM {name}")
        return(self.cursor.fetchall())

    def get_table(self, name: str, id_field="", get_only=None, silent=False) -> list:
        """
        Returns all entries in a table as python dictionaries. This function loops over all entries in the table, so it is not the best in big databases.

        :param name: Name of the table.
        :param id_field: The id_field of the table. Will be set to the database default if not set.
        :param get_only: Can be set to a list of column/field names, to only retrieve those columns/fields.
        """

        if id_field == "":
            if not self.silent and not silent:
                print(f"Using default id field: {self.default_id_field!r}")
            id_field = self.default_id_field

        raw_table = self.get_table_raw(name, get_only)
            
        return(raw_table_to_table(raw_table, self.get_table_columns(name), name, id_field))


    def get_table_info(self, name: str):
        """
        Returns sql information about a table (runs ´PRAGMA TABLE_INFO(name)´).

        :param name: Name of the table.
        """

        self.cursor.execute(f"PRAGMA table_info({name});")
        return(self.cursor.fetchall())

    def table_overview(self, name: str, max_len:int = 40, get_only = None):
        """
        Prints a pretty table (with a name).

        :param name: Name of the table.
        :param max_len: The max number of rows shown.
        :param get_only: If given a list of column/field names: only shows those
                
        """
        
        text = "" # the output text

        raw_table = self.get_table_raw(name, get_only=get_only)

        if get_only:
            fields = get_only
        else:
            fields = self.get_table_columns(name)

        cols = len(fields)

        longest_words = [0] * cols

        words_table = raw_table + [fields]


        for col in range(cols):
            for entry in words_table:
                if len(str(entry[col])) > longest_words[col]:
                    longest_words[col] = len(str(entry[col])) 

        seperator = " ║ "

        def formatRow(row, longest_words):
            formatted_list = []
            for i, string in enumerate(row):
                string = str(string)
                formatted_list.append(string + " " * (longest_words[i] - len(string)))
            return(seperator.join(formatted_list))
        
        text += formatRow(fields, longest_words) + "\n"
        underline = "═" * (sum(longest_words) + len(seperator))

        # This block is for placing the intersections
        offset = 0
        for n in longest_words[:-1]: # we dont create the an intersection after the last column
            offset += n
            underline = underline[:offset +1] + "╬" + underline[offset:]
            offset += len(seperator)

        text += underline + "\n"

        if len(raw_table) >= max_len:
            for row in raw_table[:max_len-5]:
                text += formatRow(row, longest_words) + "\n"
            text += "    .\n    .\n    .\n"
            for row in raw_table[-5:]:
                text += formatRow(row, longest_words) + "\n"
        else:
            for row in raw_table:
                text += formatRow(row, longest_words) + "\n"
            
        print(text)

    def overview(self):
        """Prints an overview of all the tables in the database with their fields."""

        text = "Tables\n"
        for table_name in self.get_table_names():
            text += "\t" + table_name + "\n"
            for col_name in self.get_table_columns(table_name):
                text += "\t\t" + col_name + "\n"
        print(text)


    def get_table_columns(self, name: str):
        """
        Returns the column names for a given table
        
        :param name: Name of the table.

        """

        keys = []

        for info in self.get_table_info(name):
            keys.append(list(info)[1])
        return(keys)

    def fill_null(self, entry: DatabaseEntry):
            """
            Fills out any unpopulated fields in a DatabaseEntry (fields that exist in the database but not in the entry).

            :param entry: The DatabaseEntry.
            """

            t_fields = self.get_table_columns(entry.table)
            e_fields = list(entry)
            for f in e_fields:
                t_fields.remove(f)
            for null_field in t_fields:
                entry[null_field] = None
            return(entry)


    def get_entry_by_id(self, table, ID, id_field=None):
        """
        Get table entry by id.

        :param table: Name of the table.
        :param ID: The entry id.
        :param id_field: The field that holds the id value. Will use default if not set.
        """

        if not id_field:
            id_field = self.default_id_field

        if not self.is_table(table):
            raise DatabaseException(f"Database contains no table with the name: \"{table}\". These are the available tables: {self.get_table_names()}")

        sql = f"SELECT * FROM {table} WHERE {id_field} = {ID}"

        self.cursor.execute(sql)

        answer = self.cursor.fetchall()

        # some checks
        if len(answer) != 1:
            if len(answer) > 1:
                raise DatabaseException(f"There are more than one entry in table \"{table}\" with an id field \"{id_field}\" with the value \"{id}\": {answer}")
            elif len(answer) == 0:
                raise DatabaseException("There is no entry in table \"{table}\" with an id_field \"{id_field}\" with a value of {ID}")
            else:
                raise DatabaseException("Something went very wrong, please contact the package author") # this will never be run... i think

        return(DatabaseEntry.from_raw_entry(answer[0], self.get_table_columns(table), table, id_field))

    #TODO implement ability to use dicts as well
    def add_table_entry(self, entry: DatabaseEntry, fill_null=False, silent=False):
        """
        Add an entry to the database. The entry must have values for all fields in the table. You can pass ´fill_null=True´ to fill remaining fields with None/null. Use ´silent=True´ to suppress warnings and messages.

        :param entry: The entry. The entry must NOT have an id_field (it has to be ´None´: ´entry.id_field = None´).
        :param fill_null: Fill in unpopulated fields with null values.
        :param silent: If True: disables prints.
        """

        if entry.id_field:
            raise DatabaseException(f"Cannot add entry with a preexisting id ({entry['id']})")

        if not self.is_table(entry.table):
            raise DatabaseException(f"Database has no table with the name \"{self.table}\". Possible tablenames are: {self.get_table_names()}")
        
        table_fields = self.get_table_columns(entry.table)

        if fill_null:
            entry = self.fill_null(entry)

        if set(entry) != set(table_fields):
            raise DatabaseException(f"entry fields are not the same as the table fields: {set(entry)} != {set(table_fields)}")

        def question_marks(n):
            if n == 0:
                return ""
            string = "?"
            for _ in range(n-1):
                string += ",?"
            return(string)

        def get_values(entry):
            keys = entry.keys()
            values = []
            for key in keys:
                values.append(entry[key])
            return(tuple(values))

        keys = tuple(entry.keys())
        values = get_values(entry)
        sql = f"INSERT INTO {entry.table}{keys} VALUES({question_marks(len(keys))})"

        self.cursor.execute(sql, values)

        if not silent:
            print(f"added entry to table \"{entry.table}\": {entry}")


    def update_entry(self, entry: dict, table=None, id_field:str = None, part=False, fill_null=False, silent=False):
        """
        Update entry in database with a DatabaseEntry, or with a dictionary + the name of the table you want to update.

        :param entry: DatabaseEntry or dictionary, if dictionary you also need to provide table and id_field.
        :param table: The table name.
        :param id_field: The field that holds the entry id.
        :param part: If True: Only updates the provided fields.
        :param fill_null: Fill in unpopulated fields with null values.
        :param silent: If True: disables prints.

        """

        if not isinstance(entry, DatabaseEntry): # the input is a dict
            if not table:
                raise DatabaseException(f"Please provide a table when updating an entry with a python dictionary")
            entry = DatabaseEntry(entry, table, id_field) 
        elif id_field:
            entry.id_field = id_field

        if not entry.id_field: # if entry has no id_field set it to the default
            entry.id_field = self.default_id_field

        if not entry.id_field in entry: # check if the id_field is a key to the entry
            raise DatabaseException(f"Cannot update entry as entry has no id in id_field: \"{entry.id_field}\"")

        if not self.is_table(entry.table):
            raise DatabaseException(f"Database has no table with the name \"{entry.table}\". Possible tablenames are: {self.get_table_names()}")

        if fill_null:
            entry = self.fill_null(entry)

        # check that entry fields and table fields match
        table_fields = self.get_table_columns(entry.table)
        if set(table_fields) != set(entry):
            if not (part and set(entry).issubset(set(table_fields))):
                raise DatabaseException(f"Table fields do not match entry fields: {table_fields} != {list(entry)}. Pass ´part = True´ or ´fill_null = True´ if entry are a subset of the table fields")


        data = []

        for field in entry: # translate python objects to sql
            if field != entry.id_field:
                value = entry[field]
                if isinstance(value, str):
                    value = f"\"{value}\""
                if value == None:
                    value = "null"
                data.append(f"{field} = {value}")

        sql = f"UPDATE {entry.table} SET {', '.join(data)} WHERE {entry.id_field} = {entry[entry.id_field]}"

        self.cursor.execute(sql)

        if not silent and not self.silent:
            print(f"updated entry in table \"{entry.table}\": {entry}")

        
    def save(self):
        """Writes any changes to the database file"""

        self.conn.commit()
    
    def close(self):
        """saves and closes the database. If you want to explicitly close without saving use: ´self.conn.close()´"""

        self.conn.commit()
        self.conn.close()

    def reconnect(self):
        """Reopen database after closing it"""

        self.conn = sqlite3.connect(self.path)
        self.cursor = self.conn.cursor()

    def SELECT(self, pattern="*"):
        """
        Start sql SELECT query from the database. Returns a Query to build from.

        :param pattern: Either a python list or sql list of table names.
        """

        return(Query(db=self).SELECT(pattern))

    def UPDATE(self, table_name):
        """
        Start sql UPDATE query from the database. Returns a Query to build from.

        :param table_name: Name of the table.
        """
        return(Query(db=self).UPDATE(table_name))

    def INSERT_INTO(self, table_name):
        """
        Start sql INSERT INTO query from the database. Returns a Query to build from.

        :param table_name: Name of the table.
        """

        return(Query(db=self).INSERT_INTO(table_name))
        
    def __eq__(self, other: object) -> bool:
        tables = self.get_table_names()
        if tables != other.get_table_names():
            return(False)

        for table in tables:
            if self.get_table_raw(table) != other.get_table_raw(table):
                return(False)
            elif self.get_table_info(table) != other.get_table_info(table):
                return(False)

        return(True)

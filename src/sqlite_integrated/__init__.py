import pandas as pd
import sqlite3
import os
from dataclasses import dataclass


@dataclass
class ForeignKey:
    """Class representing an sql foreign key"""

    table: str
    """The table the foreign key points to"""

    to_col: str
    """Column the foreign key points to"""

    from_col: str = None
    """Column in current table, containing the key value"""

    id: int = None
    """The foreign key id"""

    seq: int = None
    """The foreign key sequence attribute"""

    on_update: str = None
    """The action the column will do if the data the key is pointing to changes. (Provide sql action)."""

    on_delete: str = None
    """The action the column will do if the data the key is pointing to changes. (Provide sql action)."""

    match: str = None


    def to_sql(self):
        rep = f"FOREIGN KEY ({self.from_col}) REFERENCES {self.table} ({self.to_col})"
        if self.on_update:
            rep += f" ON UPDATE {self.on_update}"
        if self.on_delete:
            rep += f" ON DELETE {self.on_delete}"
        return(rep)

# TODO check that datatype is integer if col is a primary key
@dataclass
class Column:
    """Class representing en sql column."""

    def __init__(self, name: str, type: str, not_null: bool = None, default_value: any = None, primary_key: bool = False, col_id: int = None, foreign_key: ForeignKey = None) -> None:

        self.name = name
        """Name of the column."""

        self.type = type
        """Type of the data in the column."""

        self.not_null = not_null
        """Sql NOT NULL constraint."""

        self.default_value = default_value
        """Sql DEFAULT. Default value for the column."""

        self.primary_key = primary_key
        """Sql PRIMARY KEY. Automatic column that ensures that every entry has a unique."""

        self.col_id = col_id
        """Id if the column in the table."""
        
        if foreign_key:
            foreign_key.from_col = name

        self.foreign_key = foreign_key
        """ForeignKey object, that representing an sql foreign key."""

    def __repr__(self) -> str:
        attrs = []
        if self.col_id:
            attrs.append(str(self.col_id))
        attrs.append(self.name)
        attrs.append(self.type)
        if self.not_null:
            attrs.append("NOT NULL")
        if self.default_value:
            attrs.append(f"DEFAULT: {self.default_value}")
        if self.primary_key:
            attrs.append("PRIMARY KEY")
        if self.foreign_key:
            attrs.append(self.foreign_key.to_sql())
        return(f"Column({', '.join(attrs)})")


class DatabaseEntry(dict):
    """
    A python dictionary that keeps track of the table it belongs to. This class is not meant to be created manually.

    Parameters
    ----------
    entry_dict : dict
        A dictionary containing all the information. This information can be accesed just like any other python dict with `my_entry[my_key]`.
    table : str
        The name of the table the entry is a part of
    """

    def __init__(self, entry_dict: dict, table: str):
        self.table = table
        self.update(entry_dict)


    @classmethod
    def from_raw_entry(cls, raw_entry: tuple, table_fields: list, table_name: str):
        """
        Alternative constructor for converting a raw entry to a DatabaseEntry.
        
        Parameters
        ----------
        raw_entry : tuple
            A tuple with the data for the entry. Ex: `(2, "Tom", "Builder", 33)`
        table_fields : list
            A list of column names for the data. Ex: `["id", "FirstName", "LastName", "Age"]`
        table_name : str
            The name of the table (in the database) that the data belongs to. Ex: "people"
        """

        entry_dict = {}

        if isinstance(table_fields, str):
            table_fields = string_to_list(table_fields)
        elif not isinstance(table_fields, list):
            raise ValueError(f"table_fields must be either `list` or `str`. Got: {table_fields}")

        if len(raw_entry) != len(table_fields):
            raise DatabaseError(f"There must be as many names for table fields as there are fields in the entry: len({raw_entry}) != len({table_fields}) => {len(raw_entry)} != {len(table_fields)}")
        
        for n, field in enumerate(table_fields):
            entry_dict[field] = raw_entry[n]
        entry = DatabaseEntry(entry_dict, table_name)
        return(entry)
        

    def __repr__(self) -> str:
        """Represent a Database entry"""

        return f"DatabaseEntry(table: {self.table}, data: {super().__repr__()})"


def raw_table_to_table(raw_table: list, fields: list, table_name: str) -> list[DatabaseEntry]:
    """
    Convert a raw table (list of tuples) to a table (list of dictionaries).

    Parameters
    ----------
    raw_table : list
        A list of tuples with the data for the entries.
    fields : list
        A list of column names for the data. Ex: `["id", "FirstName", "LastName", "Age"]`
    table_name: str
        The name of the table (in the database) that the data belongs to. Ex: "people".
    """

    table = []

    if len(raw_table) == 0:
        return([])
    if len(raw_table[0]) != len(fields):
        raise DatabaseError(f"There must be one raw column per field. {raw_table[0] = }, {fields = }")
    
    for raw_entry in raw_table:
        entry = {}
        for n, field in enumerate(fields):
            entry[field] = raw_entry[n]
        table.append(DatabaseEntry(entry, table_name))
    return(table)


def string_to_list(string: str) -> list:
    """Takes a string with comma seperated values, returns a list of the values. (spaces are ignored)"""

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

def dict_to_sql(data: dict) -> str:
    """Converts a dict into sql key value pairs. Ex: \"key1 = value1, key2 = value2...\""""
    
    set_list = []
    for field in data:
        set_list.append(f"{field} = {value_to_sql_value(data[field])}")
    return(", ".join(set_list))


class DatabaseError(Exception):
    """Raised when the database fails to execute command"""

class QueryError(Exception):
    """Raised when trying to create an invalid or unsupperted query"""

# TODO implement JOIN and LEFTJOIN (RIGHTJOIN?): https://www.w3schools.com/sql/sql_join.asp
class Query:
    """
    A class for writing sql queries. Queries can be run on the attached database or a seperate one with the `run` method.

    Parameters
    ----------
    db : Database, optional
        The attached Database. This is the default database to run queries on.
    silent : bool, optional
        If true: disables prints.
    """

    def __init__(self, db=None, silent=False) -> None:
        
        self._db: Database = db
        """The attached Database"""

        self.sql = ""
        """The current raw sql command"""

        self.history = []
        """The history of commandmethods run on this object"""
        
        self.fields = None
        """The selected fields"""

        self.table = None
        """The table the sql query is interacting with"""

        self.silent = silent
        """If true: disables prints"""

    def valid_prefixes(self, prefixes: list) -> None:
        """Check if a statement is valid given its prefix"""

        prefix = None
        if len(self.history) > 0:
            prefix = self.history[-1]
        if prefix in prefixes:
            return(True)
        raise QueryError(f"Query syntax incorrect or not supported. Prefix: \"{prefix}\" is not a part of the valid prefixes: {prefixes}")

    def SELECT(self, selection="*"):
        """
        Sql `SELECT` statement. Must be followed by `FROM` statement.
            
        Parameters
        ----------
        selection : str/list, optional
            Either a python list or sql list of table names. Selects all columns if not set.
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
            raise QueryError("SELECT statement selection must be either `str` or `list`")
        return(self)

    def FROM(self, table_name):
        """
        Sql `FROM` statement. Has to be preceded by a SELECT statement. Can be followed by `WHERE` statement.

        Parameters
        ----------
        table_name : str
            Name of the table you are selecting from.
        """

        self.valid_prefixes(["SELECT"])
        self.table = table_name

        if self._db:
            table_fields = set(self._db.get_column_names(table_name)) # check if selected fields are in table

        if self.fields != "*" and self._db and not set(self.fields).issubset(table_fields):
            raise QueryError(f"Some selected field(s): {set(self.fields) - table_fields} are not fields/columns in the table: {table_name!r}. The table has the following fields: {table_fields}")

        self.history.append("FROM")
        self.sql += f"FROM {table_name} "
        return(self)

    def WHERE(self, col_name:str, value = ""):
        """
        Sql `WHERE` statement. Can be followed by `LIKE` statement.

        Parameters
        ----------
        col_name : str
            The name of the column. You can also just pass it a statement like: `"id" = 4` instead of providing a value.
        value : optional
            The value of the column.
        """

        self.valid_prefixes(["FROM", "SET", "DELETE_FROM"])
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

    def LIKE(self, pattern: str):
        """
        Sql LIKE statement. Has to be preceded by a WHERE statement.

        Parameters
        ----------
        pattern : str
            A typical sql LIKE pattern with % and _.
        """

        self.valid_prefixes(["WHERE"])
        self.history.append("LIKE")
        self.sql += f"LIKE {value_to_sql_value(pattern)} "
        return(self)

    def UPDATE(self, table_name: str):
        """
        Sql UPDATE statement. Must be followed by `SET` statement.

        Parameters
        ----------
        table_name : str
            Name of the table you are updating.
        """

        self.valid_prefixes([None])
        self.history.append("UPDATE")
        if self._db:
            if not self._db.is_table(table_name):
                raise QueryError(f"Database has no table called {table_name!r}")
            self.fields = self._db.get_column_names(table_name)
        self.table = table_name
        self.sql += f"UPDATE {table_name} "
        return(self)

    def SET(self, data: dict):
        """
        Sql SET statement. Must be preceded by an UPDATE statement. Must be followed by `WHERE` statement.

        Parameters
        ----------
        data : dict
            A dictionaty with key and value pairs.
        """

        self.valid_prefixes(["UPDATE"])
        self.history.append("SET")

        data = dict(data)

        if not set(data).issubset(self.fields):
            raise DatabaseError(f"Data keys: {set(data)} are not a subset of table fields/columns. Table fields/columns: {set(self.fields)}")
        
        self.sql += f"SET {dict_to_sql(data)} "

        return(self)

    def INSERT_INTO(self, table_name: str):
        """
        Sql `INSERT INTO` statement. Must be followed by `VALUES` statement.

        Parameters
        ----------
        table_name : str
            Name of the table you want to insert into.
        """

        self.valid_prefixes([None])
        self.history.append("INSERT_INTO")
        self.table = table_name
        if self._db:
            self.fields = self._db.get_column_names(table_name)
        self.sql += f"INSERT INTO {table_name} "
        return(self)

    def VALUES(self, data: dict):
        """
        Sql `VALUES` statement. Must be preceded by INSERT_INTO statement.

        Parameters
        ----------
        data : dict
            Dictionary with key value pairs.
        """

        self.valid_prefixes(["INSERT_INTO"])
        self.history.append("VALUES")

        if not set(data).issubset(self.fields):
            raise DatabaseError(f"Data keys: {set(data)} are not a subset of table fields/columns. Unknown keys: {set(data) - set(self.fields)}. Table fields/columns: {set(self.fields)}")

        self.sql += f"({', '.join([str(v) for v in list(data)])}) VALUES ({', '.join([str(value_to_sql_value(v)) for v in data.values()])}) "
        return(self)

    def DELETE_FROM(self, table_name: str):
        """
        Sql `DELETE FROM` statement. Must be followed by `WHERE` statement.

        Parameters
        ----------
        data : dict
            Dictionary with key value pairs.
        """

        self.valid_prefixes([None])
        self.history.append("DELETE_FROM")
        if self._db and not table_name in self._db.get_table_names():
            raise QueryError(f"Can not perform DELETE FROM on a non-existing table: {table_name!r}")
        self.table = table_name
        self.sql = f"DELETE FROM {table_name} "
        return(self)


    def run(self, db=None, raw = False, silent=False) -> list[DatabaseEntry]:
        """
        Execute the query in the attached database or in a seperate one. Returns the results in a table (list of DatabaseEntry) or `None` if no results.

        Parameters
        ----------
        db : Database, optional
            The database to execute to query on.
        raw : bool, optional
            If True: returns the raw table (list of tuples) instead of the normal table.
        silent : bool, optional
            If True: disables all prints.
        """

        
        if not db:
            db = self._db

        if not db:
            raise DatabaseError("Query does not have a database to execute")

        try:
            db.cursor.execute(self.sql)
        except sqlite3.OperationalError as e:
            raise QueryError(f"\n\n{e}\n\nError while running following sql: {self.sql}")

        if not db.silent and not self.silent and not silent:
            print(f"Executed sql: {self.sql}")

        results = db.cursor.fetchall()

        if len(results) == 0:
            return(None)
        if raw:
            return(results)

        if self.fields == "*":
            self.fields = db.get_column_names(self.table)

        return(raw_table_to_table(results, self.fields, self.table))
    
    def __repr__(self) -> str:
        return(f"> {self.sql.strip()} <")




# TODO Create open bool for the Database
class Database:
    """
    Main database class for manipulating sqlite3 databases.

    Parameters
    ----------
    path : str
        Path to the database file.
    new : bool, optional
        A new blank database will be created where the `self.path` is pointing.
    silent : bool, optional
        Disables all feedback in the form of prints .
    """

    def __init__(self, path: str, new = False, silent=True):

        if not new and not os.path.isfile(path):
            raise(DatabaseError(f"No database file at \"{path}\". If you want to create one, pass \"new=True\""))

        self.path = path
        """Path to the database file."""

        self.conn = sqlite3.connect(path)
        """The sqlite3 connection."""

        self.cursor = self.conn.cursor()
        """The sqlite3 cursor. Use `cursor.execute(cmd)` to execute raw sql."""

        # TODO
        self.connected: bool = True
        """Is true if the Database is connected to a database."""

        self.silent=silent
        """Disables all feedback in the form of prints."""


        self.conn.execute("PRAGMA foreign_keys = ON")

    # TODO respect: on_update, on_delete, match
    def create_table(self, name: str, cols: list[Column]):
        """
        Creates a table in the Database.

        Parameters
        ----------
        name : str
            Name of the new table.
        cols : list[Column]
            List of columns in the new table.
        """

        sql = f"CREATE TABLE {name} (\n"

        foreign_keys: list[ForeignKey] = []

        for col in cols:
            sql += f"{col.name!r} {col.type}"

            if col.primary_key:
                sql += " PRIMARY KEY"
            if col.not_null:
                sql += " NOT NULL"
            if col.default_value:
                sql += f" DEFAULT {col.default_value!r}"
            if col.foreign_key:
                foreign_keys.append(col.foreign_key)
            sql += ",\n"

        for key in foreign_keys:
            sql += f"FOREIGN KEY({key.from_col}) REFERENCES {key.table}({key.to_col}),\n"
            
            if key.on_update:
                sql = sql[:-2] + f"\nON UPDATE {key.on_update},\n"

            if key.on_delete:
                sql = sql[:-2] + f"\nON DELETE {key.on_delete},\n"


        sql = sql[:-2] + "\n)" # remove last ",\n"

        self.cursor.execute(sql)

    def rename_table(self, current_name: str, new_name: str):
        """
        Renames a table in the database.

        Parameters
        ----------
        current_name : str
            Current name of a table.
        new_name : str
            New name of the table.
        """
        self.cursor.execute(f"ALTER TABLE {current_name} RENAME TO {new_name}")


    def delete_table(self, table_name: str) -> None:
        """
        Deletes a table in the database.

        Parameters
        ----------
        table_name : Name of the table.
        """
        self.cursor.execute(f"DROP TABLE {table_name}")

    def add_column(self, table_name: str, col: Column):
        """
        Add column to a table in the database.

        Parameters
        ----------
        table_name : str
            Name of the table.
        col : Column
            The column to add to table.
        """

        # Check that the table exists
        if not self.is_table(table_name):
            raise DatabaseError(f"Database contains no table with the name {table_name!r}")

        sql = f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col.type}" 

        if col.primary_key:
            sql += " PRIMARY KEY"
        if col.not_null:
            sql += " NOT NULL"
        if col.default_value:
            sql += f" DEFAULT {col.default_value}"
        if col.foreign_key:
            raise DatabaseError(f"Sqlite3 and therefore sqlite-integrated, does not support adding columns with foreign key constraings to existing tables. They have to be declared with the creation of the table.")

        self.cursor.execute(sql)

    def rename_column(self, table_name: str, current_column_name: str, new_column_name: str):
        """
        Renames a column in the database.

        Parameters
        ----------
        table_name : str
            Name of the table.
        current_column_name : str
            Current name of a column.
        new_column_name : str
            New name of the column.
        """

        # Check that the table exists
        if not self.is_table(table_name):
            raise DatabaseError(f"Database contains no table with the name {table_name!r}")

        self.cursor.execute(f"ALTER TABLE {table_name} RENAME COLUMN {current_column_name} TO {new_column_name}")

    def delete_column(self, table_name: str, col):
        """
        Deletes a column in a table.

        Parameters
        ----------
        table_name : str
            Name of the table the column is in.
        col : str/Column
            Column, or column name, of the column that should be deleted.
        """

        # Check that the table exists
        if not self.is_table(table_name):
            raise DatabaseError(f"Database contains no table with the name {table_name!r}")

        if col is Column:
            col = col.name

        self.cursor.execute(f"ALTER TABLE {table_name} DROP COLUMN {col}")
    


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
        
        Parameters
        ----------
        table_name : str
            Name to check.

        """

        if table_name in self.get_table_names():
            return True
        return False

    def get_table_raw(self, name: str, get_only = None) -> list:
        """
        Returns all entries in a table as a list of tuples.
        
        Parameters
        ----------
        name : str
            Name of the table.
        get_only : list, optional
            Can be set to a list of column/field names, to only retrieve those columns/fields.
        """

        selected = "*"
        
        if get_only:
            if isinstance(get_only, list):
                fields = self.get_column_names(name)
                for field in get_only:
                    if not field in fields:
                        raise DatabaseError(f"Table \"{name}\" contains no field/column with the name: \"{field}\". Available fields are: {fields}")
                selected = ','.join(get_only)
            else:
                raise ValueError(f"get_only can either be `None` or `list`. Got: {get_only}")
        
        self.cursor.execute(f"SELECT {selected} FROM {name}")
        return(self.cursor.fetchall())

    def get_table(self, name: str, get_only=None) -> list:
        """
        Returns all entries in a table as a table (list of DatabaseEntry). This function loops over all entries in the table, so it is not the best in very big databases.

        Parameters
        ----------
        name : str
            Name of the table.
        get_only : list/None, optional
            Can be set to a list of column/field names, to only retrieve those columns/fields.
        """

        raw_table = self.get_table_raw(name, get_only)
            
        return(raw_table_to_table(raw_table, self.get_column_names(name), name))


    def get_table_cols(self, name: str) -> list[Column]:
        """
        Returns a list of Column objects, that contain information about the table columns.

        Parameters 
        ----------
        name : str
            Name of the table.
        """

        self.cursor.execute(f"PRAGMA table_info({name});")
        cols_raw_info = self.cursor.fetchall()

        cols = []
        for col_raw_info in cols_raw_info:
            is_primary = False
            if col_raw_info[5] == 1:
                is_primary = True
            not_null = False
            if col_raw_info[3] == 1:
                not_null = True
            cols.append(Column(col_raw_info[1], col_raw_info[2], not_null, col_raw_info[4], is_primary, col_id=col_raw_info[0]))

        
        # Add foreign keys to cols
        self.cursor.execute(f"PRAGMA foreign_key_list({name});")
        foreign_key_list = self.cursor.fetchall()

        if len(foreign_key_list) > 0:
            for raw_foreign_key in foreign_key_list:
                foreign_key = ForeignKey(
                        raw_foreign_key[2],
                        raw_foreign_key[4],
                        id=raw_foreign_key[0],
                        seq=raw_foreign_key[1],
                        from_col=raw_foreign_key[3],
                        on_update=raw_foreign_key[5],
                        on_delete=raw_foreign_key[6],
                        match=raw_foreign_key[7]
                        )

                for n, col in enumerate(cols):
                    if col.name == foreign_key.from_col:
                        cols[n].foreign_key = foreign_key
                        break
        return(cols)

    def get_table_id_field(self, table: str, do_error=False) -> str:
        """
        Takes a table and returns the name of the field/column marked as a `PRIMARY KEY`. (This function assumes that there is only ONE field marked as a `PRIMARY KEY`).

        Parameters
        ----------
        table : str
            Name of the table.
        do_error : bool, optional
            If True: Raises error if the table does not contain a field marked as `PRIMARY KEY`.
        """

        cols = self.get_table_cols(table)

        for col in cols:
            if col.primary_key == True: # col_info[5] is 1 if field is a primary key. Otherwise it is 0.
                return col.name # col_info[1] is the name of the column
        if do_error:
            raise DatabaseError(f"The table `{table}` has no id_field (column defined as a `PRIMARY KEY`)")
        return(None) 

    def table_overview(self, name: str, max_len:int = 40, get_only = None) -> None:
        """
        Prints a pretty table (with a name).

        Parameters
        ----------
        name : str
            Name of the table.
        max_len : int, optional
            The max number of rows shown.
        get_only : list, optional
            If given a list of column/field names: only shows those.
                
        """
        
        text = "" # the output text

        raw_table = self.get_table_raw(name, get_only=get_only)

        if get_only:
            fields = get_only
        else:
            fields = self.get_column_names(name)

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

    def overview(self, more=False) -> None:
        """
        Prints an overview of all the tables in the database with their fields.

        Parameters
        ----------
        more : optional
            If true: Prints more information on the columns in each table.
        """

        table_names = self.get_table_names()

        # if there are no tables in database
        if len(table_names) == 0:
            print(f"There are no tables in sqlite database at \"{self.path}\".")
            return(None)

        text = "Tables\n"
        for table_name in table_names:
            text += "\t" + table_name + "\n"
            for col in self.get_table_cols(table_name):
                text += f"\t\t{col.name}"
                if more:
                    text += f"\t\t[{col}]"
                text += "\n"
        print(text)


    def get_column_names(self, table_name: str) -> list[str]:
        """
        Returns the field/column names for a given table.
        
        Parameters
        ----------
        table_name : str
            Name of the table.
        """

        if not self.is_table(table_name):
            raise DatabaseError(f"Can not get column names of non-existing table {table_name!r}.")

        names = []

        for col in self.get_table_cols(table_name):
            names.append(col.name)
        return(names)
    
    def is_column(self, table_name: str, col_name: str) -> bool:
        """
        Returns True if the given column name exists in the given table. Else returns False.

        Parameters
        ----------
        table_name : str
            Name of a table.
        col_name : str
            Name of a column that may be in the table.
        """

        if col_name in self.get_column_names(table_name):
            return(True)
        return(False)

    def fill_null(self, entry: DatabaseEntry) -> DatabaseEntry:
        """
        Fills out any unpopulated fields in a DatabaseEntry (fields that exist in the database table but not in the entry) and returns it.

        Parameters
        ----------
        entry : DatabaseEntry
            The DatabaseEntry.
        """

        t_fields = self.get_column_names(entry.table)
        e_fields = list(entry)
        for f in e_fields:
            t_fields.remove(f)
        for null_field in t_fields:
            entry[null_field] = None
        return(entry)


    def get_entry_by_id(self, table, ID) -> DatabaseEntry:
        """
        Get table entry by id.

        Parameters
        ----------
        table : str
            Name of the table.
        ID :  
            The entry id.
        """

        id_field = self.get_table_id_field(table, do_error=True)

        if not self.is_table(table):
            raise DatabaseError(f"Database contains no table with the name: \"{table}\". These are the available tables: {self.get_table_names()}")

        sql = f"SELECT * FROM {table} WHERE {id_field} = {ID}"

        self.cursor.execute(sql)

        answer = self.cursor.fetchall()

        # some checks
        if len(answer) != 1:
            if len(answer) > 1:
                raise DatabaseError(f"There are more than one entry in table \"{table}\" with an id field \"{id_field}\" with the value \"{id}\": {answer}")
            elif len(answer) == 0:
                raise DatabaseError(f"There is no entry in table \"{table}\" with an id_field \"{id_field}\" with a value of {ID}")
            else:
                raise DatabaseError("Something went very wrong, please contact the package author") # this will never be run... i think

        return(DatabaseEntry.from_raw_entry(answer[0], self.get_column_names(table), table))

    def add_entry(self, entry, table = None, fill_null=False, silent=False) -> None:
        """
        Add an entry to the database by passing a DatabaseEntry, or with a dictionary and specifying a table name. The entry must have values for all fields in the table. You can pass `fill_null=True` to fill remaining fields with None/null. Use `silent=True` to suppress warnings and messages.

        Parameters
        ----------
        entry : DatabaseEntry/dict
            The entry.
        table : str, optional
            Name of the table the entry belongs to. **Needed if adding an entry with a dictionary**.
        fill_null : bool, optional
            Fill in unpopulated fields with null values.
        silent : bool, optional
            If True: disables prints.
        """

        if type(entry) == dict:
            if not table:
                raise DatabaseError(f"Please provide the table that the data should be inserted in.")
            entry = DatabaseEntry(entry, table)

        if not self.is_table(entry.table):
            raise DatabaseError(f"Database has no table with the name \"{self.table}\". Possible tablenames are: {self.get_table_names()}")
        
        table_fields = self.get_column_names(entry.table)

        id_field = self.get_table_id_field(entry.table)

        if id_field:
            entry[id_field] = None
        

        if fill_null:
            entry = self.fill_null(entry)

        if set(entry) != set(table_fields):
            raise DatabaseError(f"entry fields are not the same as the table fields: {set(entry)} != {set(table_fields)}")

        self.INSERT_INTO(entry.table).VALUES(entry).run(silent=True)

        if not silent and not self.silent:
            print(f"added entry to table \"{entry.table}\": {entry}")


    def update_entry(self, entry: dict, table=None, part=False, fill_null=False, silent=False) -> None:
        """
        Update entry in database with a DatabaseEntry, or with a dictionary + the name of the table you want to update.

        Parameters
        ----------
        entry : DatabaseEntry/dict
            DatabaseEntry or dictionary, if dictionary you also need to provide table and id_field.
        table : str, optional
            The table name. **Needed if updating an entry with a dictionary**.
        part : bool, optional
            If True: Only updates the provided fields.
        fill_null : bool, optional
            Fill in unpopulated fields with null values.
        silent : bool, optional
            If True: disables prints.
        """

        if not isinstance(entry, DatabaseEntry): # the input is a dict
            if not table:
                raise DatabaseError(f"Please provide a table when updating an entry with a python dictionary")
            entry = DatabaseEntry(entry, table) 

        id_field = self.get_table_id_field(entry.table)

        if not self.is_table(entry.table):
            raise DatabaseError(f"Database has no table with the name \"{entry.table}\". Possible tablenames are: {self.get_table_names()}")

        if fill_null:
            entry = self.fill_null(entry)

        # check that entry fields and table fields match
        table_fields = self.get_column_names(entry.table)
        if set(table_fields) != set(entry):
            if not (part and set(entry).issubset(set(table_fields))):
                raise DatabaseError(f"Table fields do not match entry fields: {table_fields} != {list(entry)}. Pass `part = True` or `fill_null = True` if entry are a subset of the table fields")

        self.UPDATE(entry.table).SET(entry).WHERE(id_field, entry[id_field]).run()

        if not silent and not self.silent:
            print(f"updated entry in table \"{entry.table}\": {entry}")

    def delete_entry(self, entry: DatabaseEntry):
        """
        Delete an entry from the database.
        
        Parameters
        ----------
        entry : DatabaseEntry
            The entry that is to be deleted.
        """

        id_field = self.get_table_id_field(entry.table)
        self.DELETE_FROM(entry.table).WHERE(id_field, entry[id_field]).run()


    def delete_entry_by_id(self, table: str, id: int):
        """
        Deletes an entry with a certain id. (Note: the table must have a primary key column, as that is what is meant by id. It is assumed that there is only one primary key column in the table.}

        Parameters
        ----------
        table : str
            The table to delete the entry from.
        id : int
            
        """

        id_field = self.get_table_id_field(table)
        self.DELETE_FROM(table).WHERE(id_field, id).run()
        
    def save(self) -> None:
        """Writes any changes to the database file"""

        self.conn.commit()
    
    def close(self) -> None:
        """Saves and closes the database. If you want to explicitly close without saving use: `self.conn.close()`"""

        self.conn.commit()
        self.conn.close()

    def reconnect(self) -> None:
        """Reopen database after closing it"""

        self.conn = sqlite3.connect(self.path)
        self.cursor = self.conn.cursor()

    def delete_table(self, table_name) -> None:
        """
        Takes a table name and deletes the table from the database.

        Parameters
        ----------
        table_name : str
            Name of the table.
        """

        self.cursor.execute(f"DROP TABLE {table_name};")

    def table_to_dataframe(self, table) -> pd.DataFrame:
        """
        Converts a table to a pandas.Dataframe.

        Parameters
        ----------
        table : str
            Name of the table.
        """

        cols = {}
        fields = self.get_column_names(table)

        for f in fields:
            cols[f] = []

        for raw_entry in self.get_table_raw(table):
            for n, field in enumerate(fields):
                cols[field].append(raw_entry[n])

        return(pd.DataFrame(cols))


    def export_to_csv(self, out_dir: str, tables: list = None, sep: str = "\t") -> None:
        """
        Export all or some tables in the database to csv files

        Parameters
        ----------
        out_dir : str
            Path to the output directory.
        tables : list[str]/None, optional
            Can be set to only export certain tables.
        sep : str, optional
            Seperator to use when writing csv-file.
        """

        if not os.path.isdir(out_dir):
            raise NotADirectoryError(f"{out_dir!r} is not a directory")

        if not tables:
            tables = self.get_table_names()

        for table_name in tables:
            df = self.table_to_dataframe(table_name)
            df.to_csv(f"{out_dir}/{table_name}.csv", index=False, sep=sep)


    def SELECT(self, pattern="*") -> Query:
        """
        Start sql SELECT query from the database. Returns a Query to build from.

        Parameters
        ----------
        pattern : str, optional
            Either a python list or sql list of table names.
        """

        return(Query(db=self, silent=True).SELECT(pattern))

    def UPDATE(self, table_name) -> Query:
        """
        Start sql UPDATE query from the database. Returns a Query to build from.

        Parameters
        ----------
        table_name : str
            Name of the table.
        """
        return(Query(db=self, silent=True).UPDATE(table_name))

    def INSERT_INTO(self, table_name) -> Query:
        """
        Start sql INSERT INTO query from the database. Returns a Query to build from.

        Parameters
        ----------
        table_name : str
            Name of the table to insert into.
        """

        return(Query(db=self, silent=True).INSERT_INTO(table_name))
    
    def DELETE_FROM(self, table_name: str) -> Query:
        """
        Start sql DELETE FROM query from the database. Returns a Query to build from.

        Parameters
        ----------
        table_name : str
            Name of the table to delete from.
        """
        return(Query(db=self, silent=True).DELETE_FROM(table_name))

        
    def __eq__(self, other: object) -> bool:
        tables = self.get_table_names()
        if tables != other.get_table_names():
            return(False)

        for table in tables:
            if self.get_table_raw(table) != other.get_table_raw(table):
                return(False)
            elif self.get_table_cols(table) != other.get_table_cols(table):
                return(False)
        return(True)

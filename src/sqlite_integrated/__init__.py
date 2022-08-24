import pandas as pd
import numpy
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

def raw_table_to_table(raw_table: list, fields: list, table_name: str):
    """
    Convert a raw table (list of tuples) to a table (table of dictionaries)

    Parameters
    ----------
    raw_table : list
        A tuple with the data for the entry. Ex: ´(2, "Tom", "Builder", 33)´
    fields : list
        A list of column names for the data. Ex: ´["id", "FirstName", "LastName", "Age"]´
    table_name: str
        The name of the table (in the database) that the data belongs to. Ex: "people"
    id_field: str
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
        table.append(DatabaseEntry(entry, table_name))
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
    """
    A class for writing sql queries. Queries can be run on the attached database or a seperate one with the ´run´ method

    Parameters
    ----------
    db : Database, optional
        The attached Database. This is the default database to run queries on.
    """

    def __init__(self, db=None) -> None:
        
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
        """Check if a statement is valid given its prefix"""

        prefix = None
        if len(self.history) > 0:
            prefix = self.history[-1]
        if prefix in prefixes:
            return(True)
        raise QueryException(f"Query syntax incorrect or not supported. Prefix: \"{prefix}\" is not a part of the valid prefixes: {prefixes}")

    def SELECT(self, selection="*"):
        """
        Sql SELECT statement.
            
        Parameters
        ----------
        selection : str/list
            Either a python list or sql list of table names.
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

        Parameters
        ----------
        table_name :
            Name of the table you are selecting from.
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

        Parameters
        ----------
        col_name : str
            The name of the column. You can also just pass it a statement like: ´"id" = 4´ instead of providing a value.
        value : optional
            The value of the column.
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

    def LIKE(self, pattern: str):
        """
        Sql WHERE statement. Has to be preceded by a WHERE statement.

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
        Sql UPDATE statement.

        Parameters
        ----------
        table_name : str
            Name of the table you are updating.
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

        Parameters
        ----------
        data : dict
            A dictionaty with key and value pairs.
        """

        self.valid_prefixes(["UPDATE"])
        self.history.append("SET")

        if not set(data).issubset(self.fields):
            raise DatabaseException(f"Data keys: {set(data)} are not a subset of table fields/columns. Table fields/columns: {set(self.fields)}")
        
        self.sql += f"SET {dict_to_sql(data)} "

        return(self)

    def INSERT_INTO(self, table_name: str):
        """
        Sql INSERT INTO statement.

        Parameters
        ----------
        table_name : str
            Name of the table you want to insert into.
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

        Parameters
        ----------
        data : dict
            Dictionary with key value pairs.
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

        Parameters
        ----------
        db : Database, optional
            The database to execute to query on.
        raw : bool, optional
            If True: returns the raw table (list of tuples) instead of the normal table.
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

        return(raw_table_to_table(results, self.fields, self.table))
    
    def __repr__(self) -> str:
        return(f"> {self.sql.strip()} <")


class DatabaseEntry(dict):
    """
    A python dictionary that keeps track of the table where it came from, and the name and value of its id field. This class is not supposed to be created manually
    
    Constructs the entry by saving the table and id_field as attributes. The ´entry_dict´ is used to populate this object with data.

    Parameters
    ----------
    entry_dict : dict
        A dictionary containing all the information. This information can be accesed just like any other python dict with ´my_entry[my_key]´.
    table : str
        The name of the table the entry is a part of
    id_field : str/None
        The column name for the entry's id
    """

    def __init__(self, entry_dict: dict, table: str, id_field=69):

        if id_field != 69:
            print("DatabaseEntry called with id_field")

        self.table = table
        self.update(entry_dict)


    @classmethod
    def from_raw_entry(cls, raw_entry: tuple, table_fields: list, table_name: str):
        """
        Alternative constructor for converting a raw entry to a DatabaseEntry.
        
        Parameters
        ----------
        raw_entry : tuple
            A tuple with the data for the entry. Ex: ´(2, "Tom", "Builder", 33)´
        table_fields : list
            A list of column names for the data. Ex: ´["id", "FirstName", "LastName", "Age"]´
        table_name : str
            The name of the table (in the database) that the data belongs to. Ex: "people"
        id_field : str/None
            The name of the column which stores the id. Ex: "id". This can be set to ´None´ but needs to be provided when writing this entry back into the database.
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
        entry = DatabaseEntry(entry_dict, table_name)
        return(entry)
        

    def __repr__(self) -> str:
        """Represent a Database entry"""

        return f"DatabaseEntry(table: {self.table}, data: {super().__repr__()})"


# TODO implement import from csv
# TODO rewrite sql queries with Query class
class Database:
    """
    Main database class for manipulating sqlite3 databases

    Parameters
    ----------
    path : str
        Path to the database file
    new : bool, optional
        A new blank database will be created where the ´self.path´ is pointing
    default_id_field : str, optional
        The default name for the id field in tables
    silent : bool, optional
        Disables all feedback in the form of prints 
    """

    def __init__(self, path: str, new = False, silent=False):

        if not new and not os.path.isfile(path):
            raise(DatabaseException(f"no database file at \"{path}\". If you want to create one, pass \"new=True\""))

        self.path = path
        """Path to the database file."""

        self.conn = sqlite3.connect(path)
        """The sqlite3 connection."""

        self.cursor = self.conn.cursor()
        """The sqlite3 cursor. Use ´cursor.execute(cmd)´ to execute raw sql"""

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
        Returns all entries in a table as a list of tuples
        
        Parameters
        ----------
        name : str
            Name of the table.
        get_only : list/None
            Can be set to a list of column/field names, to only retrieve those columns/fields.
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

    def get_table(self, name: str, get_only=None, silent=False) -> list:
        """
        Returns all entries in a table as python dictionaries. This function loops over all entries in the table, so it is not the best in big databases.

        Parameters
        ----------
            Name of the table.
        id_field : str, optional
            The id_field of the table. Will be set to the database default if not set.
        get_only : list/None, optional
            Can be set to a list of column/field names, to only retrieve those columns/fields.
        silent : bool, optional
            Disables prints if True
        """

        raw_table = self.get_table_raw(name, get_only)
            
        return(raw_table_to_table(raw_table, self.get_table_columns(name), name))


    def get_table_info(self, name: str):
        """
        Returns sql information about a table (runs ´PRAGMA TABLE_INFO(name)´).

        Parameters 
        -----------
        name : str
            Name of the table.
        """

        self.cursor.execute(f"PRAGMA table_info({name});")
        return(self.cursor.fetchall())

    # TODO docs
    # This function assumes that there is only one primary key in a table
    def get_table_id_field(self, table, do_error=False):
        cols_info = self.get_table_info(table)

        for col_info in cols_info:
            if col_info[5] == 1: # col_info[5] is 1 if field is a primary key. Otherwise it is 0.
                return col_info[1] # col_info[1] is the name of the column
        if do_error:
            raise DatabaseException(f"The table `{table}` has no id_field (column defined as a `PRIMARY KEY`)")
        return(None) 

    def table_overview(self, name: str, max_len:int = 40, get_only = None):
        """
        Prints a pretty table (with a name).

        Parameters
        ----------
        name : str
            Name of the table.
        max_len : int, optional
            The max number of rows shown.
        get_only : list/None, optional
            If given a list of column/field names: only shows those
                
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
        
        Parameters
        ----------
        name : str
            Name of the table.

        """

        keys = []

        for info in self.get_table_info(name):
            keys.append(list(info)[1])
        return(keys)

    def fill_null(self, entry: DatabaseEntry):
        """
        Fills out any unpopulated fields in a DatabaseEntry (fields that exist in the database but not in the entry).

        Parameters
        ----------
        entry : DatabaseEntry
            The DatabaseEntry.
        """

        t_fields = self.get_table_columns(entry.table)
        e_fields = list(entry)
        for f in e_fields:
            t_fields.remove(f)
        for null_field in t_fields:
            entry[null_field] = None
        return(entry)


    def get_entry_by_id(self, table, ID):
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
            raise DatabaseException(f"Database contains no table with the name: \"{table}\". These are the available tables: {self.get_table_names()}")

        sql = f"SELECT * FROM {table} WHERE {id_field} = {ID}"

        self.cursor.execute(sql)

        answer = self.cursor.fetchall()

        # some checks
        if len(answer) != 1:
            if len(answer) > 1:
                raise DatabaseException(f"There are more than one entry in table \"{table}\" with an id field \"{id_field}\" with the value \"{id}\": {answer}")
            elif len(answer) == 0:
                raise DatabaseException(f"There is no entry in table \"{table}\" with an id_field \"{id_field}\" with a value of {ID}")
            else:
                raise DatabaseException("Something went very wrong, please contact the package author") # this will never be run... i think

        return(DatabaseEntry.from_raw_entry(answer[0], self.get_table_columns(table), table))

    #TODO implement ability to use dicts as well
    # TODO update docs
    def add_table_entry(self, entry, table = None, fill_null=False, silent=False):
        """
        Add an entry to the database. The entry must have values for all fields in the table. You can pass ´fill_null=True´ to fill remaining fields with None/null. Use ´silent=True´ to suppress warnings and messages.

        Parameters
        ---------------------
        entry : DatabaseEntry/dict
            The entry. The entry must NOT have an id_field (it has to be ´None´: ´entry.id_field = None´).
        fill_null : bool, optional
            Fill in unpopulated fields with null values.
        silent : bool, optional
            If True: disables prints.
        """

        if type(entry) == dict:
            entry = DatabaseEntry(entry, table)
            fill_null = True # TODO this is a bodge. Maybe make a Table class to hold id_fields.

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


    def update_entry(self, entry: dict, table=None, part=False, fill_null=False, silent=False):
        """
        Update entry in database with a DatabaseEntry, or with a dictionary + the name of the table you want to update.

        Parameters
        ----------
        entry : DatabaseEntry/dict
            DatabaseEntry or dictionary, if dictionary you also need to provide table and id_field.
        table : str, optional
            The table name.
        id_field : str/None, optional
            The field that holds the entry id.
        part : bool, optional
            If True: Only updates the provided fields.
        fill_null : bool, optional
            Fill in unpopulated fields with null values.
        silent : bool, optional
            If True: disables prints.

        """

        if not isinstance(entry, DatabaseEntry): # the input is a dict
            if not table:
                raise DatabaseException(f"Please provide a table when updating an entry with a python dictionary")
            entry = DatabaseEntry(entry, table) 

        id_field = self.get_table_id_field(entry.table)

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
            if field != id_field:
                value = entry[field]
                if isinstance(value, str):
                    value = f"\"{value}\""
                if value == None:
                    value = "null"
                data.append(f"{field} = {value}")

        sql = f"UPDATE {entry.table} SET {', '.join(data)} WHERE {id_field} = {entry[id_field]}"

        self.cursor.execute(sql)

        if not silent and not self.silent:
            print(f"updated entry in table \"{entry.table}\": {entry}")

        
    def save(self):
        """Writes any changes to the database file"""

        self.conn.commit()
    
    def close(self):
        """Saves and closes the database. If you want to explicitly close without saving use: ´self.conn.close()´"""

        self.conn.commit()
        self.conn.close()

    def reconnect(self):
        """Reopen database after closing it"""

        self.conn = sqlite3.connect(self.path)
        self.cursor = self.conn.cursor()

    def delete_table(self, table_name):
        self.cursor.execute(f"DROP TABLE {table_name};")

    # TODO documentation
    def table_to_dataframe(self, table) -> pd.DataFrame:
        cols = {}
        fields = self.get_table_columns(table)

        for f in fields:
            cols[f] = []

        for raw_entry in self.get_table_raw(table):
            for n, field in enumerate(fields):
                cols[field].append(raw_entry[n])

        return(pd.DataFrame(cols))

    # TODO add docs
    def dataframe_to_table(self, table_name, dataframe, options=None):

        # TODO
        if options:
            raise NotImplementedError
        
        fields = dataframe.keys()

        col_types = []

        # TODO add more types
        for field in fields:
            value = dataframe[field][0]
            if isinstance(value, numpy.int64):
                col_types.append("INTEGER")
            elif isinstance(value, str):
                col_types.append("TEXT")
            else:
                raise TypeError(f"Cannot convert value of type ´{type(value)}´ to sql. Value: {value}.")

        col_pairs = []

        for n, col in enumerate(fields):
            col_type = col_types[n]
            col_pairs.append(f"{col} {col_type}")

        cols = ',\n'.join(col_pairs)

        sql = f"CREATE TABLE {table_name} (\n{cols}\n)"

        self.cursor.execute(sql)

        for df_entry in dataframe.iloc:
            df_entry = dict(df_entry)
            for n, type in enumerate(col_types): 
                if type == "INTEGER": # Convert to normal python int (from numpy.int64)
                    df_entry[fields[n]] = int(df_entry[fields[n]])
            entry = DatabaseEntry(df_entry, table_name, None)
            self.add_table_entry(entry, silent=True)



    def export_to_csv(self, out_dir: str, tables: list = None, sep: str = "\t"):
        """
        Export all or some tables in the database to csv files

        Parameters
        ----------
        out_dir : str
            Path to the output directory
        tables : list[str]/None, optional
            Can be set to only export certain tables
        sep : str, optional
            Seperator to use when writing csv-file
        """

        if not os.path.isdir(out_dir):
            raise NotADirectoryError(f"{out_dir!r} is not a directory")

        if not tables:
            tables = self.get_table_names()

        for table_name in tables:
            df = self.table_to_dataframe(table_name)
            df.to_csv(f"{out_dir}/{table_name}.csv", index=False, sep=sep)


    def SELECT(self, pattern="*"):
        """
        Start sql SELECT query from the database. Returns a Query to build from.

        Parameters
        ----------
        pattern : str, optional
            Either a python list or sql list of table names.
        """

        return(Query(db=self).SELECT(pattern))

    def UPDATE(self, table_name):
        """
        Start sql UPDATE query from the database. Returns a Query to build from.

        Parameters
        ----------
        table_name : str
            Name of the table.
        """
        return(Query(db=self).UPDATE(table_name))

    def INSERT_INTO(self, table_name):
        """
        Start sql INSERT INTO query from the database. Returns a Query to build from.

        Parameters
        ----------
        table_name : str
            Name of the table.
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

if __name__ == "__main__":
    db = Database("tests/test.db")

    print(db.get_table_id_field("customers"))


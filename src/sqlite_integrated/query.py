import sqlite3
import sqlite_integrated.utils as utils
from sqlite_integrated.utils import string_to_list
from sqlite_integrated.entry import DatabaseEntry
from sqlite_integrated.errors import QueryError, DatabaseError

# TODO implement JOIN and LEFTJOIN (RIGHTJOIN?): https://www.w3schools.com/sql/sql_join.asp
class Query:
    """
    A class for writing sql queries. Queries can be run on the attached database or a seperate one with the `run` method.

    Parameters
    ----------
    db : Database, optional
        The attached Database. This is the default database to run queries on.
    verbose : bool, optional
        Print what is going on in the `Query`
    """

    def __init__(self, db=None, verbose=False) -> None:
        
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

        self.verbose = verbose
        """Print what is going on in the `Query`"""

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
                self.sql += f"WHERE {col_name} = {utils.value_to_sql_value(value)}"
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
        self.sql += f"LIKE {utils.value_to_sql_value(pattern)} "
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
            raise QueryError(f"Data keys: {set(data)} are not a subset of table fields/columns. Table fields/columns: {set(self.fields)}")
        
        self.sql += f"SET {utils.dict_to_sql(data)} "

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
            raise QueryError(f"Data keys: {set(data)} are not a subset of table fields/columns. Unknown keys: {set(data) - set(self.fields)}. Table fields/columns: {set(self.fields)}")

        self.sql += f"({', '.join([str(v) for v in list(data)])}) VALUES ({', '.join([str(utils.value_to_sql_value(v)) for v in data.values()])}) "
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


    def run(self, db=None, raw = False, verbose=False) -> list[DatabaseEntry]:
        """
        Execute the query in the attached database or in a seperate one. Returns the results in a table (generator of DatabaseEntry) or `None` if no results.

        Parameters
        ----------
        db : Database, optional
            The database to execute to query on.
        raw : bool, optional
            If True: returns the raw table (list of tuples) instead of the normal table.
        verbose : bool, optional
            Be verbose about it.
        """

        if not db:
            db = self._db

        if not db:
            raise QueryError("Query does not have a database to execute on.")

        try:
            db.cursor.execute(self.sql)
        except sqlite3.OperationalError as e:
            raise DatabaseError(f"\n\n{e}\n\nError while running following sql: {self.sql}")

        if verbose or self.verbose or db.verbose:
            print(f"Executed sql: {self.sql}")

        results = db.cursor.fetchall()

        if raw:
            return(results)

        if self.fields == "*":
            self.fields = db.get_column_names(self.table)

        return(utils.raw_table_to_table(results, self.fields, self.table))
    
    def __repr__(self) -> str:
        return(f"> {self.sql.strip()} <")


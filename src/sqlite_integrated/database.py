import pandas as pd
import sqlite3
import os
from dataclasses import dataclass
import sqlite_integrated.utils as utils
from sqlite_integrated.query import Query, QueryError
from sqlite_integrated.entry import DatabaseEntry
from sqlite_integrated.errors import DatabaseError

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

@dataclass
class Column:
    """Class representing en sql column."""

    def __init__(self, name: str, type: str, not_null: bool = None, default_value: any = None, primary_key: bool = False, col_id: int = None, foreign_key: ForeignKey = None) -> None:

        if primary_key and type.upper() != "INTEGER":
            raise DatabaseError(f"Primary key columns must have sqlite type: `INTEGER` not \'{type}\'")

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

class Database:
    """
    Main database class for manipulating sqlite3 databases.

    Parameters
    ----------
    path : str
        Path to the database file.
    new : bool, optional
        A new blank database will be created where the `self.path` is pointing.
    verbose : bool, optional
        Enables feedback in the form of prints.
    """

    def __init__(self, path: str, new = False, verbose=False, silent=None):

        if not new and not os.path.isfile(path):
            raise(DatabaseError(f"No database file at \"{path}\". If you want to create one, pass \"new=True\""))

        self.path = path
        """Path to the database file."""

        self.conn = sqlite3.connect(path)
        """The sqlite3 connection."""

        self.cursor = self.conn.cursor()
        """The sqlite3 cursor. Use `cursor.execute(cmd)` to execute raw sql."""

        self.connected: bool = True
        """Is true if the `Database` instance is connected to a database."""

        self.verbose=verbose
        """Enables feedback in the form of prints."""

        self.conn.execute("PRAGMA foreign_keys = ON")

        # Deprecation notice
        if isinstance(silent, bool):
            print("[DEPRECATION] `silent` has been removed in favor of `verbose`. The `verbose` option is `False` by default.\n")

    @classmethod
    def in_memory(cls, verbose=False):
        """
        Create a database in memory. Returns the `Database` instance.

        Parameters
        ----------
        verbose : bool, optional
            Enables feedback in the form of prints.
        """
        return Database(":memory:", new=True, verbose=verbose)

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
        Returns all entries in a table as a table (generator of DatabaseEntry). This function loops over all entries in the table, so it is not the best in very big databases.

        Parameters
        ----------
        name : str
            Name of the table.
        get_only : list/None, optional
            Can be set to a list of column/field names, to only retrieve those columns/fields.
        """

        raw_table = self.get_table_raw(name, get_only)
            
        return(utils.raw_table_to_table(raw_table, self.get_column_names(name), name))


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

    def add_entry(self, entry, table = None, fill_null=False, verbose=False) -> None:
        """
        Add an entry to the database by passing a DatabaseEntry, or with a dictionary and specifying a table name. 

        Returns the id of the added DatabaseEntry in the table, or `None` if table does not contain a primary key.

        The entry must have values for all fields in the table. You can pass `fill_null=True` to fill any remaining fields with `None`/`null`.

        Parameters
        ----------
        entry : DatabaseEntry/dict
            The entry.
        table : str, optional
            Name of the table the entry belongs to. **Needed if adding an entry with a dictionary**.
        fill_null : bool, optional
            Fill in unpopulated fields with null values.
        verbose : bool, optional
            Enable prints.
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

        self.INSERT_INTO(entry.table).VALUES(entry).run()

        if verbose or self.verbose:
            print(f"added entry to table \"{entry.table}\": {entry}")

        if not self.get_table_id_field(table):
            return None

        self.cursor.execute("SELECT last_insert_rowid()")
        return (self.cursor.fetchall()[0][0])


    def update_entry(self, entry: dict, table=None, part=False, fill_null=False, verbose=False) -> None:
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
        verbose : bool, optional
            Enable prints.
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

        if verbose or self.verbose:
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
        self.connected = False

    def reconnect(self) -> None:
        """Reopen database after closing it"""

        self.conn = sqlite3.connect(self.path)
        self.cursor = self.conn.cursor()
        self.connected = True

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

    def run_raw_sql(self, sql: str, verbose=False):
        """
        Run SQL-string on the database. This returns a raw table as list of tuples.

        Parameters
        ----------
        sql : str
            SQL-string to be execured as an SQL command.
        verbose : bool, optional
            Prints the SQL-query if true
        """

        try:
            self.cursor.execute(sql)
        except sqlite3.OperationalError as e:
            raise QueryError(f"\n\n{e}\n\nError while running following sql: {self.sql}")

        if verbose or self.verbose:
            print(f"Executed sql: {self.sql}")

        return(self.cursor.fetchall())

    def SELECT(self, pattern="*") -> Query:
        """
        Start sql SELECT query from the database. Returns a Query to build from.

        Parameters
        ----------
        pattern : str, optional
            Either a python list or sql list of table names.
        """

        return(Query(db=self).SELECT(pattern))

    def UPDATE(self, table_name) -> Query:
        """
        Start sql UPDATE query from the database. Returns a Query to build from.

        Parameters
        ----------
        table_name : str
            Name of the table.
        """
        return(Query(db=self).UPDATE(table_name))

    def INSERT_INTO(self, table_name) -> Query:
        """
        Start sql INSERT INTO query from the database. Returns a Query to build from.

        Parameters
        ----------
        table_name : str
            Name of the table to insert into.
        """

        return(Query(db=self).INSERT_INTO(table_name))
    
    def DELETE_FROM(self, table_name: str) -> Query:
        """
        Start sql DELETE FROM query from the database. Returns a Query to build from.

        Parameters
        ----------
        table_name : str
            Name of the table to delete from.
        """
        return(Query(db=self).DELETE_FROM(table_name))

        
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

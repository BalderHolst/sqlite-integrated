import sqlite3
import os
from dataclasses import dataclass, astuple, asdict, fields
class DatabaseException(Exception):
    """Raised when the database fails to execute command"""

class DatabaseEntry(dict):
    """A python dictionary that keeps track of the table where it came from, and the name and value of its id field. This class is not supposed to be created manually"""
    def __init__(self, entry_dict: dict, table: str, id_field):
        """"
        Constructs the entry by saving the table and id_field as attributes. The ´entry_dict´ is used to populate this object with data.

            Parameters:
                id_field: The collum name for the entry's id
                table:      The name of the table the entry is a part of
                entry_dict: A dictionary containing all the information. This information can be accesed just like any other python dict with ´my_entry[my_key]´.
        """

        self.id_field = id_field
        self.table = table
        self.update(entry_dict)

    def __repr__(self) -> str:
        return f"DatabaseEntry(table: {self.table}, data: {super().__repr__()})"


class Database:
    """
    Main database class for manipulating sqlite3 databases

        Parameters:
            path:               Path to the database file

        Optional
            new:                A new blank database will be created where the ´self.path´ is pointing
            default_id_field:   The default name for the id field in tables
            silent:             Disables all feedback in the form of prints 
    """

    # TODO add global silent variable to silence all database prints

    def __init__(self, path: str, new = False, default_id_field="id", silent=False):
        if not new and not os.path.isfile(path):
            raise(DatabaseException(f"no database file at \"{path}\". If you want to create one, pass \"new=True\""))

        self.path = path
        """Path to the database file"""

        self.conn = sqlite3.connect(path)
        """The sqlite3 connection"""

        self.cursor = self.conn.cursor()
        """The sqlite3 cursor"""

        self.default_id_field = default_id_field #TODO
        """The default name for the id_field in returned DatabaseEntry"""

        self.silent=silent #TODO
        """Disables all feedback in the form of prints"""

        self.conn.execute("PRAGMA foregin_keys = ON")

    def get_table_names(self) -> list:
        """Returns the names of all tables in the database"""
        res = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        names = []
        for name in res:
            names.append(name[0])
        return(names)
    
    def is_table(self, table_name: str) -> bool:
        """Check if database has a table with a certain name"""
        if table_name in self.get_table_names():
            return True
        return False

    def get_table_raw(self, name: str, get_only = None) -> list:
        """Returns all entries in a table as tuples"""

        selected = "*"
        
        if get_only:
            if isinstance(get_only, list):
                selected = f"[{','.join(get_only)}]"
            else:
                raise ValueError(f"get_only can either be ´None´ or ´list´. Got: {get_only}")
        
        self.cursor.execute(f"SELECT {selected} FROM {name}")
        return(self.cursor.fetchall())

    def raw_entry_to_entry(self, raw_entry: tuple, table: str, id_field, fields=None) -> DatabaseEntry:
        """Convert a raw entry (tuple) to a DatabaseEntry"""

        if not fields:
            fields = self.get_table_collums(table)
        entry = {}
        for i, field in enumerate(fields):
            entry[field] = raw_entry[i]
        return(DatabaseEntry(entry, table, id_field))


    def get_table(self, name: str, get_only=None, id_field=None) -> list:
        """Returns all entries in a table as python dictionaries. This function loops over all entries in the table, so it is not the best in big databases"""

        if not id_field:
            id_field = self.default_id_field

        tuples = self.get_table_raw(name, get_only)

        fields = []
        if get_only:
            fields = get_only
        else:
            fields = self.get_table_collums(name)

        dict_table = []
        for raw_entry in tuples:
            dict_table.append(self.raw_entry_to_entry(raw_entry, name, id_field, fields=fields))
        return(dict_table)


    def get_table_info(self, name: str):
        """Returns sql information about a table (runs PRAGMA TABLE_INFO(name))"""
        self.cursor.execute(f"PRAGMA table_info({name});")
        return(self.cursor.fetchall())

    def table_overview(self, name: str, max_len:int = 40, get_only = None):
        """Returns a pretty table (with a name). Intended to to be run in a python shell or print with ´print´"""
        
        text = "" # the output text

        raw_table = self.get_table_raw(name, get_only=get_only)

        if get_only:
            fields = get_only
        else:
            fields = self.get_table_collums(name)

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
        for n in longest_words[:-1]: # we dont create the an intersection after the last collum
            offset += n
            underline = underline[:offset +1] + "╬" + underline[offset:]
            offset += len(seperator)

        text += underline + "\n"

        if len(raw_table) >= max_len:
            for row in raw_table[:max_len-5]:
                text += formatRow(row, longest_words) + "\n"
            text += "    .\n    .\n    .\n"
            for row in raw_table[-5:]:
                text += formatRow(row, longest_words)
        else:
            for row in raw_table:
                text += formatRow(row, longest_words)
        return(text)

    def overview(self):
        """Returns an overview of all the tables in the database with their fields. Intended to to be run in a python shell or print with ´print´"""

        text = "Tables\n"
        for table_name in self.get_table_names():
            text += "\t" + table_name + "\n"
            for col_name in self.get_table_collums(table_name):
                text += "\t\t" + col_name + "\n"
        return(text)


    def get_table_collums(self, name: str):
        """Returns the collum names for a given table"""
        keys = []

        for info in self.get_table_info(name):
            keys.append(list(info)[1])
        return(keys)

    def add_table_entry(self, table, entry: dict, fill_null=False, silent=False):
        """Add an entry to the database. The entry must have values for all fields in the table. You can pass ´fill_null=True´ to fill remaining fields with None/null. Use ´silent=True´ to suppress warnings and messages."""

        if 'id' in entry:
            raise DatabaseException(f"Cannot add entry with a preexisting id ({entry['id']})")

        if not self.is_table(table):
            raise DatabaseException(f"Database has no table with the name \"{table}\". Possible tablenames are: {self.get_table_names()}")
        
        table_fields = self.get_table_collums(table)[1:] # no id field

        for entry_field in entry: # removes all entry fields from table_fields list
            if entry_field in table_fields:
                table_fields.remove(entry_field)
            else:
                raise DatabaseException(f"The table \"{table}\" has no field by the name of \"{entry_field}\"")

        if len(table_fields) > 0: # if there are unpopulated fields
            if not fill_null:
                raise DatabaseException(f"Missing fields to insert into \"{table}\" table: {table_fields}")
            for field in table_fields:
                entry[field] = None

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
        sql = f"INSERT INTO {table}{keys} VALUES({question_marks(len(keys))})"

        self.cursor.execute(sql, values)

        if not silent:
            print(f"added entry to table \"{table}\": {entry}")

    # TODO implement fill_null
    def update_table_entry(self, entry: DatabaseEntry, id_field:str = None, fill_null=False, silent=False):
        """Update entry in database with a DatabaseEntry"""

        if id_field:
            entry.id_field = id_field

        if not entry.id_field in entry:
            raise DatabaseException(f"Cannot update entry as entry has no id in id_field: \"{entry.id_field}\"")

        if not self.is_table(entry.table):
            raise DatabaseException(f"Database has no table with the name \"{entry.table}\". Possible tablenames are: {self.get_table_names()}")
        
        # TODO make sure order does not matter
        table_fields = self.get_table_collums(entry.table)
        if table_fields != list(entry):
            raise DatabaseException(f"Table fields do not match entry fields: {table_fields} != {list(entry)}")

        data = []

        for field in entry:
            if field != entry.id_field:
                value = entry[field]
                if isinstance(value, str):
                    value = f"\"{value}\""
                data.append(f"{field} = {value}")

        sql = f"UPDATE {entry.table} SET {', '.join(data)} WHERE {entry.id_field} = {entry[entry.id_field]}"

        self.cursor.execute(sql)

        if not silent and not self.silent:
            print(f"updated entry in table \"{entry.table}\": {entry}")


    def get_entry_by_id(self, table, ID, id_field=None):
        """Get table entry by id"""

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

        return(self.raw_entry_to_entry(answer[0], table, id_field=id_field))
        
    def save(self):
        """Writes any changes to the database file"""
        self.conn.commit()
    
    def close(self):
        """saves and closes the database. If you want to explicitly close without saving use: ´self.conn.close()´"""
        self.conn.commit()
        self.conn.close()
        

if __name__ == "__main__": # for debugging
    db = Database("testing/test.db", default_id_field="ArtistId")

import sqlite3
import os

class DatabaseException(Exception):
    """Raised when the database fails to execute command"""


class Database:
    """Main database class for manipulating sqlite3 databases"""

    # TODO add global silent variable to silence all database prints

    def __init__(self, path: str, new = False):
        if not new and not os.path.isfile(path):
            raise(DatabaseException(f"no database file at \"{path}\". If you want to create one, pass \"new=True\""))

        self.path = path
        """Path to the database file"""

        self.conn = sqlite3.connect(path)
        """The sqlite3 connection"""

        self.cursor = self.conn.cursor()
        """The sqlite3 cursor"""

        self.conn.execute("PRAGMA foregin_keys = ON")

    def get_table_names(self):
        """Returns the names of all tables in the database"""
        res = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        names = []
        for name in res:
            names.append(name[0])
        return(names)
    
    def is_table(self, table_name: str):
        """Check if database has a table with a certain name"""
        if table_name in self.get_table_names():
            return True
        return False

    def get_table_raw(self, name: str, get_only = None):
        """Returns all entries in a table as tuples"""

        selected = "*"
        
        if get_only:
            if isinstance(get_only, list):
                selected = f"[{','.join(get_only)}]"
            else:
                raise ValueError(f"get_only can either be ´None´ or ´list´. Got: {get_only}")
        
        self.cursor.execute(f"SELECT {selected} FROM {name}")
        return(self.cursor.fetchall())

    def get_table(self, name: str, get_only=None):
        """Returns all entries in a table as python dictionaries"""
        tuples = self.get_table_raw(name, get_only)

        if get_only:
            fields = get_only
        else:
            fields = self.get_table_collums(name)

        dict_table = []

        for t in tuples:
            entry = {}
            for i, field in enumerate(fields):
                entry[field] = t[i]
            dict_table.append(entry)

        return(dict_table)


    def get_table_info(self, name: str):
        """Returns sql information about a table (runs PRAGMA TABLE_INFO(name))"""
        self.cursor.execute(f"PRAGMA table_info({name});")
        return(self.cursor.fetchall())

    def print_table(self, name: str, max_len:int = 40, get_only = None): # TODO test with more cols
        """Print a pretty table (with a name) to the terminal"""
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
        
        print(formatRow(fields, longest_words))
        underline = "═" * (sum(longest_words) + len(seperator))

        # This block is for placing the intersections
        offset = 0
        for n in longest_words[:-1]: # we dont create the an intersection after the last collum
            offset += n
            underline = underline[:offset +1] + "╬" + underline[offset:]
            offset += len(seperator)

        print(underline)

        if len(raw_table) >= max_len:
            for row in raw_table[:max_len-5]:
                print(formatRow(row, longest_words))
            print("    .\n    .\n    .")
            for row in raw_table[-5:]:
                print(formatRow(row, longest_words))
        else:
            for row in raw_table:
                print(formatRow(row, longest_words))

    def print_overview(self):
        """Prints an overview of all the tables in the database with their fields."""

        print("Tables")
        for table_name in self.get_table_names():
            print("\t" + table_name)
            for col_name in self.get_table_collums(table_name):
                print("\t\t" + col_name)

        



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

    # TODO add ability to use other field than id
    # TODO implement fill_null
    def update_table_entry(self, table: str, entry: dict, id_field:str = "id", fill_null=False, silent=False):
        if not id_field in entry:
            raise DatabaseException(f"Cannot update entry as entry has no id.")

        if not self.is_table(table):
            raise DatabaseException(f"Database has no table with the name \"{table}\". Possible tablenames are: {self.get_table_names()}")
        
        # TODO make sure order does not matter
        table_fields = self.get_table_collums(table)
        if table_fields != list(entry):
            raise DatabaseException(f"Table fields do not match entry fields: {table_fields} != {list(entry)}")

        data = []

        for field in entry:
            if field != id_field:
                value = entry[field]
                if isinstance(value, str):
                    value = f"\"{value}\""
                data.append(f"{field} = {value}")

        sql = f"UPDATE {table} SET {', '.join(data)} WHERE {id_field} = {entry[id_field]}"

        print(sql)

        self.cursor.execute(sql)

        if not silent:
            print(f"added entry to table \"{table}\": {entry}")

    def save(self):
        """Writes any changes to the database file"""
        self.conn.commit()
    
    def close(self):
        """saves and closes the database. If you want to explicitly close without saving use: ´self.conn.close()´"""
        self.conn.commit()
        self.conn.close()

if __name__ == "__main__":
    Database("not/path")


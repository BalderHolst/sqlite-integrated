import sqlite3
import os


class Database:
    """Main database class for manipulating sqlite3 databases"""

    def __init__(self, path, new = False):
        if not new and not os.path.isfile(path):
            raise(Exception(f"no database file at \"{path}\". If you want to create one, pass \"new=True\""))

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
    
    def is_table(self, table_name):
        """Check if database has a table with a certain name"""
        if table_name in self.get_table_names():
            return True
        return False

    def get_table_raw(self, name):
        """Returns all entries in a table as tuples"""
        self.cursor.execute(f"SELECT * FROM {name}")
        return(self.cursor.fetchall())

    def get_table(self, name):
        """Returns all entries in a table as python dictionaries"""
        tuples = self.get_table_raw(name)
        fields = self.get_table_collums(name)

        dict_table = []

        for t in tuples:
            entry = {}
            for i, field in enumerate(fields):
                entry[field] = t[i]
            dict_table.append(entry)

        return(dict_table)


    def get_table_info(self, name):
        """Returns sql information about a table (runs PRAGMA TABLE_INFO(name))"""
        self.cursor.execute(f"PRAGMA table_info({name});")
        return(self.cursor.fetchall())

    def save(self):
        """Writes any changes to the database file"""
        self.conn.commit()
    
    def close(self):
        """saves and closes the database. If you want to explicitly close without saving use: ´self.conn.close()´"""
        self.conn.commit()
        self.conn.close()

    def get_table_collums(self, name):
        """Returns the collum names for a given table"""
        keys = []

        for info in self.get_table_info(name):
            keys.append(list(info)[1])
        return(keys)

    def add_table_entry(self, table, entry: dict, fill_null=False, silent=False):
        """Add an entry to the database. The entry must have values for all fields in the table. You can pass ´fill_null=True´ to fill remaining fields with None/null. Use ´silent=True´ to suppress warnings and messages."""

        if 'id' in entry:
            raise Exception(f"Cannot add entry with a preexisting id ({entry['id']})")

        if not self.is_table(table):
            raise Exception(f"Database has no table with the name \"{table}\". Possible tablenames are: {self.get_table_names()}")
        
        table_fields = self.get_table_collums(table)[1:] # no id field

        for entry_field in entry: # removes all entry fields from table_fields list
            if entry_field in table_fields:
                table_fields.remove(entry_field)
            else:
                raise Exception(f"The table \"{table}\" has no field by the name of \"{entry_field}\"")

        if len(table_fields) > 0: # if there are unpopulated fields
            if not fill_null:
                raise Exception(f"Missing fields to insert into \"{table}\" table: {table_fields}")
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
    def update_table_entry(self, table, entry, fill_null=False, silent=False): # TODO finnish this next!
        if not 'id' in entry:
            raise Exception(f"Cannot update entry as entry has no id.")

        if not self.is_table(table):
            raise Exception(f"Database has no table with the name \"{table}\". Possible tablenames are: {self.get_table_names()}")

        table_fields = db.get_table_collums(table)[1:] # no id field

        for entry_field in entry: # removes all entry fields from table_fields list
            if entry_field in table_fields:
                table_fields.remove(entry_field)
            else:
                raise Exception(f"The table \"{table}\" has no field by the name of \"{entry_field}\"")

        if len(table_fields) > 0: # if there are unpopulated fields
            if not fill_null:
                raise Exception(f"Missing fields to insert into \"{table}\" table: {table_fields}")
            for field in table_fields:
                entry[field] = None


import sqlite3
import os


class Database:
    def __init__(self, path, new = False):
        if not new and not os.path.isfile(path):
            raise(Exception(f"no database file at \"{path}\". If you want to create one, pass \"new=True\""))

        self.path = path
        self.conn = sqlite3.connect(path)
        self.cursor = self.conn.cursor()

        self.conn.execute("PRAGMA foregin_keys = ON")

    def get_table_names(self):
        res = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        names = []
        for name in res:
            names.append(name[0])
        return(names)
    
    def is_table(self, table_name):
        if table_name in self.get_table_names():
            return True
        return False

    def get_table(self, name):
        self.cursor.execute(f"SELECT * FROM {name}")
        return(self.cursor.fetchall())

    def get_table_info(self, name):
        self.cursor.execute(f"PRAGMA table_info({name});")
        return(self.cursor.fetchall())

    def save(self):
        self.conn.commit()
    
    def close(self):
        self.conn.commit()
        self.conn.close()

    def get_table_collums(self, name):
        keys = []

        for info in self.get_table_info(name):
            keys.append(list(info)[1])
        return(keys)


    def entry_to_dict(self, entry, table_name):
        keys = self.get_table_collums(table_name)
        res = {}
        
        for n, field in enumerate(list(entry)):
            res[keys[n]] = field

        return(res)


    def add_table_entry(self, table, entry, fill_null=False, silent=False):

        if 'id' in entry:
            raise Exception(f"Cannot add entry with a preexisting id ({entry['id']})")

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




            



if __name__ == "__main__":
    db = Database('database/test.db')

    db.add_person({"name": "testperson", "birth": "69420"})
    db.update_table_entry("people", {"id": 1, "name": "updated!"}, fill_null=True)

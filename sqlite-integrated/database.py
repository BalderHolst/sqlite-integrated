import sqlite3
import os


class Database:
    def __init__(self, path, new = False):
        if not new and not os.path.isfile(path):
            raise(Exception(f"no database file at \"{path}\""))

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
        from generate_json import export_to_json
        self.conn.commit()
        export_to_json(self)
    
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



    ## ==========  People ==========

    def get_people(self):

        keys = self.get_table_collums("people")

        data = self.get_table("people")
        res = []
        for person in data:
            attrs = list(person)
            person_dir = {}
            for a, attr in enumerate(attrs):
                person_dir[keys[a]] = attr
            res.append(person_dir)
        return(res)

    def get_person(self, ID):
        self.cursor.execute("SELECT * FROM people WHERE id = ?", (ID,))
        answers = self.cursor.fetchall()
        if answers == []:
            return(None)
        return(self.entry_to_dict(answers[0], "people"))

    def is_person(self, person):
        if self.get_person(person['id']):
            return True
        return False

    def add_person(self, person, fill_null=False, silent=False):
        self.add_table_entry("people", person, silent=True, fill_null=fill_null)
        if not silent:
            print(f"added person: {person}")


    def update_person(self, person):
        fields = self.get_table_collums("people")

        set_statement = ""

        # Check
        for key in person:
            if key not in fields:
                print(f"\nWARNING: no collum with the name of \"{key}\" in table. Valid keys are: {fields}\n")
        for field in fields:
            if field not in person:
                raise Exception(f"Cannot update person. Person has no \"{field}\" attribute")

        # Build query
        for field in fields[1:]: # Skip id field
            set_statement += f"{field} = ?, "
        set_statement = set_statement[:-2]

        query = f"UPDATE people\nSET {set_statement}\nWHERE id = ?"
        # print(query)

        cmd = "self.cursor.execute(query, ("
        for field in fields[1:]: # skip id
            cmd += f"person['{field}'], "
        cmd += "person['id']))"
        # print(cmd)

        eval(cmd)

    def update_or_add_person(self, person):
        if self.is_person(person):
            self.update_person(person)
        else:
            self.add_person(person)

    # =============== KIDS ================

    def as_parrent(self, person):
        query = """SELECT p.id, p2.id, k.id 
            FROM people p 
	        left join parrent_kid pk on p.id = pk.parrent_id
	        left join people k on pk.kid_id = k.id
	        left join parrent_kid pk2 on k.id = pk2.kid_id
	        left join people p2 on pk2.parrent_id = p2.id
            """
        query += f"\nWHERE p.id = {person['id']} AND p.id <> p2.id"

        self.cursor.execute(query)
        answers = self.cursor.fetchall()

        sets = []
        for answer in answers:
            s = {"parrents": []}
            (parrent1, parrent2, kid) = answer
            s['parrents'].append(self.get_person(parrent1))
            s['parrents'].append(self.get_person(parrent2))
            s['kid'] = self.get_person(kid)
            sets.append(s)

        return(sets)

    def get_parrents(self, person):
        self.cursor.execute(f"SELECT pp.* FROM people p left join parrent_kid pk on p.id = pk.kid_id left join people pp on pk.parrent_id = pp.id WHERE p.id = {person['id']}")
        answers = self.cursor.fetchall()

        if answers[0][0] == None:
            return(None)

        if len(answers) != 2:
            raise Exception(f"Person with id {person['id']} has {len(answers)} parrent(s)")

        parrents = (self.entry_to_dict(answers[0], "people"), self.entry_to_dict(answers[1], "people"))
        return(parrents)


    # ================= GIFT ==================

    def update_marriage(self, marriage):
        query = f"UPDATE marriages SET date = ?, skilt = ? WHERE id = ?"

        self.cursor.execute(query, (marriage['date'], marriage['skilt'], marriage['id']))

        for person in marriage['people']:
            db.update_person(person)

    def get_marriages(self):
        self.cursor.execute(f"SELECT pm.marriage_id, m.date, m.skilt, min(pm.person_id), max(pm.person_id) FROM marriages m LEFT JOIN person_marriage pm ON m.id = pm.marriage_id group by m.id, pm.marriage_id")

        marriages = self.cursor.fetchall()

        res = []

        for m in marriages:
            marriage = {}
            (marriage['id'], marriage['date'], marriage['skilt'], p1, p2) = m
            marriage['people'] = (self.get_person(p1), self.get_person(p2))
            res.append(marriage)
        return(res)

    def get_person_marriages(self, person):
        self.cursor.execute(f"SELECT pm.marriage_id,pm.person_id,pm2.person_id,m.date,m.skilt FROM people p left join person_marriage pm on p.id = pm.person_id left join person_marriage pm2 on pm.marriage_id = pm2.marriage_id left join marriages m on pm.marriage_id = m.id WHERE p.id = {person['id']} and pm.person_id <> pm2.person_id")

        answers = self.cursor.fetchall()

        if len(answers) == 0:
            return(None)
        
        marriages = []

        for a in answers:
            m = {}
            m['id'], p1, p2, m['date'], m['skilt'] = a
            m['people'] = (person, self.get_person(p2))
            # m['people'] = (self.get_person(p1), self.get_person(p2))
            marriages.append(m)

        return(marriages)

    def get_marriage_by_people(self, p1, p2):
        for m in self.get_marriages(p1):
            if m['people'][1] == p2:
                return(m)
        return(None)
    
    def married_to(self, person):
        marriages = self.get_person_marriages(person)
        
        if marriages == None:
            return(None)

        people = []

        for m in marriages:
            people.append({"person": m['people'][1], "date": m['date'], "skilt": m['skilt']})
        
        if len(people) == 0:
            return(None)

        return(people)

            



if __name__ == "__main__":
    db = Database('database/test.db')

    db.add_person({"name": "testperson", "birth": "69420"})
    db.update_table_entry("people", {"id": 1, "name": "updated!"}, fill_null=True)

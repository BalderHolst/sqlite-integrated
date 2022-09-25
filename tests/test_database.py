import pytest
import shutil
import os

from sqlite_integrated import *


@pytest.fixture
def db() -> Database:
    shutil.copy("tests/test.db", "tests/temp.db")
    yield Database("tests/temp.db", silent=True)
    os.remove("tests/temp.db")


# ================== TESTS ===================

def test_creating_database():
    with pytest.raises(DatabaseError):
        Database("does_not_exist.db")

def test_creating_database_and_table():
    path = "tests/test_creating_database_and_table.db"
    db = Database(path, new=True)

    db.cursor.execute("""CREATE TABLE people (
    id integer PRIMARY KEY,
    first_name text,
    last_name text
    )""")

    db.add_entry({"first_name": "John", "last_name": "Smith"}, "people")
    db.add_entry({"first_name": "Tom", "last_name": "Builder"}, "people")
    db.add_entry({"first_name": "Eva", "last_name": "Larson"}, "people")

    os.remove(path)


def test_get_table_names(db):
    assert len(db.get_table_names()) == 13

def test_is_table(db):
    assert db.is_table(db.get_table_names()[0])

def test_get_table_raw(db):
    table_name = db.get_table_names()[1]
    table = db.get_table_raw(table_name)

    assert isinstance(table, list)
    assert isinstance(table[0], tuple)

def test_get_table_raw_and_get_table_columns(db):
    db: Database
    for table_name in db.get_table_names():
        table = db.get_table_raw(table_name)
        assert len(table[0]) == len(db.get_table_cols(table_name))

def test_get_table(db):
    table_name = "customers"
    raw_table = db.get_table_raw(table_name)
    table = db.get_table(table_name)

    assert len(raw_table) == len(table)
    assert isinstance(table, list)
    assert isinstance(table[0], DatabaseEntry)
    assert table[0].table == table_name

def test_null_fill(db):
    table_name = "customers"
    entry = DatabaseEntry({"FirstName": "TestName"}, table_name)
    filled_entry = db.fill_null(entry)

    assert len(filled_entry) == len(db.get_table(table_name)[0])

def test_get_entry_by_id(db):
    table_name = "customers"
    entry_by_id = db.get_entry_by_id(table_name, 1)
    entry_by_table = DatabaseEntry(db.get_table(table_name)[0], table_name)

    assert len(entry_by_id) == len(entry_by_table)
    assert entry_by_id == entry_by_table

def test_add_entry(db):
    table_name = "customers"
    entry = DatabaseEntry({"FirstName": "TestFirstName", "LastName": "TestLastName", "Email": "TestEmail"}, table_name)

    before_table = db.get_table(table_name)
    db.add_entry(entry, fill_null=True)
    after_table = db.get_table(table_name)

    assert len(after_table) == len(before_table) + 1
    assert entry['FirstName'] == after_table[-1]['FirstName']

    db.add_entry(DatabaseEntry({"FirstName": "SecondTestName", "LastName": "Laaaaaaast", "Email": "Random@email.com"}, table_name), fill_null=True)
    after_after_table = db.get_table(table_name)

    assert len(after_after_table) == len(before_table) + 2


def test_update_entry(db):
    entry = db.get_entry_by_id("customers", 1)
    entry['FirstName'] = "TestName"
    db.update_entry(entry)

    entry_from_table = db.get_table("customers")[0]

    assert entry_from_table['FirstName'] == "TestName"
    assert entry == entry_from_table

    # Need either part=True or fill_null=True
    with pytest.raises(DatabaseError):
        db.update_entry({}, "customers")

    with pytest.raises(DatabaseError):
        db.update_entry(DatabaseEntry({}, "customers"))

    # Part = True
    db.update_entry(DatabaseEntry({"CustomerId": 1, "FirstName": "TestFirstName", "LastName": "TestLastName", "Email": "TestEmail"}, "customers"), part=True)
    db.update_entry({"CustomerId": 2, "FirstName": "TestSecondFirstName", "LastName": "TestLastName", "Email": "TestEmail"}, "customers", part=True)

    assert db.get_table("customers")[0]['FirstName'] == "TestFirstName"
    assert db.get_table("customers")[1]['FirstName'] == "TestSecondFirstName"

    # fill_null = True
    db.update_entry(DatabaseEntry({"CustomerId": 3, "FirstName": "test1", "LastName": "TestLastName", "Email": "TestEmail"}, "customers"), fill_null=True)
    db.update_entry({"CustomerId": 4, "FirstName": "test2", "LastName": "TestLastName", "Email": "TestEmail"}, "customers", fill_null=True)

    assert db.get_table("customers")[2]['FirstName'] == "test1"
    assert db.get_table("customers")[3]['FirstName'] == "test2"

    # fill_null and part is NOT the same
    data = {"CustomerId": 5, "FirstName": "firstname", "LastName": "lastname", "Email": "email"}

    db.update_entry(data, "customers", part=True)
    part_entry = db.get_entry_by_id("customers", 5)

    db.update_entry(data, "customers", fill_null=True)
    fill_null_entry = db.get_entry_by_id("customers", 5)

    print(f"\n\n{fill_null_entry}\n\n{part_entry}\n\n")

    assert fill_null_entry != part_entry




def test_save(db):
    path = "tests/test_save.db"
    shutil.copy(db.path,path)

    db1 = Database(path)
    db2 = Database(db.path)

    assert db1 == db2

    entry = db1.get_entry_by_id("customers", 1)
    entry['FirstName'] = "Different Name"
    db1.update_entry(entry)

    assert db1 != db2

    db1.close()

    db3 = Database(path)

    assert db3 != db2

    with pytest.raises(sqlite3.ProgrammingError):
        assert db1 != db2
    
    db1.reconnect()
    assert db1 == db3

    os.remove(path)

def test_select(db):
    table_name = "customers"

    q = db.SELECT().FROM(table_name)

    table = db.get_table(table_name)
    
    assert q.run() == table
    assert q.run(raw = True) == db.get_table_raw(table_name)

    assert table[0] == db.SELECT().FROM(table_name).WHERE("CustomerId", 1).run()[0]
    assert table[0] == db.SELECT().FROM(table_name).WHERE("CustomerId = 1").run()[0]
    
    assert len(db.SELECT(["FirstName", "LastName"]).FROM("customers").run()[0]) == 2
    assert len(db.SELECT(["FirstName", "LastName"]).FROM("customers").WHERE("CustomerId", 1).run()[0]) == 2

def test_update(db):
    db1 = Database(db.path)
    db2 = Database(db.path)

    assert db1 == db2

    db1.UPDATE("customers").SET({"FirstName": "TestName"}).WHERE("CustomerId", 1).run()

    assert db1 != db2

    db1.close()

    db2.update_entry(db2.get_entry_by_id("customers", 1))

    db1.reconnect()

    assert db1 == db2

def test_insert_into(db):
    db1 = Database(db.path)
    db2 = Database(db.path)

    assert db1 == db2

    data = {"FirstName": "TestFirst", "LastName": "TestLast", "Email": "test@mail.com"}

    table_name = "customers"

    db1.INSERT_INTO(table_name).VALUES(data).run()

    assert len(db1.get_table(table_name)) == len(db2.get_table(table_name)) + 1

    inserted_entry = db1.get_table(table_name)[-1]

    assert inserted_entry['Email'] == data['Email']
    assert inserted_entry['LastName'] == data['LastName']
    assert inserted_entry['FirstName'] == data['FirstName']

def test_run(db):
    query = Query().SELECT().FROM("customers")

    assert query.run(db) == db.SELECT().FROM("customers").run()

    assert len(Query().SELECT(["FirstName", "LastName"]).FROM("customers").run(db)[0]) == 2
    assert Query().SELECT(["FirstName", "LastName"]).FROM("customers").run(db)[0] == db.SELECT(["FirstName", "LastName"]).FROM("customers").run()[0]

def test_export_to_csv(db):
    out_dir = "tests/test_export_to_csv"
    os.mkdir(out_dir)

    db.export_to_csv(out_dir, ["customers", "artists"])

    assert len(os.listdir(out_dir)) == 2

    db.export_to_csv(out_dir)

    assert len(os.listdir(out_dir)) == len(db.get_table_names())
    
    db.export_to_csv(out_dir, sep = ",")

    assert len(os.listdir(out_dir)) == len(db.get_table_names())

    # cleanup
    shutil.rmtree(out_dir)

def test_get_table_info(db):
    db: Database

    cols = db.get_table_cols("artists")[1]
    assert isinstance(cols, Column)

def test_column():
    col = Column("colname", "text", not_null=True, default_value="defname", col_id=9)

    assert col.name == "colname"
    assert col.type == "text"
    assert col.not_null == True
    assert col.default_value == "defname"
    assert col.col_id == 9



def test_create_table_and_memory_database():
    db = Database(":memory:", new=True)

    db.create_table("table1", [
        Column("id", "integer", primary_key=True),
        Column("data1", "text"),
        Column("data2", "text")
        ])

    db.create_table("table2", [
        Column("id2", "integer", primary_key=True),
        Column("data1", "text", not_null=True, default_value="defval"),
        Column("data2", "text")
        ])

    assert len(db.get_table_names()) == 2
    assert db.get_table_cols("table2")[1].not_null == True

def test_add_rename_and_delete_column():
    db = Database(":memory:", new=True)

    db.create_table("table_name", [
        Column("id", "integer", primary_key=True),
        Column("data1", "text"),
        Column("data2", "text")
        ])

    cols_before = db.get_table_cols("table_name")

    db.add_column("table_name", Column("added_col", "text"))

    assert len(cols_before) + 1 == len(db.get_table_cols("table_name"))

    db.rename_column("table_name", "added_col", "new_name")

    assert db.get_column_names("table_name")[-1] == "new_name"

    db.delete_column("table_name", "new_name")

    assert len(db.get_table_cols("table_name")) == len(cols_before)

def test_DELETE_FROM():
    db = Database(":memory:", new=True)

    db.create_table("table_name", [
        Column("id", "integer", primary_key=True),
        Column("name", "text")
        ])

    length = 10


    for i in range(length):
        db.add_entry({"name": f"name{i}"}, "table_name")

    db.DELETE_FROM("table_name").WHERE("id", 3).run()

    assert len(db.get_table("table_name")) == length - 1
    
def test_is_column(db):
    db: Database = db
    assert db.is_column("customers", "FirstName") == True
    assert db.is_column("customers", "NotaCol") == False

def test_rename_and_delete_table(db):
    db = Database(":memory:", new=True)

    db.create_table("table1", [
        Column("id", "integer", primary_key=True),
        Column("data1", "text"),
        ])

    db.rename_table("table1", "gamers")

    assert db.is_table("gamers") == True
    assert db.is_table("table1") == False

    db.delete_table("gamers")

    assert db.is_table("gamers") == False

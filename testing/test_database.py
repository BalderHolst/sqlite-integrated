from sqlite_integrated import *
import unittest
import shutil
import os


class TestDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        shutil.copy("testing/test.db", "testing/temp.db")

    @classmethod
    def tearDownClass(cls) -> None:
        os.remove("testing/temp.db")

    def setUp(self) -> None:
        self.db = Database("testing/temp.db", silent=True)
    
    def tearDown(self) -> None:
        pass

    def test_creating(self):
        with self.assertRaises(DatabaseException):
            Database("does_not_exist.db")

    def test_DatabaseEntry(self):
        self.assertIsInstance(DatabaseEntry({"name": "this is the name", "data": "this is data"}, "the_table", "id"), dict)

    # def test_add_table_entry(self):
    #     artist = {"name"}

    def test_update_table(self):
        artist = self.db.get_entry_by_id("artists", 1, id_field="ArtistId")
        artist['Name'] = "Balder" # Changing the name
        self.db.update_table_entry(artist)
        self.db.close()
        self.db = Database(self.db.path)
        self.assertEqual(self.db.get_entry_by_id("artists", 1, id_field="ArtistId")['Name'], "Balder")



if __name__ == "__main__":
    unittest.main()


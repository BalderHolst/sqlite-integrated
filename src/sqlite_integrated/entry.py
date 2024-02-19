import sqlite_integrated.utils as utils
from sqlite_integrated.errors import DatabaseError

class DatabaseEntry(dict):
    """
    A python dictionary that keeps track of the table it belongs to. This class is not meant to be created manually.

    Parameters
    ----------
    entry_dict : dict
        A dictionary containing all the information. This information can be accesed just like any other python dict with `my_entry[my_key]`.
    table : str
        The name of the table the entry is a part of
    """

    def __init__(self, entry_dict: dict, table: str):
        self.table = table
        self.update(entry_dict)


    @classmethod
    def from_raw_entry(cls, raw_entry: tuple, table_fields: list, table_name: str):
        """
        Alternative constructor for converting a raw entry to a DatabaseEntry.
        
        Parameters
        ----------
        raw_entry : tuple
            A tuple with the data for the entry. Ex: `(2, "Tom", "Builder", 33)`
        table_fields : list
            A list of column names for the data. Ex: `["id", "FirstName", "LastName", "Age"]`
        table_name : str
            The name of the table (in the database) that the data belongs to. Ex: "people"
        """

        entry_dict = {}

        if isinstance(table_fields, str):
            table_fields = utils.string_to_list(table_fields)
        elif not isinstance(table_fields, list):
            raise ValueError(f"table_fields must be either `list` or `str`. Got: {table_fields}")

        if len(raw_entry) != len(table_fields):
            raise DatabaseError(f"There must be as many names for table fields as there are fields in the entry: len({raw_entry}) != len({table_fields}) => {len(raw_entry)} != {len(table_fields)}")
        
        for n, field in enumerate(table_fields):
            entry_dict[field] = raw_entry[n]
        entry = DatabaseEntry(entry_dict, table_name)
        return(entry)
        

    def __repr__(self) -> str:
        """Represent a Database entry"""

        return f"DatabaseEntry(table: {self.table}, data: {super().__repr__()})"


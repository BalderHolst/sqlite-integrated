from sqlite_integrated.entry import DatabaseEntry

def string_to_list(string: str) -> list:
    """Takes a string with comma seperated values, returns a list of the values. (spaces are ignored)"""

    return(string.replace(" ", "").split(","))

def value_to_sql_value(value) -> str:
    """Converts python values to sql values. Basically just puts quotes around strings and not ints or floats. Also converts None to null"""

    if isinstance(value, str):
        return("'" + value.replace("'", "''") + "'")
    elif isinstance(value, int):
        return(str(value))
    elif isinstance(value, float):
        return(str(value))
    elif value == None:
        return("null")
    elif isinstance(value, list):
        try:
            return(",".join(value))
        except TypeError:
            raise TypeError("Cannot convert list on non-string objects to sql")
    else:
        raise TypeError(f"Cannot convert value of type {type(value)} to sql")

def dict_to_sql(data: dict) -> str:
    """Converts a dict into sql key value pairs. Ex: \"key1 = value1, key2 = value2...\""""
    
    set_list = []
    for field in data:
        set_list.append(f"{field} = {value_to_sql_value(data[field])}")
    return(", ".join(set_list))

def raw_table_to_table(raw_table: list, fields: list, table_name: str) -> list[DatabaseEntry]:
    """
    Convert a raw table (list of tuples) to a table (generator of DatabaseEntry).

    Parameters
    ----------
    raw_table : list
        A list of tuples with the data for the entries.
    fields : list
        A list of column names for the data. Ex: `["id", "FirstName", "LastName", "Age"]`
    table_name: str
        The name of the table (in the database) that the data belongs to. Ex: "people".
    """

    if len(raw_table) == 0:
        return
    if len(raw_table[0]) != len(fields):
        raise DatabaseError(f"There must be one raw column per field. {raw_table[0] = }, {fields = }")
    
    for raw_entry in raw_table:
        entry = {}
        for n, field in enumerate(fields):
            entry[field] = raw_entry[n]
        yield DatabaseEntry(entry, table_name)

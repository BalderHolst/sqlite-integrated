class DatabaseError(Exception):
    """Raised when the database fails to execute command"""

class QueryError(Exception):
    """Raised when trying to create an invalid or unsupperted query"""


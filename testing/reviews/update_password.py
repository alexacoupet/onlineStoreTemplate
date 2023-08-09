# update_password.py
import sys
import os
import pytest
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from database.db import Database

# Add the path to the 'database' module directory to the Python path
module_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "database"))
sys.path.insert(0, module_dir)

# Your test functions
def test_update_password():
    # Arrange
    db = Database("database/store_records.db")
    email = "test@example.com"
    new_password = "new_password"

    # Act
    result = db.update_password(email, new_password)

    # Assert
    assert result

if __name__ == "__main__":
    pytest.main()

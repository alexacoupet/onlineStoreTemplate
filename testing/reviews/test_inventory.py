import pytest
from database.db import Database
from db_tests import test_get_inventory_exists  # Import the testing function

# Arrange
db = Database("database/store_records.db")

# Act
result, error_report = test_get_inventory_exists(db)

# Assert
def test_retrieving_inventory():
    assert result, error_report

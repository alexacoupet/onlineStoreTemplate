# test_is_valid_email_in_database.py
import sys
import os
import pytest

# Append the parent directory of your project to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from database.db import Database

# test_is_valid_email_in_database.py
def test_is_valid_email_in_database():
    # Arrange
    db = Database("database/store_records.db")  # Provide the correct path
    existing_email = "dennis@unix.com"
    non_existing_email = "jeliseo@uncc.edu"

    # Act
    result_existing = db.is_valid_email_in_database(existing_email)
    result_non_existing = db.is_valid_email_in_database(non_existing_email)

    # Assert
    assert result_existing is True
    assert result_non_existing is False

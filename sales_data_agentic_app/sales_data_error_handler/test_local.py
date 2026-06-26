import unittest
from unittest.mock import MagicMock, patch
import os

# Set mock environment variables
os.environ["SOURCE_BUCKET"] = "mock-source-bucket"
os.environ["ERROR_BUCKET"] = "mock-error-bucket"
os.environ["GOOGLE_CLOUD_PROJECT"] = "mock-project"

import tools

class TestSalesDataErrorHandlerTools(unittest.TestCase):

    @patch("tools.storage.Client")
    def test_list_quarantined_files(self, mock_storage_client):
        # Setup mock GCS list
        mock_client = MagicMock()
        mock_storage_client.return_value = mock_client
        mock_bucket = MagicMock()
        mock_client.bucket.return_value = mock_bucket
        
        mock_blob1 = MagicMock()
        mock_blob1.name = "sales_ny_error.csv"
        mock_blob2 = MagicMock()
        mock_blob2.name = "sales_boston.csv"
        
        mock_bucket.list_blobs.return_value = [mock_blob1, mock_blob2]
        
        # Execute tool
        result = tools.list_quarantined_files()
        
        # Assertions
        self.assertEqual(result["status"], "success")
        self.assertIn("sales_ny_error.csv", result["files"])
        self.assertIn("sales_boston.csv", result["files"])
        mock_client.bucket.assert_called_with("mock-error-bucket")

    @patch("tools.storage.Client")
    def test_analyze_file_errors_invalid_date(self, mock_storage_client):
        # Setup mock GCS content
        mock_client = MagicMock()
        mock_storage_client.return_value = mock_client
        mock_bucket = MagicMock()
        mock_client.bucket.return_value = mock_bucket
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = True
        
        # CSV with an invalid date on row 2 (header is row 1)
        mock_blob.download_as_text.return_value = (
            "date,location,product_line,sales\n"
            "2026/06/18,New York,Electronics,500.0\n"
        )
        
        # Execute tool
        result = tools.analyze_file_errors("sales_ny_error.csv")
        
        # Assertions
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["row"], 2)
        self.assertIn("Invalid date format", result["errors"][0]["reason"])

    @patch("tools.storage.Client")
    def test_analyze_file_errors_negative_sales(self, mock_storage_client):
        # Setup mock GCS content
        mock_client = MagicMock()
        mock_storage_client.return_value = mock_client
        mock_bucket = MagicMock()
        mock_client.bucket.return_value = mock_bucket
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = True
        
        # CSV with a negative sales amount on row 2
        mock_blob.download_as_text.return_value = (
            "date,location,product_line,sales\n"
            "2026-06-18,New York,Electronics,-100.0\n"
        )
        
        # Execute tool
        result = tools.analyze_file_errors("sales_ny_error.csv")
        
        # Assertions
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["row"], 2)
        self.assertIn("cannot be negative", result["errors"][0]["reason"])

    @patch("tools.storage.Client")
    def test_submit_corrections_success(self, mock_storage_client):
        # Setup mock GCS client
        mock_client = MagicMock()
        mock_storage_client.return_value = mock_client
        
        mock_source_bucket = MagicMock()
        mock_error_bucket = MagicMock()
        
        # Side effect to return source or error bucket based on arg
        def bucket_side_effect(bucket_name):
            if bucket_name == "mock-source-bucket":
                return mock_source_bucket
            return mock_error_bucket
            
        mock_client.bucket.side_effect = bucket_side_effect
        
        mock_dest_blob = MagicMock()
        mock_source_bucket.blob.return_value = mock_dest_blob
        
        mock_error_blob = MagicMock()
        mock_error_bucket.blob.return_value = mock_error_blob
        mock_error_blob.exists.return_value = True
        
        # Valid corrected content
        corrected_content = (
            "date,location,product_line,sales\n"
            "2026-06-18,New York,Electronics,500.0\n"
        )
        
        # Execute tool
        result = tools.submit_corrections("sales_ny_error.csv", corrected_content)
        
        # Assertions
        self.assertEqual(result["status"], "success")
        mock_dest_blob.upload_from_string.assert_called_with(corrected_content, content_type="text/csv")
        mock_error_blob.delete.assert_called_once()

    @patch("tools.storage.Client")
    def test_submit_corrections_invalid(self, mock_storage_client):
        # Invalid corrected content (negative sales)
        corrected_content = (
            "date,location,product_line,sales\n"
            "2026-06-18,New York,Electronics,-500.0\n"
        )
        
        # Execute tool
        result = tools.submit_corrections("sales_ny_error.csv", corrected_content)
        
        # Assertions
        self.assertEqual(result["status"], "error")
        self.assertIn("Validation failed", result["message"])

if __name__ == "__main__":
    unittest.main()

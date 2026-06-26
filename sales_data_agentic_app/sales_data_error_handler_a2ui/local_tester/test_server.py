import requests
import json
import os
import unittest
from google.cloud import storage

class TestA2UILocalTesterServer(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.project_id = "agentspace-demo-1145-b"
        cls.error_bucket_name = "agentspace-demo-1145-b-sales-data-errors"
        cls.source_bucket_name = "agentspace-demo-1145-b-sales-data"
        cls.server_url = "http://localhost:8005/jsonrpc"
        cls.session_id = "test_integration_session_999"
        
        # Initialize GCS Client
        cls.storage_client = storage.Client(project=cls.project_id)
        cls.error_bucket = cls.storage_client.bucket(cls.error_bucket_name)
        cls.source_bucket = cls.storage_client.bucket(cls.source_bucket_name)
        
        # 1. Ensure any old test file is cleaned up from the source bucket
        source_blob = cls.source_bucket.blob("sales_chicago_error.csv")
        if source_blob.exists():
            source_blob.delete()
            print("Cleaned up existing sales_chicago_error.csv from source bucket.")
            
        # 2. Upload a fresh mock error file to the error bucket
        mock_content = (
            "date,location,product_line,sales\n"
            "2026/06/18,Chicago,Electronics,-500.0\n"
        )
        error_blob = cls.error_bucket.blob("sales_chicago_error.csv")
        error_blob.upload_from_string(mock_content, content_type="text/csv")
        print("Uploaded fresh mock_error file to GCS error bucket.")

    def test_e2e_a2ui_repair_flow(self):
        # ----------------------------------------------------
        # TURN 1: GREETING & DISCOVERY
        # ----------------------------------------------------
        payload = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "message": {
                    "text": "hi"
                },
                "session_id": self.session_id
            },
            "id": 1
        }
        
        response = requests.post(self.server_url, json=payload)
        self.assertEqual(response.status_code, 200)
        
        res_data = response.json()
        self.assertIn("result", res_data)
        parts = res_data["result"]["message"]["parts"]
        
        # Verify we got both text and A2UI data
        self.assertTrue(any("text" in p for p in parts))
        self.assertTrue(any(p.get("metadata", {}).get("mimeType") == "application/json+a2ui" for p in parts))
        
        # Extract A2UI messages
        ui_parts = [p["data"] for p in parts if p.get("metadata", {}).get("mimeType") == "application/json+a2ui"]
        
        # Verify Discovery UI structure
        has_begin = any("beginRendering" in msg and msg["beginRendering"]["root"] == "discovery_root" for msg in ui_parts)
        has_surface = any("surfaceUpdate" in msg and any(c["id"] == "discovery_root" for c in msg["surfaceUpdate"]["components"]) for msg in ui_parts)
        
        self.assertTrue(has_begin, "Missing beginRendering for discovery_root")
        self.assertTrue(has_surface, "Missing surfaceUpdate for discovery_root components")
        print("✔ Turn 1: Discovery Dashboard rendered successfully.")
        
        # ----------------------------------------------------
        # TURN 2: INSPECT FILE
        # ----------------------------------------------------
        payload = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "message": {
                    "text": "Inspect sales_chicago_error.csv",
                    "parts": [
                        {
                            "data": {
                                "userAction": {
                                    "name": "submit",
                                    "context": {
                                        "message": "Inspect sales_chicago_error.csv"
                                    }
                                }
                            },
                            "metadata": {
                                "mimeType": "application/json+a2ui"
                            }
                        }
                    ]
                },
                "session_id": self.session_id
            },
            "id": 2
        }
        
        response = requests.post(self.server_url, json=payload)
        self.assertEqual(response.status_code, 200)
        
        res_data = response.json()
        parts = res_data["result"]["message"]["parts"]
        ui_parts = [p["data"] for p in parts if p.get("metadata", {}).get("mimeType") == "application/json+a2ui"]
        
        # Verify Repair Form UI structure and pre-population
        has_begin_repair = any("beginRendering" in msg and msg["beginRendering"]["root"] == "repair_root" for msg in ui_parts)
        has_data_model = any("dataModelUpdate" in msg and any(item["key"] == "/row_2/date" and item["valueString"] == "2026/06/18" for item in msg["dataModelUpdate"]["contents"]) for msg in ui_parts)
        has_fields = any("surfaceUpdate" in msg and any(c["id"] == "tf_date_2" for c in msg["surfaceUpdate"]["components"]) for msg in ui_parts)
        
        self.assertTrue(has_begin_repair, "Missing beginRendering for repair_root")
        self.assertTrue(has_data_model, "Missing pre-population dataModelUpdate for Row 2 values")
        self.assertTrue(has_fields, "Missing TextField components in surfaceUpdate")
        print("✔ Turn 2: Pre-populated Interactive Repair Form rendered successfully.")

        # ----------------------------------------------------
        # TURN 3: SUBMIT FIXES
        # ----------------------------------------------------
        payload = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "message": {
                    "text": "Submit corrections for sales_chicago_error.csv",
                    "parts": [
                        {
                            "data": {
                                "userAction": {
                                    "name": "submit",
                                    "context": {
                                        "message": "Submit corrections for sales_chicago_error.csv",
                                        "file_name": "sales_chicago_error.csv",
                                        "row_2_date": "2026-06-18",
                                        "row_2_location": "Chicago",
                                        "row_2_product_line": "Electronics",
                                        "row_2_sales": "500.0"
                                    }
                                }
                            },
                            "metadata": {
                                "mimeType": "application/json+a2ui"
                            }
                        }
                    ]
                },
                "session_id": self.session_id
            },
            "id": 3
        }
        
        response = requests.post(self.server_url, json=payload)
        self.assertEqual(response.status_code, 200)
        
        res_data = response.json()
        parts = res_data["result"]["message"]["parts"]
        ui_parts = [p["data"] for p in parts if p.get("metadata", {}).get("mimeType") == "application/json+a2ui"]
        
        # Verify Success Card
        has_begin_success = any("beginRendering" in msg and msg["beginRendering"]["root"] == "success_root" for msg in ui_parts)
        has_success_card = any("surfaceUpdate" in msg and any(c["id"] == "success_header" for c in msg["surfaceUpdate"]["components"]) for msg in ui_parts)
        
        self.assertTrue(has_begin_success, "Missing beginRendering for success_root")
        self.assertTrue(has_success_card, "Missing success_header in surfaceUpdate components")
        print("✔ Turn 3: Correction validated and Success Card rendered successfully.")
        
        # 4. Verify physical GCS bucket state transitions
        self.assertFalse(self.error_bucket.blob("sales_chicago_error.csv").exists(), "Quarantined file should be deleted from error bucket.")
        self.assertTrue(self.source_bucket.blob("sales_chicago_error.csv").exists(), "Corrected file should exist in the primary source bucket.")
        print("✔ Physical GCS bucket transitions verified successfully.")

if __name__ == "__main__":
    unittest.main()

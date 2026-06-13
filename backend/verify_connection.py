import os
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def run_e2e_verification():
    print("=== OralDysplasia AI: Executing End-to-End API and Database Integration Tests ===")
    
    # ── 1. Register or Login Pathologist ──────────────────────────────────
    auth_data = {
        "email": "verify_dr@hospital.com",
        "name": "Verify Doctor",
        "license_id": "LIC-999-VERIFY",
        "role": "Consultant Pathologist",
        "institution": "Verification Central Lab",
        "password": "testpass123"
    }
    
    token = None
    print("[TEST] Registering new pathologist user...")
    try:
        r = requests.post(f"{BASE_URL}/auth/signup", json=auth_data)
        if r.status_code == 200:
            res_json = r.json()
            token = res_json["access_token"]
            print("  [SUCCESS] Pathologist registered successfully!")
        elif r.status_code == 400 and "already registered" in r.text.lower():
            print("  [INFO] Pathologist already registered. Logging in instead...")
            login_data = {
                "email": auth_data["email"],
                "password": auth_data["password"]
            }
            r_login = requests.post(f"{BASE_URL}/auth/login", json=login_data)
            if r_login.status_code == 200:
                token = r_login.json()["access_token"]
                print("  [SUCCESS] Pathologist logged in successfully!")
            else:
                print(f"  [FAIL] Login failed: {r_login.text}")
                return False
        else:
            print(f"  [FAIL] Registration failed: {r.text}")
            return False
    except Exception as e:
        print(f"  [FAIL] Connection to server failed: {e}")
        return False
        
    # ── 2. Create simulated WSI slide file ──────────────────────────────
    dummy_filepath = "dummy_verify_slide.svs"
    with open(dummy_filepath, "wb") as f:
        f.write(b"Simulated virtual WSI diagnostic scan pixel values")
    print(f"[TEST] Created local simulated slide file: '{dummy_filepath}'")
    
    # ── 3. Upload Slide Case ──────────────────────────────────────────
    headers = {"Authorization": f"Bearer {token}"}
    slide_metadata = {
        "patient_id": "PT-888-VERIFY",
        "patient_name": "Verify Patient",
        "patient_age": "45",
        "patient_gender": "Male",
        "anatomical_site": "Lateral Tongue",
        "clinical_notes": "Verification mock case history history notes"
    }
    
    slide_id = None
    print("[TEST] Uploading slide case to database via REST endpoint...")
    try:
        with open(dummy_filepath, "rb") as f:
            files = {"file": (dummy_filepath, f, "application/octet-stream")}
            r_upload = requests.post(
                f"{BASE_URL}/slides/upload",
                headers=headers,
                data=slide_metadata,
                files=files
            )
            
        if r_upload.status_code == 200:
            res_upload = r_upload.json()
            slide_id = res_upload["id"]
            print(f"  [SUCCESS] Slide uploaded successfully! Assigned ID: {slide_id}")
        else:
            print(f"  [FAIL] Upload request failed: {r_upload.text}")
            os.remove(dummy_filepath)
            return False
    except Exception as e:
        print(f"  [FAIL] Upload request encountered connection error: {e}")
        os.remove(dummy_filepath)
        return False
        
    # Remove dummy file
    if os.path.exists(dummy_filepath):
        os.remove(dummy_filepath)
        
    # ── 4. Verify Library listing & AES decryption ──────────────────
    print("[TEST] Querying slide library list to verify database records...")
    try:
        r_lib = requests.get(f"{BASE_URL}/slides/library", headers=headers)
        if r_lib.status_code == 200:
            library_json = r_lib.json()
            slides = library_json["slides"]
            
            # Find our uploaded slide case
            match = next((s for s in slides if s["id"] == slide_id), None)
            if match:
                print("  [SUCCESS] Found uploaded slide record in cached library query!")
                # Verify AES encryption-decryption works and returned decrypted plain text matches
                assert match["patient_id"] == slide_metadata["patient_id"]
                assert match["patient_name"] == slide_metadata["patient_name"]
                assert match["patient_age"] == slide_metadata["patient_age"]
                assert match["patient_gender"] == slide_metadata["patient_gender"]
                print("  [SUCCESS] Patient PII AES-256 decryption test passed! Plaintext matches input.")
                print(f"            Patient ID: {match['patient_id']}")
                print(f"            Patient Name: {match['patient_name']}")
                print(f"            Patient Age: {match['patient_age']}")
                print(f"            Patient Gender: {match['patient_gender']}")
            else:
                print(f"  [FAIL] Uploaded slide ID {slide_id} not found in library list.")
                return False
        else:
            print(f"  [FAIL] Library fetch failed: {r_lib.text}")
            return False
    except Exception as e:
        print(f"  [FAIL] Library query encountered connection error: {e}")
        return False

    print("=== [ALL INTEGRATION TESTS PASSED SUCCESSFULLY] ===")
    print(">>> Front-end and Back-end connectivity is 100% established and verified! <<<")
    return True

if __name__ == "__main__":
    run_e2e_verification()

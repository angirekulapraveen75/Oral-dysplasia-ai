"""
OralDysplasia AI — Appium Conftest / Driver Configuration.
Centralised Appium driver setup for the OralDysplasia Android test suite.

This module provides:
  - Appium desired capabilities / UiAutomator2Options configuration
  - Driver initialisation helper with graceful simulation fallback
  - Device connectivity validation utilities
  - Common element locator strategies tailored to OralDysplasia AI Android app
"""

import os
import subprocess

# ──────────────────────────────────────────────────────────────────────────────
# Appium Server & Device Configuration
# ──────────────────────────────────────────────────────────────────────────────

# Appium 2.x server URL (default port 4723)
APPIUM_SERVER_URL = os.environ.get("APPIUM_URL", "http://127.0.0.1:4723")

# Android backend URL visible from emulator (10.0.2.2 maps to host machine localhost)
BACKEND_URL = os.environ.get("BACKEND_URL", "http://10.0.2.2:8000")

# ─── Android Device / Emulator Capabilities ───────────────────────────────────
ANDROID_CAPS = {
    "platformName": "Android",
    # Adjust to match your emulator/device API level
    "platformVersion": os.environ.get("ANDROID_VERSION", "14"),
    # Get device name from: adb devices
    "deviceName": os.environ.get("DEVICE_NAME", "emulator-5554"),
    # OralDysplasia AI package and entry activity
    "appPackage": "com.oraldysplasia.ai",
    "appActivity": ".MainActivity",
    # Use UiAutomator2 (modern Appium 2.x driver)
    "automationName": "UiAutomator2",
    # noReset=True keeps the app installed and session data (login state persists)
    "noReset": True,
    # Full reset = True clears app data (use for fresh session tests)
    "fullReset": False,
    # Timeout for commands (seconds)
    "newCommandTimeout": 60,
    # Auto-grant runtime permissions (camera, storage)
    "autoGrantPermissions": True,
    # UiAutomator2 specific
    "uiautomator2ServerInstallTimeout": 60000,
    "adbExecTimeout": 60000,
    # Skip unlocking device screen
    "skipUnlock": True,
    # Capture screenshots on failure (useful for CI)
    "screenshotOnFailure": True,
}

# ──────────────────────────────────────────────────────────────────────────────
# Element Locator Strategies
# ──────────────────────────────────────────────────────────────────────────────
# These resource-ids are inferred from the Kotlin Compose screens in the app.
# Compose uses semantic properties / accessibility labels, not XML IDs.
# Use AppiumBy.ACCESSIBILITY_ID for content-desc and AppiumBy.XPATH for text.

LOCATORS = {
    # ── Splash ────────────────────────────────────────────────────────────────
    "splash_app_name": ("accessibility_id", "OralDysplasia AI"),

    # ── Login Screen ──────────────────────────────────────────────────────────
    "login_email_field": ("xpath", '//*[@content-desc="email" or @hint="name@hospital.com" or @text="Clinical Email Address"]'),
    "login_password_field": ("xpath", '//*[@content-desc="password" or @hint="••••••••"]'),
    "login_submit_btn": ("xpath", '//*[@text="Access Hub" or @text="Sign In" or @content-desc="Access Hub"]'),
    "login_goto_signup": ("xpath", '//*[@text="Register License Key" or @text="Sign Up"]'),
    "login_forgot_password": ("xpath", '//*[@text="Forgot Password?" or @text="Forgot Password"]'),

    # ── Sign Up Screen ────────────────────────────────────────────────────────
    "signup_name_field": ("xpath", '//*[@content-desc="full_name" or @hint="Dr. Jane Doe"]'),
    "signup_email_field": ("xpath", '//*[@content-desc="signup_email" or @hint="name@hospital.com" and @index="1"]'),
    "signup_license_field": ("xpath", '//*[@content-desc="license" or @hint="LIC-999-DENT"]'),
    "signup_role_dropdown": ("xpath", '//*[@content-desc="role_dropdown" or @text="Consultant Pathologist"]'),
    "signup_institution_field": ("xpath", '//*[@content-desc="institution" or @hint="City Medical Center"]'),
    "signup_password_field": ("xpath", '//*[@content-desc="signup_password" or @hint="Min 6 characters"]'),
    "signup_submit_btn": ("xpath", '//*[@text="Register License" or @content-desc="Register License"]'),

    # ── Bottom Navigation ────────────────────────────────────────────────────
    "nav_home": ("xpath", '//*[@content-desc="Home" or @text="Home"]'),
    "nav_upload": ("xpath", '//*[@content-desc="Upload" or @text="Upload"]'),
    "nav_library": ("xpath", '//*[@content-desc="Library" or @text="Library"]'),
    "nav_profile": ("xpath", '//*[@content-desc="Profile" or @text="Profile"]'),

    # ── Home / Dashboard ──────────────────────────────────────────────────────
    "dashboard_welcome": ("xpath", '//*[contains(@text, "Welcome") or contains(@content-desc, "Welcome")]'),
    "kpi_total_slides": ("xpath", '//*[@content-desc="kpi_total" or contains(@text, "Total")]'),
    "kpi_pending": ("xpath", '//*[@content-desc="kpi_pending" or contains(@text, "Pending")]'),
    "kpi_severe": ("xpath", '//*[@content-desc="kpi_severe" or contains(@text, "Severe")]'),
    "recent_cases_list": ("class_name", "androidx.recyclerview.widget.RecyclerView"),

    # ── Upload Screen ─────────────────────────────────────────────────────────
    "upload_patient_id": ("xpath", '//*[@content-desc="patient_id" or @hint="PT-888-CASE"]'),
    "upload_patient_name": ("xpath", '//*[@content-desc="patient_name" or @hint="John Doe"]'),
    "upload_patient_age": ("xpath", '//*[@content-desc="patient_age" or @hint="e.g. 45"]'),
    "upload_gender_dropdown": ("xpath", '//*[@content-desc="gender_dropdown"]'),
    "upload_site_dropdown": ("xpath", '//*[@content-desc="site_dropdown"]'),
    "upload_notes": ("xpath", '//*[@content-desc="clinical_notes" or @hint="Anamnesis description"]'),
    "upload_mock_slide_a": ("xpath", '//*[@text="Pick Mock Slide A" or @content-desc="pick_mock_a"]'),
    "upload_mock_slide_b": ("xpath", '//*[@text="Pick Mock Slide B" or @content-desc="pick_mock_b"]'),
    "upload_submit_btn": ("xpath", '//*[@text="Upload & Run Diagnostic Pipeline" or @content-desc="upload_submit"]'),

    # ── Biopsy Library ────────────────────────────────────────────────────────
    "library_case_list": ("class_name", "android.widget.ScrollView"),
    "library_filter_all": ("xpath", '//*[@text="ALL" or @content-desc="filter_all"]'),
    "library_filter_pending": ("xpath", '//*[@text="PENDING" or @content-desc="filter_pending"]'),
    "library_filter_severe": ("xpath", '//*[@text="SEVERE" or @content-desc="filter_severe"]'),

    # ── Slide Detail ──────────────────────────────────────────────────────────
    "detail_filename": ("xpath", '//*[@content-desc="detail_filename"]'),
    "detail_status_badge": ("xpath", '//*[@content-desc="detail_status"]'),
    "detail_grade_chip": ("xpath", '//*[@content-desc="detail_grade"]'),
    "detail_patient_id": ("xpath", '//*[@content-desc="detail_patient_id"]'),
    "detail_ai_runner_btn": ("xpath", '//*[@text="Initialize AI Diagnostic Runner" or @content-desc="btn_initialize_analysis"]'),
    "detail_back_btn": ("xpath", '//*[@content-desc="Navigate up" or @class="android.widget.ImageButton"]'),

    # ── AI Analysis ──────────────────────────────────────────────────────────
    "analysis_progress": ("xpath", '//*[@content-desc="analysis_progress"]'),
    "analysis_grade_chip": ("xpath", '//*[@content-desc="analysis_grade"]'),
    "analysis_confidence": ("xpath", '//*[@content-desc="analysis_confidence"]'),
    "open_canvas_btn": ("xpath", '//*[@text="Open AI Diagnostics Canvas" or @content-desc="btn_open_diagnostics"]'),

    # ── Results / Verdict ─────────────────────────────────────────────────────
    "results_grade_dropdown": ("xpath", '//*[@content-desc="canvas_final_grade"]'),
    "results_who_checklist": ("xpath", '//*[@text="WHO Histological Checklist" or @content-desc="who_checklist"]'),
    "results_icd_dropdown": ("xpath", '//*[@content-desc="canvas_icd_select"]'),
    "results_comments": ("xpath", '//*[@content-desc="canvas_comments"]'),
    "results_submit_btn": ("xpath", '//*[@text="Submit Verified Review" or @content-desc="btn_submit_review"]'),
    "results_success_msg": ("xpath", '//*[@content-desc="canvas_status_msg"]'),

    # ── Profile ───────────────────────────────────────────────────────────────
    "profile_name": ("xpath", '//*[@content-desc="profile_name"]'),
    "profile_email": ("xpath", '//*[@content-desc="profile_email"]'),
    "profile_license": ("xpath", '//*[@content-desc="profile_license"]'),
    "profile_role": ("xpath", '//*[@content-desc="profile_role"]'),
    "profile_institution": ("xpath", '//*[@content-desc="profile_institution"]'),
    "profile_logout_btn": ("xpath", '//*[@text="Logout" or @content-desc="logout_btn"]'),
}

# ──────────────────────────────────────────────────────────────────────────────
# Device Utilities
# ──────────────────────────────────────────────────────────────────────────────

def get_connected_devices():
    """Returns a list of connected Android device IDs via adb."""
    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True, text=True, timeout=10
        )
        lines = result.stdout.strip().split("\n")[1:]  # skip header line
        devices = [
            line.split("\t")[0]
            for line in lines
            if line.strip() and "offline" not in line and "unauthorized" not in line
        ]
        return devices
    except Exception as e:
        print(f"[WARN] adb not found or failed: {e}")
        return []


def is_device_connected():
    """Check if any Android device is connected."""
    devices = get_connected_devices()
    if devices:
        print(f"[INFO] Connected device(s): {devices}")
        return True
    print("[WARN] No Android device/emulator connected (adb devices returned empty).")
    return False


def is_appium_running():
    """Ping Appium server to check if it is running."""
    try:
        import urllib.request
        status_url = APPIUM_SERVER_URL.rstrip("/") + "/status"
        resp = urllib.request.urlopen(status_url, timeout=5)
        return resp.status == 200
    except Exception:
        return False


def print_setup_instructions():
    """Print setup instructions for running live Appium tests."""
    print("\n" + "=" * 70)
    print("  APPIUM LIVE TEST SETUP INSTRUCTIONS")
    print("=" * 70)
    print("  1. Install Appium 2.x:")
    print("     npm install -g appium@latest")
    print("  2. Install UiAutomator2 driver:")
    print("     appium driver install uiautomator2")
    print("  3. Start Appium server:")
    print("     appium --port 4723")
    print("  4. Start Android Emulator (Android Studio AVD Manager)")
    print("     OR connect a real Android device with USB debugging enabled")
    print("  5. Verify device connection:")
    print("     adb devices")
    print("  6. Build & install OralDysplasia AI APK on the device:")
    print("     cd android && gradlew installDebug")
    print("  7. Start the backend server:")
    print("     cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000")
    print("  8. Run the Appium test suite:")
    print("     cd appium_tests && python run_appium_tests.py")
    print("=" * 70 + "\n")


# ──────────────────────────────────────────────────────────────────────────────
# Pre-flight Check
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("[CHECK] Verifying Appium test environment readiness...")

    appium_ok = is_appium_running()
    device_ok = is_device_connected()

    print(f"  Appium Server ({APPIUM_SERVER_URL}): {'✔ RUNNING' if appium_ok else '✘ NOT RUNNING'}")
    print(f"  Android Device: {'✔ CONNECTED' if device_ok else '✘ NOT CONNECTED'}")
    print(f"  Target Package: {ANDROID_CAPS['appPackage']}")
    print(f"  Platform: Android {ANDROID_CAPS['platformVersion']}")

    if not appium_ok or not device_ok:
        print_setup_instructions()
    else:
        print("\n[OK] Environment ready. Run: python run_appium_tests.py\n")

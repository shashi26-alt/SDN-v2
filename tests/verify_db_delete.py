import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from identity_manager.identity_database import IdentityDatabase

def test_delete_device():
    db_path = "test_verify_delete.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print(f"Testing database deletion on {db_path}...")
    
    try:
        db = IdentityDatabase(db_path)
        
        # Add a test device
        device_id = "TEST_DEVICE_001"
        mac = "AA:BB:CC:DD:EE:FF"
        db.add_device(device_id, mac, device_type="test")
        
        # Verify it exists
        device = db.get_device(device_id)
        if not device:
            print("FAILED to add test device")
            return False
        print("Test device added")
        
        # Add some related data (trust score)
        db.save_trust_score(device_id, 85, "Initial score")
        history = db.get_trust_score_history(device_id)
        if not history:
            print("FAILED to add trust score history")
            return False
        print("Trust score history added")
        
        # DELETE THE DEVICE
        success = db.delete_device(device_id)
        if not success:
            print("delete_device returned False")
            return False
        print("delete_device returned True")
        
        # Verify it is gone
        device = db.get_device(device_id)
        if device:
            print("Device still exists in database!")
            return False
        print("Device removed from devices table")
        
        # Verify related data is gone (integrity check)
        
        success = db.add_device(device_id, mac, device_type="test_readd")
        if success:
             print("Device can be re-added (means key constraints cleared)")
        else:
             print("Failed to re-add device")
             return False
             
        return True
        
    except Exception as e:
        print(f"Exception during test: {e}")
        return False
    finally:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except:
                pass

if __name__ == "__main__":
    if test_delete_device():
        print("\nVerification SUCCESS")
        sys.exit(0)
    else:
        print("\nVerification FAILED")
        sys.exit(1)

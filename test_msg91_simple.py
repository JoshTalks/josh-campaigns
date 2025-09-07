#!/usr/bin/env python3
"""
Simple MSG91 Email Test Function

This script contains a single function that tests MSG91 email sending
by taking all necessary variables as parameters and sending a real email.

Usage:
    python test_msg91_simple.py
"""

import http.client
import json
import time
from datetime import datetime

def test_msg91_email_sending():
    """
    Test MSG91 email sending with provided parameters
    
    Args:
        auth_key (str): Your MSG91 authentication key
        test_email (str): Email address to send test email to
        from_email (str): Sender email address (must be verified in MSG91)
        from_name (str): Sender name (default: "Test Sender")
        domain (str): Your verified domain in MSG91 (default: "example.com")
    
    Returns:
        dict: Test results with success status and details
    """
    import http.client

    conn = http.client.HTTPSConnection("control.msg91.com")
    
    try:
        payload = {
            "recipients": [
                {
                    "to": [
                        {
                            "name": "Avi",
                            "email": "avivish000@gmail.com"
                        }
                    ],
                    "variables": {
                        "company_name": "Avu",
                        "otp": "1234"
                    }
                },
                {
                    "to": [
                        {
                            "name": "Avi2",
                            "email": "avikumar@joshtalks.com"
                        }
                    ],
                    "variables": {
                        "company_name": "Avu2",
                        "otp": "431124"
                    }
                }
            ],
            "from": {
                "name": "Josh2",
                "email": "developers@joshtalks.com"
            },
            "domain": "joshjobs.joshtalks.com",
            "template_id": "global_otp"
        }

        headers = {
            'accept': "application/json",
            'authkey': "465189AMRdJW6Oa68a43d18P1",
            'content-type': "application/JSON"
        }

        # Convert payload to JSON string
        payload_json = json.dumps(payload)
        
        conn.request("POST", "/api/v5/email/send", payload_json, headers)

        res = conn.getresponse()
        data = res.read()
        result = json.loads(data.decode("utf-8"))

        print(data.decode("utf-8"))
        
        # Check response and return result
        if res.status == 200 and (result.get('status') == 'success' or result.get('hasError') == False):
            print("\n🎉 SUCCESS! Email sent successfully!")
            print("   📧 Check your inboxes for the test emails!")
            
            return {
                'success': True,
                'message': 'Emails sent successfully',
                'response': result,
                'status_code': res.status,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            error_msg = result.get('message', 'Unknown error from MSG91')
            print(f"\n❌ FAILED! Email sending failed.")
            print(f"   Error: {error_msg}")
            
            return {
                'success': False,
                'error': error_msg,
                'response': result,
                'status_code': res.status,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    except Exception as e:
        error_msg = str(e)
        print(f"\n💥 EXCEPTION! Test failed with error:")
        print(f"   Error: {error_msg}")
        
        return {
            'success': False,
            'error': error_msg,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    finally:
        # Clean up connection
        try:
            conn.close()
        except:
            pass

def main():
    """Main function to run the test"""
    
    print("🎯 MSG91 Email Test Function")
    print("=" * 50)
    print("This function will send real test emails via MSG91 API")
    print("=" * 50)
    print()
    
    # Run the test
    result = test_msg91_email_sending()
    
    print()
    print("=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    if result and result.get('success'):
        print("✅ SUCCESS: Emails sent successfully!")
        print(f"   📧 Check your inboxes for the test emails!")
        print(f"   ⏰ Sent at: {result.get('timestamp', 'Unknown')}")
    else:
        print("❌ FAILED: Email sending failed!")
        if result:
            print(f"   🚫 Error: {result.get('error', 'Unknown error')}")
            print(f"   ⏰ Failed at: {result.get('timestamp', 'Unknown')}")
        else:
            print("   🚫 Error: No result returned from function")
    
    print()
    print("🔍 For more details, check the output above.")
    print("📚 Visit https://msg91.com for MSG91 documentation and support.")

if __name__ == "__main__":
    main()

"""Test email connectivity"""
import socket
import smtplib
import ssl

print("\n" + "="*80)
print("TESTING EMAIL CONNECTION")
print("="*80 + "\n")

# Test 1: DNS Resolution
print("1. Testing DNS resolution for smtp.gmail.com...")
try:
    ip = socket.gethostbyname('smtp.gmail.com')
    print(f"   ✓ Resolved to: {ip}")
except socket.gaierror as e:
    print(f"   ✗ DNS Resolution Failed: {e}")
    print("   → Check your internet connection or DNS settings")
    exit(1)

# Test 2: Port connectivity
print("\n2. Testing connection to smtp.gmail.com:587...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    result = sock.connect_ex(('smtp.gmail.com', 587))
    if result == 0:
        print("   ✓ Port 587 is reachable")
    else:
        print(f"   ✗ Cannot connect to port 587 (error code: {result})")
        print("   → Check firewall or antivirus settings")
    sock.close()
except Exception as e:
    print(f"   ✗ Connection test failed: {e}")
    exit(1)

# Test 3: SMTP connection
print("\n3. Testing SMTP connection...")
try:
    server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
    server.ehlo()
    print("   ✓ SMTP connection established")
    
    print("\n4. Testing STARTTLS...")
    server.starttls()
    print("   ✓ TLS connection established")
    
    server.quit()
    print("\n✓ All connectivity tests passed!")
    print("\nNow testing with your credentials...\n")
    
except Exception as e:
    print(f"   ✗ SMTP test failed: {e}")
    exit(1)

# Test 4: Authentication (with credentials from .env)
print("5. Testing authentication...")
try:
    import os
    import sys
    import pathlib
    
    # Load environment
    SYNAPSE_PATH = str(pathlib.Path(__file__).parent.absolute())
    sys.path.insert(0, SYNAPSE_PATH)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.synapse")
    
    from dotenv import load_dotenv
    env_path = pathlib.Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=True)
    
    email_user = os.getenv('EMAIL_HOST_USER')
    email_pass = os.getenv('EMAIL_HOST_PASSWORD')
    
    if not email_user or not email_pass:
        print("   ✗ EMAIL_HOST_USER or EMAIL_HOST_PASSWORD not found in .env")
        exit(1)
    
    print(f"   Email: {email_user}")
    print(f"   Password: {'*' * len(email_pass)}")
    
    server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
    server.starttls()
    server.login(email_user, email_pass)
    print("   ✓ Authentication successful!")
    server.quit()
    
    print("\n" + "="*80)
    print("ALL TESTS PASSED - Email should work!")
    print("="*80 + "\n")
    
except smtplib.SMTPAuthenticationError as e:
    print(f"   ✗ Authentication failed: {e}")
    print("\n   Possible fixes:")
    print("   1. Enable 2FA and generate an App Password:")
    print("      https://myaccount.google.com/apppasswords")
    print("   2. Or enable 'Less secure app access' (not recommended):")
    print("      https://myaccount.google.com/lesssecureapps")
except Exception as e:
    print(f"   ✗ Test failed: {e}")
    exit(1)

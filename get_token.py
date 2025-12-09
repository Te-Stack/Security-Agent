import os
from getstream import Stream

# 1. Get keys from the environment (loaded by uv)
key = os.getenv("STREAM_API_KEY")
secret = os.getenv("STREAM_API_SECRET")

if not key or not secret:
    print("❌ Error: Could not find API keys. Make sure you run with --env-file .env")
    exit(1)

# 2. Initialize Stream
client = Stream(key, secret)

# 3. Generate Token for Shaq12
user_id = "Shaq12"
token = client.create_token(user_id)

print(f"\n✅ TOKEN FOR {user_id}:")
print(token)
print("\nCopy the string above and paste it into App.tsx")
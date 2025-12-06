"""Test database connection."""
import asyncio
from story_generator.database import db

async def main():
    print("🔍 Testing database connection...")
    
    # Test health check
    health = await db.health_check()
    
    if health:
        print("✅ Database connected successfully!")
        
        # Test query
        try:
            result = db.client.table("users").select("*").limit(1).execute()
            print(f"✅ Query successful! Found {len(result.data)} users")
        except Exception as e:
            print(f"❌ Query failed: {e}")
    else:
        print("❌ Database connection failed!")
        print("Check your SUPABASE_URL and SUPABASE_KEY in .env")

if __name__ == "__main__":
    asyncio.run(main())
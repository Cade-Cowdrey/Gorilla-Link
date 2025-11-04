"""
Add Federal Grants to Database
Run this script to add 5 major federal grants (Pell, FSEOG, TEACH, etc.)
"""

from app_pro import app
from federal_aid_api import add_federal_grants
from loguru import logger

if __name__ == "__main__":
    logger.info("🇺🇸 Starting Federal Grant Import...")
    
    with app.app_context():
        try:
            count = add_federal_grants()
            logger.info(f"✅ SUCCESS! Added {count} federal grants to database")
            print("\n" + "="*60)
            print("🎉 FEDERAL GRANTS ADDED SUCCESSFULLY!")
            print("="*60)
            print(f"\n✅ {count} federal grants imported:")
            print("   • Federal Pell Grant ($7,395)")
            print("   • FSEOG ($4,000)")
            print("   • TEACH Grant ($4,000)")
            print("   • Iraq/Afghanistan Service Grant ($7,395)")
            print("   • Federal Work-Study ($5,000)")
            print("\n💰 Total Federal Funding Added: $27,790")
            print("\n🌐 Visit your site to see them:")
            print("   https://pittstate-connect.onrender.com/scholarships/browse")
            print("="*60 + "\n")
            
        except Exception as e:
            logger.error(f"❌ Error adding federal grants: {e}")
            print(f"\n❌ Error: {e}")

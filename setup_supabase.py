from database.config import get_supabase
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def seed_admin():
    supabase = get_supabase()
    
    admin_email = "admin@hragent.ai"
    admin_password = "Admin@123"
    
    try:
        # Check if admin profile already exists
        response = supabase.table("profiles").select("*").eq("email", admin_email).execute()
        
        if len(response.data) == 0:
            logger.info("Admin user not found. Attempting to seed...")
            
            # Since we don't have a service_role key to bypass email confirmation,
            # this assumes email confirmations are disabled in the Supabase Dashboard.
            # If they are enabled, the admin will receive an email.
            try:
                # Store any current session so we don't accidentally log out the current user
                # Although this is typically run on app startup
                auth_res = supabase.auth.sign_up({
                    "email": admin_email,
                    "password": admin_password,
                    "options": {
                        "data": {
                            "name": "Super Admin"
                        }
                    }
                })
                
                if auth_res.user:
                    logger.info(f"Successfully seeded admin user: {admin_email}")
                else:
                    logger.warning("Sign up executed, but no user returned. Email confirmation might be required.")
            except Exception as e:
                if "already registered" in str(e).lower():
                    logger.info("Admin user already registered in Auth.")
                else:
                    logger.error(f"Error seeding admin user: {e}")
        else:
            logger.info("Admin user already seeded in Database.")
            
    except Exception as e:
        logger.error(f"Error checking profiles: {e}")

if __name__ == "__main__":
    seed_admin()

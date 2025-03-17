from fastapi import APIRouter
from app.api.endpoints import webhooks, email_configs, processed_emails, stats, auth, websocket
import inspect

router = APIRouter()

# Add debug output
print("="*80)
print("CONFIGURING API ENDPOINTS")
print("="*80)

# Check if modules are properly imported
for module_name, module in [
    ("webhooks", webhooks),
    ("email_configs", email_configs),
    ("processed_emails", processed_emails),
    ("stats", stats), 
    ("auth", auth),
    ("websocket", websocket)
]:
    print(f"Module {module_name}: {module}")
    if hasattr(module, "router"):
        print(f"  Has router: YES")
        if hasattr(module.router, "routes"):
            routes_count = len(module.router.routes)
            print(f"  Routes count: {routes_count}")
            for route in module.router.routes:
                print(f"    - {route}")
        else:
            print(f"  Routes count: NONE")
    else:
        print(f"  Has router: NO")
print("="*80)

# Include routers
router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
router.include_router(email_configs.router,
                      prefix="/email-configs", tags=["email-configs"])
router.include_router(processed_emails.router,
                      prefix="/processed-emails", tags=["processed-emails"])
router.include_router(stats.router, prefix="/stats", tags=["stats"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(websocket.router, prefix="/ws", tags=["websocket"])

# Print final router configuration
print("="*80)
print("FINAL ROUTER CONFIGURATION")
print("="*80)
print(f"Router routes count: {len(router.routes)}")
for route in router.routes:
    print(f"  - {route}")
print("="*80)

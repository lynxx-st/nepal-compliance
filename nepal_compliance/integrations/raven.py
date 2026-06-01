"""
Raven integration hooks for Nepal Compliance.

Automatically adds new ERPNext users to Raven (team chat) so they appear
in channel member searches without manual setup.
"""

import frappe


def auto_add_raven_user(doc, method=None):
    """
    after_insert hook on User — create a Raven User record for every
    new real (non-system, non-Guest) user.
    """
    if _skip(doc):
        return

    if frappe.db.exists("Raven User", {"user": doc.name}):
        return  # already exists

    try:
        raven_user = frappe.new_doc("Raven User")
        raven_user.user       = doc.name
        raven_user.full_name  = doc.full_name or doc.name
        raven_user.first_name = doc.first_name or doc.full_name or doc.name
        raven_user.enabled    = 1
        raven_user.type       = "User"
        raven_user.insert(ignore_permissions=True)
        frappe.logger().info(f"[nepal_compliance] Created Raven User for {doc.name}")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Raven auto_add_raven_user failed")

    _ensure_raven_role(doc.name)


def sync_raven_user(doc, method=None):
    """
    on_update hook on User — keep full_name in sync and ensure
    the Raven User role is present.
    """
    if _skip(doc):
        return

    # Create record if missing (e.g. user existed before this hook was deployed)
    if not frappe.db.exists("Raven User", {"user": doc.name}):
        auto_add_raven_user(doc, method)
        return

    # Sync name change
    try:
        raven_user = frappe.get_doc("Raven User", {"user": doc.name})
        changed = False
        if raven_user.full_name != doc.full_name:
            raven_user.full_name  = doc.full_name or doc.name
            raven_user.first_name = doc.first_name or doc.full_name or doc.name
            changed = True
        if doc.enabled == 0 and raven_user.enabled:
            raven_user.enabled = 0
            changed = True
        if doc.enabled == 1 and not raven_user.enabled:
            raven_user.enabled = 1
            changed = True
        if changed:
            raven_user.save(ignore_permissions=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Raven sync_raven_user failed")

    _ensure_raven_role(doc.name)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _skip(doc):
    """Return True for users that should not be added to Raven."""
    SYSTEM_USERS = {"Guest", "Administrator"}
    if doc.name in SYSTEM_USERS:
        return True
    if getattr(doc, "user_type", None) not in (None, "System User", "Website User"):
        return True
    # Skip if Raven is not installed
    if "raven" not in frappe.get_installed_apps():
        return True
    return False


def _ensure_raven_role(user_name):
    """Add the Raven User role if not already present."""
    try:
        if not frappe.db.exists("Has Role", {"parent": user_name, "role": "Raven User"}):
            user_doc = frappe.get_doc("User", user_name)
            # Skip users with role profiles (Raven can't override them)
            if user_doc.role_profile_name or (
                hasattr(user_doc, "role_profiles") and user_doc.role_profiles
            ):
                return
            user_doc.append("roles", {"role": "Raven User"})
            user_doc.save(ignore_permissions=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Raven _ensure_raven_role failed")

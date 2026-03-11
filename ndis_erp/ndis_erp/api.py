# -*- coding: utf-8 -*-
# Copyright (c) 2025, ndis_erp and contributors
# For license information, please see license.txt
"""
ndis_erp API – whitelisted endpoints for the React frontend.
Module path: ndis_erp.ndis_erp.api (api.py lives in ndis_erp/ndis_erp/ndis_erp/)
"""

from __future__ import unicode_literals

import json
import re
import frappe
from frappe.exceptions import DuplicateEntryError


# ---------------------------------------------------------------------------
# Test & health
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def test_connection():
	"""Test endpoint to verify the React frontend can reach the ERP API."""
	try:
		frappe.logger().info("ndis_erp test_connection called")
		return {
			"status": "success",
			"message": "ERP API connected",
			"timestamp": frappe.utils.now(),
			"server": "ndis_erp",
		}
	except Exception as e:
		frappe.logger().error("test_connection failed: %s", str(e))
		return {
			"status": "error",
			"message": str(e),
		}


# ---------------------------------------------------------------------------
# Website settings (navbar logo, footer logo, address, company contact)
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def get_website_settings():
	"""
	Fetch Website Settings and Company data for the React frontend.
	Returns: app_logo, footer_logo, address (from Website Settings),
	         phone_no, email (from default Company).
	"""
	try:
		frappe.set_user("Guest")
		frappe.local.flags.ignore_permissions = True

		settings = frappe.get_single("Website Settings")
		app_logo = getattr(settings, "app_logo", None) or getattr(settings, "logo", None) or getattr(settings, "banner_image", None) or ""
		footer_logo = getattr(settings, "footer_logo", None) or ""
		address = getattr(settings, "address", None) or ""

		default_company = frappe.get_cached_value("Global Defaults", None, "default_company")
		phone_no = ""
		email = ""
		company_description = ""
		if default_company:
			company = frappe.get_cached_value(
				"Company",
				default_company,
				["phone_no", "email", "company_description"],
				as_dict=True
			)
			if company:
				phone_no = company.get("phone_no") or ""
				email = company.get("email") or ""
				company_description = company.get("company_description") or ""

		return {
			"success": True,
			"app_logo": app_logo,
			"footer_logo": footer_logo,
			"address": address,
			"phone_no": phone_no,
			"email": email,
			"company_description": company_description,
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Website Settings API")
		frappe.logger().error("get_website_settings failed: %s", str(e))
		return {
			"success": False,
			"error": str(e),
			"app_logo": "",
			"footer_logo": "",
			"address": "",
			"phone_no": "",
			"email": "",
			"company_description": "",
		}


@frappe.whitelist(allow_guest=True)
def get_company_description():
	"""
	Fetch company_description (rich text / text editor) from the default Company.

	Returns:
		{
			"success": True,
			"company_description": "<html or plain text>",
		}
	"""
	try:
		frappe.set_user("Guest")
		frappe.local.flags.ignore_permissions = True

		default_company = frappe.get_cached_value("Global Defaults", None, "default_company")
		if not default_company:
			return {"success": False, "company_description": "", "error": "Default company not set"}

		company_description = frappe.get_cached_value(
			"Company",
			default_company,
			"company_description",
		) or ""

		return {
			"success": True,
			"company_description": company_description,
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Company Description API")
		frappe.logger().error("get_company_description failed: %s", str(e))
		return {
			"success": False,
			"company_description": "",
			"error": str(e),
		}


# ---------------------------------------------------------------------------
# Services – list & detail APIs for frontend
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def get_services():
	"""
	Fetch all Services records for the public website.

	Returns:
		{
			"success": True,
			"data": [
				{
					"name": str,
					"title": str,
					"subtitle": str,
					"image": str,
					"description": str,
				},
				...
			]
		}
	"""
	try:
		frappe.set_user("Guest")
		frappe.local.flags.ignore_permissions = True

		services = frappe.get_all(
			"Services",
			fields=["name", "service_name", "title", "subtitle", "image", "description"],
			order_by="idx asc, modified desc",
		)
		return {"success": True, "data": services}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Services API")
		frappe.logger().error("get_services failed: %s", str(e))
		return {"success": False, "data": [], "error": str(e)}


@frappe.whitelist(allow_guest=True)
def get_service(name):
	"""
	Fetch a single Service record by name (docname).

	Args:
		name (str): Docname of the Service (usually same as Title, via autoname field:title).
	"""
	try:
		frappe.set_user("Guest")
		frappe.local.flags.ignore_permissions = True

		if not name:
			return {"success": False, "error": "Service name is required"}

		docname = name
		if not frappe.db.exists("Services", docname):
			# Fallback: try matching by Title if a plain title string is passed
			match = frappe.get_all("Services", filters={"title": name}, fields=["name"], limit=1)
			if not match:
				return {"success": False, "error": "Service not found"}
			docname = match[0].name

		doc = frappe.get_doc("Services", docname)
		data = {
			"name": doc.name,
			"service_name": getattr(doc, "service_name", "") or "",
			"title": doc.title,
			"subtitle": getattr(doc, "subtitle", "") or "",
			"image": getattr(doc, "image", "") or "",
			"description": getattr(doc, "description", "") or "",
		}
		return {"success": True, "data": data}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Service API")
		frappe.logger().error("get_service failed: %s", str(e))
		return {"success": False, "data": None, "error": str(e)}


# ---------------------------------------------------------------------------
# Testimonials – list API for frontend
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def get_testimonials():
	"""
	Fetch Testimonial records for the public website.

	Fields expected on the Testimonial DocType:
	- name1, role, image, detail, rating
	"""
	try:
		frappe.set_user("Guest")
		frappe.local.flags.ignore_permissions = True

		rows = frappe.get_all(
			"Testimonial",
			fields=["name", "name1", "role", "image", "detail", "rating"],
			order_by="idx asc, modified desc",
		)
		out = []
		for r in rows or []:
			if isinstance(r, dict):
				out.append({
					"name": r.get("name"),
					"name1": r.get("name1") or "",
					"role": r.get("role") or "",
					"image": r.get("image") or "",
					"detail": r.get("detail") or "",
					"rating": r.get("rating") or 0,
				})
			else:
				out.append({
					"name": getattr(r, "name", None),
					"name1": getattr(r, "name1", "") or "",
					"role": getattr(r, "role", "") or "",
					"image": getattr(r, "image", "") or "",
					"detail": getattr(r, "detail", "") or "",
					"rating": getattr(r, "rating", 0) or 0,
				})
		return {"success": True, "data": out}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Testimonials API")
		frappe.logger().error("get_testimonials failed: %s", str(e))
		return {"success": False, "data": [], "error": str(e)}


# ---------------------------------------------------------------------------
# Web Page – content API for frontend (Terms / Privacy)
# ---------------------------------------------------------------------------

def _web_page_content_by_route(route):
	"""Return published Web Page content (main_section) by route."""
	if not route:
		return None
	names = frappe.get_all("Web Page", filters={"route": route, "published": 1}, fields=["name"], limit=1)
	if not names:
		return None
	page = frappe.get_doc("Web Page", names[0].name)
	# Rich Text pages store HTML in main_section; keep fallbacks for older/custom fields.
	content = getattr(page, "main_section", None) or getattr(page, "content", None) or getattr(page, "body", None) or ""
	return {
		"name": page.name,
		"title": getattr(page, "title", "") or "",
		"route": getattr(page, "route", "") or route,
		"content": content or "",
		"modified": str(getattr(page, "modified", "") or ""),
	}


@frappe.whitelist(allow_guest=True)
def get_web_page_content(route):
	"""Fetch published Web Page rich text content by route."""
	try:
		frappe.set_user("Guest")
		frappe.local.flags.ignore_permissions = True
		data = _web_page_content_by_route(route)
		if not data:
			return {"success": False, "error": "Page not found", "data": None}
		return {"success": True, "data": data}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Web Page Content API")
		return {"success": False, "error": str(e), "data": None}


@frappe.whitelist(allow_guest=True)
def get_terms_and_conditions():
	"""Convenience API for route=terms-and-conditions."""
	return get_web_page_content("terms-and-conditions")


@frappe.whitelist(allow_guest=True)
def get_privacy_policy():
	"""Convenience API for route=privacy-policy."""
	return get_web_page_content("privacy-policy")


# ---------------------------------------------------------------------------
# About Us – single doctype (title, subtitle, description, aboutus_section, leadership)
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def get_about_us():
	"""
	Fetch About Us single doctype for the public website.
	Returns: title, subtitle, description, about_title, image; aboutus_section (cards: title, details);
	         leadership_title, leadership_subtitle; aboutus_leadership (image, name1, designation, team_detail).
	"""
	try:
		frappe.set_user("Guest")
		frappe.local.flags.ignore_permissions = True

		doc = frappe.get_single("About Us")
		aboutus_section = []
		for row in getattr(doc, "aboutus_section", []) or []:
			aboutus_section.append({
				"title": getattr(row, "title", "") or "",
				"details": getattr(row, "details", "") or "",
			})
		aboutus_leadership = []
		for row in getattr(doc, "aboutus_leadership", []) or []:
			aboutus_leadership.append({
				"image": getattr(row, "image", "") or "",
				"name1": getattr(row, "name1", "") or "",
				"designation": getattr(row, "designation", "") or "",
				"team_detail": getattr(row, "team_detail", "") or "",
			})

		data = {
			"title": getattr(doc, "title", "") or "",
			"subtitle": getattr(doc, "subtitle", "") or "",
			"description": getattr(doc, "description", "") or "",
			"about_title": getattr(doc, "about_title", "") or "",
			"image": getattr(doc, "image", "") or "",
			"aboutus_section": aboutus_section,
			"leadership_title": getattr(doc, "leadership_title", "") or "",
			"leadership_subtitle": getattr(doc, "leadership_subtitle", "") or "",
			"aboutus_leadership": aboutus_leadership,
		}
		return {"success": True, "data": data}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get About Us API")
		frappe.logger().error("get_about_us failed: %s", str(e))
		return {"success": False, "data": None, "error": str(e)}


# ---------------------------------------------------------------------------
# Home page builder (Page Building Blocks – same as get_home_page_builder?route=home)
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def get_home_page_builder(route="home"):
	"""
	Fetch Web Page by route (e.g. home) and return Page Building Blocks.
	Same pattern as krishna_royal_club get_home_page_builder.
	Returns: { "success": True, "data": [ { "web_template", "values", "background_image", "add_background_image" }, ... ], "count": N }
	"""
	try:
		frappe.set_user("Guest")
		frappe.local.flags.ignore_permissions = True

		names = frappe.get_all(
			"Web Page",
			filters={"route": route, "published": 1},
			limit=1,
		)
		if not names:
			return {"success": True, "data": [], "count": 0}

		page = frappe.get_doc("Web Page", names[0].name)
		data = []

		# Page Building Blocks: can be page_blocks (standard) or blocks
		blocks = getattr(page, "page_blocks", None) or getattr(page, "blocks", None) or []
		for row in blocks:
			values = getattr(row, "web_template_values", None) or getattr(row, "values", None) or {}
			if isinstance(values, str):
				try:
					values = json.loads(values or "{}")
				except (TypeError, ValueError):
					values = {}
			data.append({
				"web_template": getattr(row, "web_template", None) or getattr(row, "block_type", None) or "",
				"values": values if isinstance(values, dict) else {},
				"background_image": getattr(row, "background_image", None) or "",
				"add_background_image": getattr(row, "add_background_image", None) or 0,
			})

		return {"success": True, "data": data, "count": len(data)}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Home Page Builder API")
		frappe.logger().error("get_home_page_builder failed: %s", str(e))
		return {"success": True, "data": [], "count": 0}


# ---------------------------------------------------------------------------
# Home page hero (left text, right image; data from Web Page Hero block)
# ---------------------------------------------------------------------------

def _default_home_hero_slides():
	"""Default hero content when no Web Page hero data is found."""
	return [
		{
			"welcome_text": "Welcome to Perfection Care",
			"title": "Elevating care through reliable services",
			"description": "We connect people with tailored disability support services, ensuring consistent quality, clear communication, and measurable outcomes.",
			"primary_button_text": "View Services",
			"primary_button_link": "/services",
			"secondary_button_text": "Talk to Our Team",
			"secondary_button_link": "/contact",
			"image": "",
			"align": "Left",
		},
	]


def _slide_from_hero_values(values):
	"""Build one slide dict from Web Page / Hero block values (Edit Values form)."""
	if not values or not isinstance(values, dict):
		return None
	return {
		"welcome_text": values.get("welcome_text") or "",
		"title": values.get("title") or values.get("Title") or "",
		"description": (values.get("description") or values.get("subtitle") or values.get("Subtitle") or "").strip(),
		"primary_button_text": values.get("primary_action_label") or values.get("primary_button_text") or values.get("Primary Action Label") or "",
		"primary_button_link": values.get("primary_action_url") or values.get("primary_button_link") or values.get("Primary Action URL") or "",
		"secondary_button_text": values.get("secondary_action_label") or values.get("secondary_button_text") or values.get("Secondary Action Label") or "",
		"secondary_button_link": values.get("secondary_action_url") or values.get("secondary_button_link") or values.get("Secondary Action URL") or "",
		"image": values.get("image") or values.get("hero_image") or values.get("banner_image") or "",
		"align": values.get("align") or values.get("Align") or "Left",
	}


@frappe.whitelist(allow_guest=True)
def get_home_hero():
	"""
	Fetch hero content for the Home page. Used by the React frontend.
	Data source: Web Page "hero" (route home) or "home" – reads web_template_values (Hero block)
	or custom hero_slides JSON. Returns slides for left text + right image; align from form.
	"""
	try:
		frappe.set_user("Guest")
		frappe.local.flags.ignore_permissions = True

		# Try Web Page "hero" first (Edit Values URL: /app/web-page/hero), then "home"
		web_page = None
		for name in ("hero", "home"):
			if frappe.db.exists("Web Page", name):
				web_page = frappe.get_doc("Web Page", name)
				break
		if not web_page:
			names = frappe.get_all("Web Page", filters={"route": "home"}, limit=1)
			if names:
				web_page = frappe.get_doc("Web Page", names[0].name)

		if web_page:
			# 0) Page Building Blocks (page_blocks) – same as get_home_page_builder
			blocks = getattr(web_page, "page_blocks", None) or getattr(web_page, "blocks", None) or []
			hero_slides_out = []
			for row in blocks:
				wt = (getattr(row, "web_template", None) or getattr(row, "block_type", None) or "").lower()
				if "hero" not in wt:
					continue
				values = getattr(row, "web_template_values", None) or getattr(row, "values", None) or {}
				if isinstance(values, str):
					try:
						values = json.loads(values or "{}")
					except (TypeError, ValueError):
						values = {}
				bg_image = getattr(row, "background_image", None) or ""
				slide = _slide_from_hero_values(values) if isinstance(values, dict) else None
				if not slide:
					slide = {"welcome_text": "", "title": "", "description": "", "primary_button_text": "", "primary_button_link": "", "secondary_button_text": "", "secondary_button_link": "", "image": "", "align": "Left"}
				if bg_image and not slide.get("image"):
					slide["image"] = bg_image
				hero_slides_out.append(slide)
			if hero_slides_out:
				return {"success": True, "slides": hero_slides_out}

			# 1) Hero block values from Web Page Builder (web_template_values on Web Page)
			wtv = getattr(web_page, "web_template_values", None)
			if wtv:
				try:
					if isinstance(wtv, str):
						wtv = json.loads(wtv) if wtv.strip() else None
					if isinstance(wtv, dict):
						slide = _slide_from_hero_values(wtv)
						if slide and slide.get("title"):
							return {"success": True, "slides": [slide]}
				except (TypeError, ValueError):
					pass

			# 2) Custom hero_slides (JSON array) for multiple slides / slider
			hero_slides = getattr(web_page, "hero_slides", None)
			if hero_slides:
				try:
					if isinstance(hero_slides, (list, tuple)):
						slides = list(hero_slides)
					else:
						slides = json.loads(hero_slides) if isinstance(hero_slides, str) and hero_slides.strip() else None
					if slides and isinstance(slides, list) and len(slides) > 0:
						out = []
						for s in slides:
							if isinstance(s, dict):
								slide = _slide_from_hero_values(s) or {
									"welcome_text": s.get("welcome_text") or "",
									"title": s.get("title") or "",
									"description": s.get("description") or "",
									"primary_button_text": s.get("primary_button_text") or "",
									"primary_button_link": s.get("primary_button_link") or "",
									"secondary_button_text": s.get("secondary_button_text") or "",
									"secondary_button_link": s.get("secondary_button_link") or "",
									"image": s.get("image") or "",
									"align": s.get("align") or "Left",
								}
								out.append(slide)
						if out:
							return {"success": True, "slides": out}
				except (TypeError, ValueError):
					pass

			# 3) Direct custom fields on Web Page (snake_case)
			slide = _slide_from_hero_values({
				"title": getattr(web_page, "title", None) or getattr(web_page, "hero_title", None),
				"subtitle": getattr(web_page, "subtitle", None) or getattr(web_page, "hero_subtitle", None) or getattr(web_page, "description", None),
				"primary_action_label": getattr(web_page, "primary_action_label", None),
				"primary_action_url": getattr(web_page, "primary_action_url", None),
				"secondary_action_label": getattr(web_page, "secondary_action_label", None),
				"secondary_action_url": getattr(web_page, "secondary_action_url", None),
				"align": getattr(web_page, "hero_align", None) or getattr(web_page, "align", None),
				"image": getattr(web_page, "hero_image", None) or getattr(web_page, "banner_image", None),
			})
			if slide and slide.get("title"):
				return {"success": True, "slides": [slide]}

		return {"success": True, "slides": _default_home_hero_slides()}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Home Hero API")
		frappe.logger().error("get_home_hero failed: %s", str(e))
		return {"success": True, "slides": _default_home_hero_slides()}


# ---------------------------------------------------------------------------
# Signup (create Lead + User for website)
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def signup(**kwargs):
	"""
	Create a Lead and User for website signup only if not created earlier.
	- If User already exists: return error (already registered).
	- If Lead exists but User does not: create only User.
	- If neither exists: create Lead then User.
	Required: full_name, email, password.
	"""
	try:
		data = kwargs or {}
		required = ["full_name", "email", "password"]
		for field in required:
			if not data.get(field):
				return {"success": False, "error": f"{field.replace('_', ' ').title()} is required"}

		email = data.get("email", "").strip().lower()
		if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
			return {"success": False, "error": "Invalid email format"}

		password = data.get("password", "")
		if len(password) < 6:
			return {"success": False, "error": "Password must be at least 6 characters long"}

		if frappe.db.exists("User", email):
			return {"success": False, "error": "An account with this email already exists. Please sign in."}

		lead_name = data.get("full_name", "").strip()
		phone = (data.get("phone") or "").strip()
		company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
		lead_doc = None

		# Create Lead only if not created earlier (no Lead with this email)
		if not frappe.db.exists("Lead", {"email_id": email}):
			lead_doc = frappe.get_doc({
				"doctype": "Lead",
				"lead_name": lead_name,
				"email_id": email,
				"mobile_no": phone,
				"phone": phone,
				"status": "Lead",
				"territory": "All Territories",
				"company": company,
			})
			lead_doc.insert(ignore_permissions=True)

		name_parts = lead_name.split()
		first_name = name_parts[0] if name_parts else "User"
		last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

		user_doc = frappe.get_doc({
			"doctype": "User",
			"email": email,
			"first_name": first_name,
			"last_name": last_name,
			"enabled": 1,
			"user_type": "Website User",
			"send_welcome_email": 0,
			"mobile_no": phone,
			"new_password": password,
		})
		user_doc.insert(ignore_permissions=True)
		try:
			user_doc.add_roles("Customer")
		except Exception:
			pass
		if lead_doc:
			try:
				lead_doc.add_comment("Comment", f"User account created: {email}")
			except Exception:
				pass

		frappe.db.commit()
		lead_info = None
		if lead_doc:
			lead_info = {"name": lead_doc.name, "lead_name": lead_doc.lead_name, "email": lead_doc.email_id, "phone": lead_doc.mobile_no, "status": lead_doc.status}
		return {
			"success": True,
			"message": "Account created successfully",
			"lead": lead_info,
		}
	except frappe.ValidationError as e:
		frappe.db.rollback()
		return {"success": False, "error": str(e)}
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Signup API")
		return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Forgot password – send reset link email
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def forgot_password(email):
	"""Send password reset email with link to /pcds#/reset-password?key=..."""
	try:
		if not email:
			return {"success": False, "error": "Email is required"}
		email = email.strip().lower()
		if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
			return {"success": False, "error": "Invalid email format"}

		if not frappe.db.exists("User", email):
			return {"success": True, "message": "If this email is registered, you will receive a password reset link shortly."}

		user = frappe.get_doc("User", email)
		if not user.enabled:
			return {"success": False, "error": "Your account has been disabled. Please contact support."}

		reset_key = frappe.utils.random_string(32)
		user.reset_password_key = reset_key
		user.last_reset_password_key_generated_on = frappe.utils.now_datetime()
		user.save(ignore_permissions=True)
		frappe.db.commit()

		base_url = (frappe.local.conf.get("base_url") or "http://127.0.0.1:8007").rstrip("/")
		reset_link = f"{base_url}/pcds#/reset-password?key={reset_key}"

		subject = "Password Reset - Perfection Care Disability Services"
		message = f"""
		<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
			<h2 style="color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px;">Password Reset Request</h2>
			<p>Hello {user.first_name or 'User'},</p>
			<p>We received a request to reset your password for your Perfection Care account.</p>
			<p>Click the link below to reset your password:</p>
			<p><a href="{reset_link}" style="background-color: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a></p>
			<p style="word-break: break-all; background: #f5f5f5; padding: 10px; color: #666;">{reset_link}</p>
			<p style="color: #999; font-size: 12px;">If you did not request this, please ignore this email. This link will expire in 24 hours.</p>
		</div>
		"""
		frappe.sendmail(recipients=[email], subject=subject, message=message, delayed=False)
		return {"success": True, "message": "Password reset link has been sent to your email. Please check your inbox."}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Forgot Password API")
		return {"success": True, "message": "If this email is registered, you will receive a password reset link shortly."}


# ---------------------------------------------------------------------------
# Reset password – key + new password
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def reset_password(key, new_password):
	"""Reset user password using the key from the email link."""
	if not key or not new_password:
		return {"success": False, "error": "Key and new password are required"}
	if len(new_password) < 6:
		return {"success": False, "error": "Password must be at least 6 characters long"}

	user = frappe.db.get_value(
		"User",
		{"reset_password_key": key},
		["name"],
		as_dict=True,
	)
	if not user:
		return {"success": False, "error": "Invalid or expired reset link"}

	try:
		from frappe.utils.password import update_password
		update_password(user.name, new_password)
		frappe.db.set_value("User", user.name, "reset_password_key", None)
		frappe.db.commit()
		return {"success": True, "message": "Password has been reset successfully"}
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Reset Password API")
		return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Contact us – create Lead from enquiry form
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def submit_contact_enquiry(**kwargs):
	"""
	Create a Lead from the public contact form.

	Expected kwargs:
	- first_name (required)
	- middle_name (optional)
	- last_name (required)
	- full_name (optional; will be derived if missing)
	- email (required)
	- mobile (required)
	- country (required)
	- message (required)
	"""
	try:
		data = kwargs or {}

		required_fields = ["first_name", "last_name", "email", "mobile", "country", "message"]
		for field in required_fields:
			if not (data.get(field) or "").strip():
				return {"success": False, "error": f"{field.replace('_', ' ').title()} is required"}

		first_name = (data.get("first_name") or "").strip()
		middle_name = (data.get("middle_name") or "").strip()
		last_name = (data.get("last_name") or "").strip()
		full_name = (data.get("full_name") or "").strip() or " ".join(
			[x for x in [first_name, middle_name, last_name] if x]
		)
		email = (data.get("email") or "").strip().lower()
		mobile = (data.get("mobile") or "").strip()
		country = (data.get("country") or "").strip()
		message = (data.get("message") or "").strip()

		if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
			return {"success": False, "error": "Invalid email format"}

		frappe.set_user("Guest")
		frappe.local.flags.ignore_permissions = True

		company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
			"Global Defaults", "default_company"
		)

		lead_doc = frappe.get_doc(
			{
				"doctype": "Lead",
				"lead_name": full_name or first_name or "Website Enquiry",
				"first_name": first_name or None,
				"last_name": last_name or None,
				"email_id": email,
				"mobile_no": mobile,
				"phone": mobile,
				"status": "Lead",
				"territory": "All Territories",
				"company": company,
				"country": country
			}
		)
		lead_doc.insert(ignore_permissions=True)
		frappe.db.commit()

		return {
			"success": True,
			"message": "Thank you for your enquiry. Our team will contact you shortly.",
			"lead_name": lead_doc.name,
		}
	except DuplicateEntryError:
		# Specific, user-friendly message when a Lead with this email already exists
		frappe.db.rollback()
		return {
			"success": False,
			"error": "An enquiry with this email already exists. Please use a different email or wait for our team to respond.",
		}
	except Exception as e:
		frappe.db.rollback()
		# Log full traceback on the server, but return a short, safe message to the frontend
		frappe.log_error(frappe.get_traceback(), "Submit Contact Enquiry API")
		return {
			"success": False,
			"error": "Something went wrong while submitting your enquiry. Please try again later.",
		}

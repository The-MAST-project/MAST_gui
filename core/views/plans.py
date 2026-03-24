import json
import logging
import sys
import os

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse

logger = logging.getLogger(__name__)


@login_required
def plans_new(request):
	"""
	Renders the new plan form page. The page fetches a plan template from
	GET /plans/new on the control backend (which allocates a ULID and returns
	spec defaults), then lets the user fill in the form and POST to /plans/submit.
	"""
	from django.http import HttpResponseForbidden
	user = request.user
	can_submit = user.has_perm('accounts.can_submit_plans') or user.is_superuser
	if not can_submit:
		return HttpResponseForbidden()

	# Build field metadata for the new-plan form from the Plan model's json_schema_extra.
	try:
		common_path = os.environ.get('MAST_COMMON_PATH', os.path.join(os.path.dirname(__file__), '../../common'))
		if common_path not in sys.path:
			sys.path.insert(0, common_path)
		from common.models.plans import Plan
		from units.config_utils import extract_field_metadata_recursive
		field_meta = extract_field_metadata_recursive(Plan)
		field_meta_json = json.dumps(field_meta)
	except Exception as e:
		logger.exception(f"plans_new: failed to build field metadata: {e}")
		field_meta_json = '{}'

	return render(request, "plans/plan_new.html", {
		"SCRIPT_PREFIX": request.META.get("SCRIPT_NAME", ""),
		"field_meta_json": field_meta_json,
	})


@login_required
def plans_index(request):
	"""
	Renders the Plans page. Data is populated client-side via ControlApi('/plans/get').
	Two capability flags are passed to the template:
	  - canManagePlans: admins — can execute, postpone, cancel, delete, revive plans
	  - canSubmitPlans: scientists — can submit new observation plans
	"""
	from accounts.models import User as MASTUser

	user = request.user
	can_manage = user.has_perm('accounts.can_manage_plans') or user.is_superuser
	can_submit = user.has_perm('accounts.can_submit_plans') or user.is_superuser
	script_prefix = request.META.get("SCRIPT_NAME", "")

	try:
		common_path = os.environ.get('MAST_COMMON_PATH', os.path.join(os.path.dirname(__file__), '../../common'))
		if common_path not in sys.path:
			sys.path.insert(0, common_path)
		from common.models.plans import Plan
		from units.config_utils import extract_field_metadata_recursive
		field_meta_json = json.dumps(extract_field_metadata_recursive(Plan))
	except Exception as e:
		logger.exception(f"plans_index: failed to build field metadata: {e}")
		field_meta_json = '{}'

	owners = {
		str(u.uid): {
			'name': u.full_name or u.username,
			'url': reverse('accounts:user_profile', args=[u.uid]),
		}
		for u in MASTUser.objects.filter(is_active=True)
	}

	return render(
		request,
		"plans/index.html",
		{
			"canManagePlans": can_manage,
			"canSubmitPlans": can_submit,
			"SCRIPT_PREFIX": script_prefix,
			"field_meta_json": field_meta_json,
			"owners_json": json.dumps(owners),
		}
	)

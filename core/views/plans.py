import json
import logging
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
		from MAST_common.models.plans import Plan
		from units.config_utils import extract_field_metadata_recursive
		field_meta = extract_field_metadata_recursive(Plan)
		field_meta_json = json.dumps(field_meta)
	except Exception as e:
		logger.exception(f"plans_new: failed to build field metadata: {e}")
		field_meta_json = '{}'

	try:
		from MAST_common.config import Config
		filter_options = Config().get_thar_filters()
	except Exception as e:
		logger.warning(f"plans_new: could not fetch ThAr filter options: {e}")
		filter_options = []

	from accounts.models import User as MASTUser
	from django.urls import reverse
	owners = {
		str(u.uid): {
			'name': u.full_name or u.username,
			'url': reverse('accounts:user_profile', args=[u.uid]),
		}
		for u in MASTUser.objects.filter(is_active=True)
	}

	return render(request, "plans/plan_new.html", {
		"SCRIPT_PREFIX": request.META.get("SCRIPT_NAME", ""),
		"field_meta_json": field_meta_json,
		"filter_options_json": json.dumps(filter_options),
		"current_user_uid": str(user.uid),
		"owners_json": json.dumps(owners),
	})


@login_required
def plans_edit(request, ulid):
	from django.http import HttpResponseForbidden
	user = request.user
	can_submit = user.has_perm('accounts.can_submit_plans') or user.is_superuser
	if not can_submit:
		return HttpResponseForbidden()

	try:
		from MAST_common.models.plans import Plan
		from units.config_utils import extract_field_metadata_recursive
		field_meta_json = json.dumps(extract_field_metadata_recursive(Plan))
	except Exception as e:
		logger.exception(f"plans_edit: failed to build field metadata: {e}")
		field_meta_json = '{}'

	try:
		from MAST_common.config import Config
		filter_options = Config().get_thar_filters()
	except Exception as e:
		logger.warning(f"plans_edit: could not fetch ThAr filter options: {e}")
		filter_options = []

	from accounts.models import User as MASTUser
	from django.urls import reverse
	owners = {
		str(u.uid): {
			'name': u.full_name or u.username,
			'url': reverse('accounts:user_profile', args=[u.uid]),
		}
		for u in MASTUser.objects.filter(is_active=True)
	}

	return render(request, "plans/plan_new.html", {
		"SCRIPT_PREFIX": request.META.get("SCRIPT_NAME", ""),
		"field_meta_json": field_meta_json,
		"filter_options_json": json.dumps(filter_options),
		"current_user_uid": str(user.uid),
		"owners_json": json.dumps(owners),
		"edit_ulid": ulid,
	})


@login_required
def plans_index(request):
	"""
	Renders the Plans page. Data is populated client-side via ControlApi('/plans/get').
	Three capability flags are passed to the template:
	  - canManagePlans:  can postpone, cancel, delete, revive plans
	  - canSubmitPlans:  can submit new observation plans
	  - canExecutePlans: can manually execute a single plan (dev/operator only)
	"""
	from accounts.models import User as MASTUser

	user = request.user
	can_manage  = user.has_perm('accounts.can_manage_plans')  or user.is_superuser
	can_submit  = user.has_perm('accounts.can_submit_plans')  or user.is_superuser
	can_execute = user.has_perm('accounts.can_execute_plans') or user.is_superuser
	script_prefix = request.META.get("SCRIPT_NAME", "")

	try:
		from MAST_common.models.plans import Plan
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

	scraping_results_json = '{}'
	try:
		sr_path = os.path.join(os.path.dirname(__file__), '../../static/plan-files/scraping_results.json')
		sr_path = os.path.realpath(sr_path)
		if os.path.exists(sr_path):
			with open(sr_path) as f:
				scraping_results_json = f.read()
			logger.info(f"plans_index: loaded scraping_results from {sr_path} ({len(scraping_results_json)} bytes)")
		else:
			logger.warning(f"plans_index: scraping_results not found at {sr_path}")
	except Exception as e:
		logger.warning(f"plans_index: could not load scraping_results: {e}")

	tab_defs = [
		('submitted', 'Submitted', False),
		('pending',   'Pending',   True),
		('completed', 'Completed', False),
		('postponed', 'Postponed', False),
		('expired',   'Expired',   False),
		('failed',    'Failed',    False),
		('canceled',  'Canceled',  False),
		('deleted',   'Deleted',   False),
	]

	return render(
		request,
		"plans/index.html",
		{
			"canManagePlans":  can_manage,
			"canSubmitPlans":  can_submit,
			"canExecutePlans": can_execute,
			"tab_defs":        tab_defs,
			"SCRIPT_PREFIX": script_prefix,
			"field_meta_json": field_meta_json,
			"owners_json": json.dumps(owners),
			"current_user_uid": str(user.uid),
		"scraping_results_json": scraping_results_json,
		}
	)

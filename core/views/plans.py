from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def plans_index(request):
	"""
	Renders the Plans page. Data is populated client-side via ControlApi('/plans/get').
	Two capability flags are passed to the template:
	  - canManagePlans: admins — can execute, postpone, cancel, delete, revive plans
	  - canSubmitPlans: scientists — can submit new observation plans
	"""
	user = request.user
	can_manage = user.has_perm('accounts.can_manage_plans') or user.is_superuser
	can_submit = user.has_perm('accounts.can_submit_plans') or user.is_superuser
	script_prefix = request.META.get("SCRIPT_NAME", "")
	return render(
		request,
		"plans/index.html",
		{
			"canManagePlans": can_manage,
			"canSubmitPlans": can_submit,
			"SCRIPT_PREFIX": script_prefix,
		}
	)

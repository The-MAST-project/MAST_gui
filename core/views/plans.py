from django.shortcuts import render

def plans_index(request):
	"""
	Simple view that renders the Plans page. The page is populated via client-side
	ControlApi('/plans/get'). We provide a boolean 'canManagePlans' used to enable/disable
	buttons in the template — replace with your actual capability check as needed.
	"""
	# Replace this with your real capability check if available (groups/capabilities).
	can_manage = False
	try:
		can_manage = request.user.is_staff or request.user.is_superuser
	except Exception:
		can_manage = False
	script_prefix = request.META.get("SCRIPT_NAME", "")
	return render(
		request,
		"plans/index.html",
		{
			"canManagePlans": can_manage,
			"SCRIPT_PREFIX": script_prefix,
		}
	)

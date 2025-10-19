from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import CustomUser

@login_required
@csrf_exempt
def generate_referral_code_view(request):
    """Generate referral code for the current user if they don't have one"""
    if request.method == 'POST':
        user = request.user
        if user.user_type == 'vendor':
            if not user.referral_code:
                referral_code = user.generate_referral_code()
                return JsonResponse({
                    'success': True,
                    'referral_code': referral_code,
                    'message': 'Referral code generated successfully'
                })
            else:
                return JsonResponse({
                    'success': True,
                    'referral_code': user.referral_code,
                    'message': 'Referral code already exists'
                })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Only vendors can have referral codes'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})
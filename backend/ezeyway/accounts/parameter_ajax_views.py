from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Category, SubCategory
from .parameter_models import CategoryParameter, SubCategoryParameter

@login_required
def get_category_parameters(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    target_id = request.GET.get('target_id')
    target_type = request.GET.get('target_type')
    
    if not target_id or not target_type:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    try:
        if target_type == 'category':
            parameters = CategoryParameter.objects.filter(category_id=target_id, is_active=True).order_by('display_order', 'name')
        elif target_type == 'subcategory':
            parameters = SubCategoryParameter.objects.filter(subcategory_id=target_id, is_active=True).order_by('display_order', 'name')
        else:
            return JsonResponse({'error': 'Invalid target type'}, status=400)
        
        params_data = []
        for param in parameters:
            params_data.append({
                'id': param.id,
                'name': param.name,
                'label': param.label,
                'field_type': param.field_type,
                'is_required': param.is_required,
                'options': param.options,
                'placeholder': param.placeholder,
                'description': param.description,
                'display_order': param.display_order
            })
        
        return JsonResponse({'parameters': params_data})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def add_category_parameter(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        target_id = request.POST.get('target_id')
        target_type = request.POST.get('target_type')
        param_name = request.POST.get('param_name')
        param_label = request.POST.get('param_label')
        param_type = request.POST.get('param_type')
        param_placeholder = request.POST.get('param_placeholder')
        param_order = request.POST.get('param_order', 0)
        param_required = request.POST.get('param_required') == 'on'
        param_options = request.POST.get('param_options')
        param_min = request.POST.get('param_min')
        param_max = request.POST.get('param_max')
        param_step = request.POST.get('param_step')
        
        if not all([target_id, target_type, param_name, param_label, param_type]):
            return JsonResponse({'error': 'All required fields must be filled'}, status=400)
        
        # Parse options if provided
        options = []
        if param_options:
            try:
                options = json.loads(param_options)
            except json.JSONDecodeError:
                options = [opt.strip() for opt in param_options.split('\n') if opt.strip()]
        
        if target_type == 'category':
            category = Category.objects.get(id=target_id)
            CategoryParameter.objects.create(
                category=category,
                name=param_name,
                label=param_label,
                field_type=param_type,
                is_required=param_required,
                options=options,
                placeholder=param_placeholder,
                display_order=int(param_order),
                min_value=float(param_min) if param_min else None,
                max_value=float(param_max) if param_max else None,
                step=float(param_step) if param_step else None
            )
        elif target_type == 'subcategory':
            subcategory = SubCategory.objects.get(id=target_id)
            SubCategoryParameter.objects.create(
                subcategory=subcategory,
                name=param_name,
                label=param_label,
                field_type=param_type,
                is_required=param_required,
                options=options,
                placeholder=param_placeholder,
                display_order=int(param_order),
                min_value=float(param_min) if param_min else None,
                max_value=float(param_max) if param_max else None,
                step=float(param_step) if param_step else None
            )
        else:
            return JsonResponse({'error': 'Invalid target type'}, status=400)
        
        return JsonResponse({'success': True, 'message': 'Parameter added successfully'})
    
    except (Category.DoesNotExist, SubCategory.DoesNotExist):
        return JsonResponse({'error': 'Target not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_parameters_public(request):
    """Public endpoint for vendors to get category/subcategory parameters"""
    target_id = request.GET.get('target_id')
    target_type = request.GET.get('target_type')
    
    if not target_id or not target_type:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    try:
        if target_type == 'category':
            parameters = CategoryParameter.objects.filter(category_id=target_id, is_active=True).order_by('display_order', 'name')
        elif target_type == 'subcategory':
            parameters = SubCategoryParameter.objects.filter(subcategory_id=target_id, is_active=True).order_by('display_order', 'name')
        else:
            return JsonResponse({'error': 'Invalid target type'}, status=400)
        
        params_data = []
        for param in parameters:
            params_data.append({
                'id': param.id,
                'name': param.name,
                'label': param.label,
                'field_type': param.field_type,
                'is_required': param.is_required,
                'options': param.options,
                'placeholder': param.placeholder,
                'description': param.description,
                'display_order': param.display_order
            })
        
        return JsonResponse({'parameters': params_data})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def delete_category_parameter(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        data = json.loads(request.body)
        parameter_id = data.get('parameter_id')
        target_type = data.get('target_type')
        
        if not parameter_id or not target_type:
            return JsonResponse({'error': 'Missing parameters'}, status=400)
        
        if target_type == 'category':
            parameter = CategoryParameter.objects.get(id=parameter_id)
        elif target_type == 'subcategory':
            parameter = SubCategoryParameter.objects.get(id=parameter_id)
        else:
            return JsonResponse({'error': 'Invalid target type'}, status=400)
        
        parameter.delete()
        return JsonResponse({'success': True, 'message': 'Parameter deleted successfully'})
    
    except (CategoryParameter.DoesNotExist, SubCategoryParameter.DoesNotExist):
        return JsonResponse({'error': 'Parameter not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
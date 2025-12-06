"""
Admin mixins for enhanced functionality.
"""

import csv
import json
from django.http import HttpResponse
from django.contrib import admin
from datetime import datetime


class ExportMixin:
    """
    Mixin to add CSV and JSON export functionality to Django admin.
    """
    
    def export_as_csv(self, request, queryset):
        """
        Export selected items as CSV.
        """
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={meta.verbose_name_plural}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        writer = csv.writer(response)
        writer.writerow(field_names)
        
        for obj in queryset:
            row = []
            for field in field_names:
                value = getattr(obj, field)
                if callable(value):
                    value = value()
                row.append(str(value))
            writer.writerow(row)
        
        return response
    
    export_as_csv.short_description = "Export selected as CSV"
    
    def export_as_json(self, request, queryset):
        """
        Export selected items as JSON.
        """
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]
        
        data = []
        for obj in queryset:
            item = {}
            for field in field_names:
                value = getattr(obj, field)
                if callable(value):
                    value = value()
                # Convert to JSON-serializable format
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                elif value is None:
                    value = None
                else:
                    value = str(value)
                item[field] = value
            data.append(item)
        
        response = HttpResponse(content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename={meta.verbose_name_plural}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        response.write(json.dumps(data, indent=2))
        
        return response
    
    export_as_json.short_description = "Export selected as JSON"


class AdminActionsMixin:
    """
    Common admin actions for models.
    """
    
    def activate_selected(self, request, queryset):
        """Activate selected items."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} items activated successfully.')
    
    activate_selected.short_description = "Activate selected items"
    
    def deactivate_selected(self, request, queryset):
        """Deactivate selected items."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} items deactivated successfully.')
    
    deactivate_selected.short_description = "Deactivate selected items"

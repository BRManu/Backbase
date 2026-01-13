from django.contrib import admin
from django.urls import path, reverse

class MyCurrencyAdminSite(admin.AdminSite):
    site_header = "MyCurrency Administration"
    site_title = "MyCurrency Admin Portal"
    index_title = "Welcome to MyCurrency Researcher Portal"

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)
        
        for app in app_list:
            if app['app_label'] == 'MyCurrency':
                # Map the manual converter URL
                converter_url = reverse('admin:currency-converter')
                
                # Add a "fake" model entry to the sidebar
                app['models'].append({
                    'name': 'Currency Converter',
                    'object_name': 'currency_converter',
                    'admin_url': converter_url,
                    'view_only': True,
                })
        return app_list

# Instantiate the custom admin site
my_currency_admin_site = MyCurrencyAdminSite(name='admin')

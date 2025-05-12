from django.apps import AppConfig

class GroupforumConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Groupforum'
    
    def ready(self):
        import Groupforum.signals  # Activate signals
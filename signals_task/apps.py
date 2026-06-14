from django.apps import AppConfig


class SignalsTaskConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'signals_task'

    def ready(self):
        import signals_task.signals
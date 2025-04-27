from django.core.management.base import BaseCommand
from chatbot.llm_integration import initialize_knowledge_base

class Command(BaseCommand):
    help = 'Reload the chatbot knowledge base'

    def handle(self, *args, **options):
        self.stdout.write("Reloading knowledge base...")
        initialize_knowledge_base()
        self.stdout.write("Knowledge base reloaded successfully!")
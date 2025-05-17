from django.core.management.base import BaseCommand
from pathlib import Path
from chatbot.knowledge_base.processor import KnowledgeBaseProcessor
from chatbot.llm_integration import LLMIntegration
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Initialize the knowledge base with documents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--documents-dir',
            type=str,
            help='Directory containing documents to process',
            default='documents'
        )

    def handle(self, *args, **options):
        documents_dir = Path(options['documents_dir'])
        
        if not documents_dir.exists():
            self.stdout.write(
                self.style.WARNING(f'Documents directory {documents_dir} does not exist')
            )
            return

        # Initialize processors
        kb_processor = KnowledgeBaseProcessor()
        llm = LLMIntegration()

        # Process each document
        for file_path in documents_dir.glob('**/*'):
            if file_path.is_file():
                try:
                    self.stdout.write(f'Processing {file_path}...')
                    result = llm.add_to_knowledge_base(str(file_path))
                    
                    if result['status'] == 'success':
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Successfully processed {file_path} '
                                f'({result["chunks_added"]} chunks added)'
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Failed to process {file_path}: {result["error"]}'
                            )
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error processing {file_path}: {str(e)}')
                    )

        # Test the knowledge base
        self.stdout.write('\nTesting knowledge base...')
        test_queries = [
            "What is the main purpose of this system?",
            "How do I use the chatbot?",
            "What are the key features?"
        ]

        for query in test_queries:
            try:
                results = kb_processor.search(query)
                self.stdout.write(f'\nQuery: {query}')
                for i, result in enumerate(results, 1):
                    self.stdout.write(
                        f'Result {i} (Similarity: {result["similarity"]:.2f}):\n'
                        f'{result["text"][:200]}...\n'
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error testing query "{query}": {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS('\nKnowledge base initialization completed')
        ) 
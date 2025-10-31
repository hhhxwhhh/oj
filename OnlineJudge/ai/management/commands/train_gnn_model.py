import logging
from django.core.management.base import BaseCommand
from ai.service import KnowledgeGraphService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Train GNN model and generate knowledge point embeddings'

    def add_arguments(self, parser):
        parser.add_argument('--epochs', type=int, default=100, help='Number of training epochs')
        parser.add_argument('--lr', type=float, default=0.01, help='Learning rate')
        parser.add_argument('--hidden_dim', type=int, default=64, help='Hidden layer dimension')
        parser.add_argument('--model_type', type=str, default='gcn', help='Model type: gcn or gat')

    def handle(self, *args, **options):
        self.stdout.write('Training GNN model and generating knowledge point embeddings...')
        try:
            epochs = options['epochs']
            lr = options['lr']
            hidden_dim = options['hidden_dim']
            model_type = options['model_type']
            
            # 训练GNN模型
            model = KnowledgeGraphService.train_gnn_model(
                epochs=epochs, 
                lr=lr, 
                hidden_dim=hidden_dim, 
                model_type=model_type
            )
            
            if model:
                self.stdout.write(
                    self.style.SUCCESS('Successfully trained GNN model and generated embeddings')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('Failed to train GNN model or no data available')
                )
        except Exception as e:
            logger.error(f"Failed to train GNN model: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'Failed to train GNN model: {str(e)}')
            )
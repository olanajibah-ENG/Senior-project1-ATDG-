from abc import ABC, abstractmethod
from typing import Dict, Any

class ILanguageProcessorStrategy(ABC):
    """
    Base interface for language processing strategies.
    Each concrete processor must implement these methods.
    """

    @abstractmethod
    def parse_source_code(self, code_content: str) -> Dict[str, Any]:
        """
        Parses the source code and returns its AST structure.
        """
        pass

    @abstractmethod
    def extract_features(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts various features from the AST data.
        """
        pass

    @abstractmethod
    def extract_dependencies(self, ast_data: Dict[str, Any]) -> list[str]:
        """
        Extracts dependencies and builds a dependency graph from AST.
        """
        pass

    @abstractmethod
    def perform_semantic_analysis(self, ast_data: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs advanced semantic analysis.
        """
        pass

    @abstractmethod
    def generate_class_diagram_data(self, ast_data: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates data suitable for class diagram visualization.
        """
        pass
    
    @abstractmethod
    def generate_dependency_graph_data(self, ast_data: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates data suitable for dependency graph visualization.
        """
        pass
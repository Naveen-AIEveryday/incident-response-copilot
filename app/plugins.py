import json

from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function

from app.knowledge_base import KnowledgeBase


class KnowledgePlugin:
    def __init__(self, knowledge_base: KnowledgeBase):
        self.knowledge_base = knowledge_base

    @kernel_function(
        name="search_incident_knowledge",
        description=(
            "Search runbooks and historical incidents "
            "for evidence related to an IT incident."
        ),
    )
    def search_incident_knowledge(self, query: str) -> str:
        matches = self.knowledge_base.search(query, limit=3)
        return json.dumps(matches, indent=2)


def create_kernel(knowledge_base: KnowledgeBase) -> Kernel:
    kernel = Kernel()

    plugin = KnowledgePlugin(knowledge_base)

    kernel.add_plugin(
        plugin=plugin,
        plugin_name="knowledge",
    )

    return kernel
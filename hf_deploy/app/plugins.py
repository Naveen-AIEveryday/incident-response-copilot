import json

from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function

from app.knowledge_base import KnowledgeBase


class KnowledgePlugin:
    def __init__(self, knowledge_base: KnowledgeBase):
        self.knowledge_base = knowledge_base

    @kernel_function(
        name="search_knowledge",
        description=(
            "Search incident runbooks and historical incidents."
        ),
    )
    def search_knowledge(self, query: str) -> str:
        matches = self.knowledge_base.search(query)
        return json.dumps(matches, indent=2)


def create_kernel(
    knowledge_base: KnowledgeBase,
) -> tuple[Kernel, KnowledgePlugin]:
    kernel = Kernel()
    plugin = KnowledgePlugin(knowledge_base)

    kernel.add_plugin(
        plugin=plugin,
        plugin_name="knowledge",
    )

    return kernel, plugin
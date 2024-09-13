""" 
JSONScraperMultiGraph Module
"""

from copy import deepcopy
from typing import List, Optional
from pydantic import BaseModel
from .base_graph import BaseGraph
from .abstract_graph import AbstractGraph
from .json_scraper_graph import JSONScraperGraph
from ..nodes import (
    GraphIteratorNode,
    MergeAnswersNode
)
from ..utils.copy import safe_deepcopy

class JSONScraperMultiGraph(AbstractGraph):
    """ 
    JSONScraperMultiGraph is a scraping pipeline that scrapes a 
    list of URLs and generates answers to a given prompt.
    It only requires a user prompt and a list of URLs.

    Attributes:
        prompt (str): The user prompt to search the internet.
        llm_model (dict): The configuration for the language model.
        embedder_model (dict): The configuration for the embedder model.
        headless (bool): A flag to run the browser in headless mode.
        verbose (bool): A flag to display the execution information.
        model_token (int): The token limit for the language model.

    Args:
        prompt (str): The user prompt to search the internet.
        source (List[str]): The source of the graph.
        config (dict): Configuration parameters for the graph.
        schema (Optional[BaseModel]): The schema for the graph output.

    Example:
        >>> search_graph = MultipleSearchGraph(
        ...     "What is Chioggia famous for?",
        ...     {"llm": {"model": "openai/gpt-3.5-turbo"}}
        ... )
        >>> result = search_graph.run()
    """

    def __init__(self, prompt: str, source: List[str], 
                 config: dict, schema: Optional[BaseModel] = None):

        self.max_results = config.get("max_results", 3)

        self.copy_config = safe_deepcopy(config)

        self.copy_schema = deepcopy(schema)

        super().__init__(prompt, config, source, schema)

    def _create_graph(self) -> BaseGraph:
        """
        Creates the graph of nodes representing the workflow for web scraping and searching.

        Returns:
            BaseGraph: A graph instance representing the web scraping and searching workflow.
        """

        # smart_scraper_instance = JSONScraperGraph(
        #     prompt="",
        #     source="",
        #     config=self.copy_config,
        #     schema=self.copy_schema
        # )

        graph_iterator_node = GraphIteratorNode(
            input="user_prompt & jsons",
            output=["results"],
            node_config={
                "graph_instance": JSONScraperGraph,
                "scraper_config": self.copy_config,
            },
            schema=self.copy_schema
        )

        merge_answers_node = MergeAnswersNode(
            input="user_prompt & results",
            output=["answer"],
            node_config={
                "llm_model": self.llm_model,
                "schema": self.copy_schema
            }
        )

        return BaseGraph(
            nodes=[
                graph_iterator_node,
                merge_answers_node,
            ],
            edges=[
                (graph_iterator_node, merge_answers_node),
            ],
            entry_point=graph_iterator_node,
            graph_name=self.__class__.__name__
        )

    def run(self) -> str:
        """
        Executes the web scraping and searching process.

        Returns:
            str: The answer to the prompt.
        """
        inputs = {"user_prompt": self.prompt, "jsons": self.source}
        self.final_state, self.execution_info = self.graph.execute(inputs)

        return self.final_state.get("answer", "No answer found.")

import requests
from os.path import join

from app.dante.tree_node import DanteTreeNode

DANTE_URL = 'https://api.dante.gbv.de'
VOCABULARY_PUBLISHER = 'Archäologisches Museum Hamburg'


class DanteVocabulary(DanteTreeNode):
    @classmethod
    def from_uri(cls, uri):
        data = requests.get(join(DANTE_URL, 'data'), params={'uri': uri}).json()[0]
        self = cls(**data)
        self.initialize_top()
        return self

    def initialize_top(self):
        top_url = join(DANTE_URL, 'voc', self.id, 'top')
        self.depth = 0
        top_nodes = requests.get(top_url).json()
        self.children = [DanteTreeNode(dig=True, dig_deeper=True, item_cache=self.item_cache, level=1, **top_node) for top_node in top_nodes]
        for child in self.children:
            self.item_cache[child.uri] = child
        self.checked_for_children = True

    def get_field_list(self, max_depth=None):
        return {
            'description': self.prefLabel,
            'createdBy': VOCABULARY_PUBLISHER,
            'creationDate': self.created,
            'values': self.get_values(max_depth)
        }

    def get_values(self, max_depth):
        items = list(self.flatten(max_depth=max_depth))
        items.remove(self)
        result = {}
        for item in items:
            result[item.id] = item.get_field_value()
        return result

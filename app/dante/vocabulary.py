import requests
from os.path import join

from app import settings
from app.dante.tree_node import DanteTreeNode


class DanteVocabulary(DanteTreeNode):
    @classmethod
    def from_uri(cls, uri):
        data = requests.get(join(settings.Dante.HOST_URL, 'data'), params={ 'uri': uri, 'cache': 0 }).json()[0]
        self = cls(**data)
        self.__initialize_top()
        return self

    def get_field_list(self, max_depth=None):
        return {
            'description': self.prefLabel,
            'createdBy': settings.Dante.VOCABULARY_PUBLISHER,
            'creationDate': self.created,
            'values': self.__get_values(max_depth)
        }

    def __initialize_top(self):
        top_url = join(settings.Dante.HOST_URL, 'voc', self.id, 'top')
        self.depth = 0
        top_nodes = requests.get(top_url, params={ 'cache': 0 }).json()
        self.children = [DanteTreeNode(dig=True, dig_deeper=True, item_cache=self.item_cache, level=1, **top_node) for top_node in top_nodes]
        for child in self.children:
            self.item_cache[child.uri] = child
        self.checked_for_children = True

    def __get_values(self, max_depth):
        items = list(self.flatten(max_depth=max_depth))
        items.remove(self)
        result = {}
        for item in items:
            result[item.id] = item.get_field_value()
        return result

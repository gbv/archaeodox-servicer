import requests
from os.path import join

from app import settings


class DanteTreeNode:
    def __init__(self, uri="", prefLabel="", parentLabel=None, created="", item_cache={}, level=0, dig=False, dig_deeper=False, *args, **kwargs):
        self.uri = uri
        self.depth = level
        self.prefLabel = self.__add_parent_to_pref_label(prefLabel, parentLabel)
        self.parentLabel = parentLabel
        self.created = created
        self.__initialize_item_cache(item_cache)
        self.id = self.__get_id(uri)
        self.checked_for_children = False
        self.children = []
        if dig:
            self.__check_for_children(dig_deeper=dig_deeper)

    def get_field_value(self):
        return {
            'references': [self.uri],
            'label': self.prefLabel
        }

    def flatten(self, max_depth=None):
        nodes = self.item_cache.values()
        if max_depth is not None:
            nodes = filter(lambda n: n.depth <= max_depth, nodes)
        return nodes

    def __add_parent_to_pref_label(self, pref_label, parent_label):
        if parent_label:
            return { 'de': f"{parent_label['de']} / {pref_label['de']}" }
        else:
            return pref_label

    def __initialize_item_cache(self, item_cache):
        if item_cache:
            self.item_cache = item_cache
        else:
            self.item_cache = { self.uri: self }

    def __get_id(self, uri):
        parts = uri.split('/')
        parts = filter(lambda p: p != '', parts)
        return list(parts)[-1]

    def __check_for_children(self, dig_deeper=False):
        if not self.checked_for_children:
            descendants = requests.get(join(settings.Dante.HOST_URL, 'descendants'), params = { 'uri': self.uri, 'cache': 0 })
            for d in descendants.json():
                if d['uri'] in self.item_cache.keys():
                    child = self.item_cache[d['uri']]
                else: 
                    child = DanteTreeNode(parentLabel=self.prefLabel, dig=dig_deeper, dig_deeper=dig_deeper, item_cache=self.item_cache, level=self.depth+1, **d)
                    self.item_cache[child.uri] = child
                self.children.append(child)
            self.checked_for_children = True

import requests
from os.path import join

from app import settings


class DanteTreeNode:
    def __init__(self, uri="", prefLabel="", parentLabel=None, created="", item_cache={}, level=0, dig=False, dig_deeper=False, *args, **kwargs):
        print(uri)
        self.uri = uri
        self.depth = level
        if parentLabel:
            self.prefLabel = { 'de': f"{parentLabel['de']} / {prefLabel['de']}" }
        else:
            self.prefLabel = prefLabel
        self.parentLabel = parentLabel
        self.created = created
        if item_cache:
            self.item_cache = item_cache
        else:
            self.item_cache = {self.uri: self}
        def last_string(uri):
            parts = uri.split('/')
            parts = filter(lambda p: p != '', parts)
            return list(parts)[-1]
        self.id = last_string(uri)
        self.checked_for_children = False
        self.children = []
        if dig:
            self.check_for_children(dig_deeper=dig_deeper)
            

    def first_label(self):
        if self.prefLabel:
            label = list(self.prefLabel.items())[0][-1]
            label = label.replace('–', '-')
            label = label.replace('(', '')
            label = label.replace(')', '')
            return label

    def check_for_children(self, dig_deeper=False):
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
    
    @property
    def has_children(self):
        if not self.checked_for_children:
            self.check_for_children()
        return bool(len(self.children))
    
    
    def json(self, recursive=False):
        to_return = {'uri': self.uri,
                     'prefLabel': self.prefLabel,
                     'id': self.id,
                     'children': self.children}
        if recursive:
            self.checked_for_children = False
            self.check_for_children(True)
            to_return['children'] = [child.json(True) for child in self.children]
        return to_return

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

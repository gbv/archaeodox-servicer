import requests
import json
from os.path import join

DANTE_URL = 'https://api.dante.gbv.de'
VOCABULARY_PUBLISHER = 'Archäologisches Museum Hamburg'


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
            descendants = requests.get(join(DANTE_URL, 'descendants'), params = {'uri': self.uri})
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
    
    def get_mermaid(self, direction='TD', file_name=None, max_depth=None):
        mermaid = ['graph ' + direction]
        items = self.flatten(max_depth=max_depth)
        def get_text(item, mermaid):
            for child in item.children:
                mermaid.append(f'    {item.id}[{item.first_label()} {item.depth}] --> {child.id}[{child.first_label()} {child.depth}]')
        for item in items:
            get_text(item, mermaid)
        mermaid = '\n'.join(mermaid)
        if file_name:
            with open(file_name, 'w') as out_file:
                out_file.write(mermaid)
        return mermaid


if __name__ == '__main__':
    vocabulary = DanteVocabulary.from_uri('http://uri.gbv.de/terminology/amh_objektbezeichnung')
    field_list = vocabulary.get_field_list()
    with open('vocabulary.json', 'w') as out_file:
        json.dump(field_list, out_file, indent=2, ensure_ascii=False)
    
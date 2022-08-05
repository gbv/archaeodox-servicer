from pydoc_data.topics import topics
import requests
from os.path import join

DANTE_URL = 'https://api.dante.gbv.de'

casserolle = ['amh_causes_role']
real_unit = 'nld_areal_unit'


class DanteTreeNode:
    def __init__(self, uri="", prefLabel="", item_cache={}, level=0, dig=False, dig_deeper=False, *args, **kwargs):
        self.uri = uri
        self.depth = level
        self.prefLabel = prefLabel 
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
            # print(f'Node: {self.id}')
            for d in descendants.json():
                if d['uri'] in self.item_cache.keys():
                    child = self.item_cache[d['uri']]
                    # print('from cache: ' + child.id)
                else: 
                    child = DanteTreeNode(dig=dig_deeper, dig_deeper=dig_deeper, item_cache=self.item_cache, level=self.depth+1, **d)
                    self.item_cache[child.uri] = child
                    # print('added: ' + child.id)
                # print(f'child: {child.id}')
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

    def get_idai(self):
        tag = f'{str(self.prefLabel)} - {self.id}'
        return {tag: {'references': [self.uri],
                      'label': self.prefLabel,
                      'level': self.depth}}

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

    def get_idai_list(self, max_depth=None):
        items = list(self.flatten(max_depth=max_depth))
        items.remove(self)
        return [item.get_idai() for item in items]
    
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
    technology = DanteVocabulary.from_uri('http://uri.gbv.de/terminology/kuniweb_technik')
    technology.get_mermaid(file_name='technology.mmd')
    exit(0)
    import pickle
    
    def pickle_tree(voc_name):
        voc = DanteTreeNode.from_uri(f'http://uri.gbv.de/terminology/{voc_name}/')
        voc.initialize_top()
        with open(f'{voc_name}.pkl', 'wb') as out_file:
            pickle.dump(voc, out_file)
    # fieldified = fieldify_dante('http://api.dante.gbv.de', 'https://uri.gbv.de/terminology/kenom_material/')
    
    # fieldified = fieldify_dante('http://api.dante.gbv.de', "http://uri.gbv.de/terminology/amh_datierung/")
    
    vocs = ['prizepapers_journey_type',
            'lido_eventtype',
            'kuniweb_technik',
            'gender',
            'kenom_material',
            'amh_datierung'
            ]
    for voc in vocs:
        print(f"Pickling: {voc}")
        pickle_tree(voc)
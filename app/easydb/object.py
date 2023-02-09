class EdbObject:
    TAG_MODE_ADD = 'tag_add'
    TAG_MODE_REPLACE = 'tag_replace'
    TAG_MODE_REMOVE = 'tag_remove'
    TAG_MODE_REMOVEALL = 'tag_remove_all'
    

    def __init__(self, object_type, data, mask='_all_fields', tags=[], tag_mode=None) -> None:
        self.object_type = object_type
        self.data = data
        self.mask = mask
        self.tags = tags
        self.tag_mode = tag_mode

    def get_edb_format(self):
        wrapped = {self.object_type: self.data}
        wrapped['_mask'] = self.mask
        if self.tags:
            wrapped['_tags'] = [{'_id': tag} for tag in self.tags]
        if self.tag_mode:
            wrapped['_tags:group_mode'] = self.tag_mode
        return wrapped

    def set_tags(self, tags, tag_mode):
        self.tags = tags
        self.tag_mode = tag_mode

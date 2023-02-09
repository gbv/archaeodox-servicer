class CSV:
    @staticmethod
    def inflate(row):
        nested_keys = list(filter(lambda k: '.' in k, row.keys()))
        for key in nested_keys:
            dp.new(row, key, row[key], separator='.')
            row.pop(key)
        return row
    
    @staticmethod
    def remove_empties(row):
        sanitized = {}
        for key, value in row.items():
            if str(value).strip():
                sanitized[key] = value
        return sanitized
                
    @staticmethod
    def process(row):
        row = CSV.remove_empties(row)
        return CSV.inflate(row)

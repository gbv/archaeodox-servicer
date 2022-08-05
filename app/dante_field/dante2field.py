import argparse

from dante import DanteVocabulary, DANTE_URL
from couch import Client

def load_and_inject(uri, max_depth, client, database, path):
    dante_vocabulary = DanteVocabulary.from_uri(uri)
    patch = dante_vocabulary.get_idai_list(max_depth)

    client.inject_config(database, path, patch)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Load a vocabulary from Dante and inject it into the couch db behind an iDAI.field instance.")
    
    parser.add_argument('vocabulary_uri', help='URI of the required vocabulary.')
    parser.add_argument('host', help='Url of the couch db server incl. protocol and port.')
    parser.add_argument('database', help="Name of the targetet couch db.")
    parser.add_argument('path', help='path to the intended location of the vocabulary.')
    parser.add_argument('-u', '--user', help='The database user')
    parser.add_argument('-p', '--password', help='The d password.')
    parser.add_argument('-l', '--level', '--max_depth', help='Maximal depth of copying.')
    
    args = parser.parse_args()
    use_auth_from_env = (args.user is None and args.password is None)
    
    client = Client(args.host, args.user, args.password, use_auth_from_env)
    load_and_inject(args.vocabulary_uri, args.level, client, args.database, args.path)

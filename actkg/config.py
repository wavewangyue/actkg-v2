import sys
import logging
import jieba
import warnings
warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')
import json
import gensim

database_address = "http://10.1.1.28:7474"
server_RelationPredict_address = 'http://10.1.1.28:20001'
server_AnswerSelection_address = 'http://10.1.1.28:20002'
server_TripleExtraction_address = 'http://10.1.1.28:20004'
server_CountQA_address = 'http://10.1.1.28:20005'

resource_path = sys.path[0] + '/resource'

# init set
logging_format = '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s'
logging.basicConfig(filename=sys.path[0]+'/static/log/runlog.txt', level=logging.DEBUG, format=logging_format)
jieba.load_userdict(resource_path+'/jieba/dict.txt')

# load data
print ("Loading json:alias_keyid ......")
alias_keyid = json.load(open(resource_path+'/kg/alias_keyid.json'))
print ("Loading json:keyid_pop ......")
keyid_pop = json.load(open(resource_path+'/kg/keyid_popularity.json'))
print ("Loading json:category_attributes ......")
category_attributes = json.load(open(resource_path+'/kg/category_attributes.json'))
print ("Loading json:category_entitysamples ......")
category_entitysamples = json.load(open(resource_path+'/kg/category_entitysamples.json'))


# load model
print ("Loading model:word2vec ......")
w2v_model = gensim.models.KeyedVectors.load_word2vec_format(resource_path+'/word2vec/baike.vectors.bin', binary=True)

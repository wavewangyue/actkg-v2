#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
import logging
import os.path
import sys
import multiprocessing
 
from gensim.models import Word2Vec
from gensim.models.word2vec import LineSentence
 
if __name__ == '__main__':
    i_file = 'corpus.txt'
    m_file = 'yelp.model'
    v_file = 'yelp.vector.bin'
 
    program = os.path.basename(sys.argv[0])
    logger = logging.getLogger(program)
    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
    logging.root.setLevel(level=logging.INFO)
    logger.info("running %s" % ' '.join(sys.argv))
    
    model = Word2Vec(LineSentence(i_file), size=200, window=5, min_count=50,
            workers=multiprocessing.cpu_count())
 
    # trim unneeded model memory = use(much) less RAM
    #model.init_sims(replace=True)
    model.save(m_file)
    model.wv.save_word2vec_format(v_file, binary=True)
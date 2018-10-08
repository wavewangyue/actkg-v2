import gensim

model = gensim.models.KeyedVectors.load_word2vec_format('baike.vectors.bin', binary=True)
print model[u'中国']
print model.wv.most_similar(positive=[u'中国'])
print model.n_similarity([u'院校'], [u'学校'])
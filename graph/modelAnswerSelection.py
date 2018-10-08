# -*- coding: utf-8 -*-
import tensorflow as tf
from tensorflow.contrib import rnn
import tensorlayer as tl
import data
import jieba
import numpy as np
from pyltp import SentenceSplitter
import modelWord2vec
import actkg.Config as Config


class AnswerSelectionModel:
    def __init__(self, model_path=None, w2v_model=None):
        self.word2idx, self.idx2vec = self.get_word2vec(w2v_model)

        self.Ques = tf.placeholder(tf.int32, [None, None])
        self.Pos_Ans = tf.placeholder(tf.int32, [None, None])
        self.Neg_Ans = tf.placeholder(tf.int32, [None, None])
        self.Ques_seq_len = tf.placeholder(tf.int32, [None])
        self.Pos_Ans_len = tf.placeholder(tf.int32, [None])
        self.Neg_Ans_len = tf.placeholder(tf.int32, [None])
        self.keep_prob = tf.placeholder(tf.float32)
        self.hidden_size = 256

        self.Q_out = self.network(self.Ques, self.Ques_seq_len, reuse=False)
        self.PA_out = self.network(self.Pos_Ans, self.Pos_Ans_len, reuse=True)
        self.NA_out = self.network(self.Neg_Ans, self.Neg_Ans_len, reuse=True)

        self.Q_rep = self.max_pool(self.Q_out)
        self.PA_rep = self.max_pool(self.PA_out)
        self.NA_rep = self.max_pool(self.NA_out)

        self.Q_rep = tf.nn.l2_normalize(self.Q_rep, 1)
        self.PA_rep = tf.nn.l2_normalize(self.PA_rep, 1)
        self.NA_rep = tf.nn.l2_normalize(self.NA_rep, 1)

        self.simi_P = tf.reduce_sum(tf.multiply(self.Q_rep, self.PA_rep), 1)
        self.simi_N = tf.reduce_sum(tf.multiply(self.Q_rep, self.NA_rep), 1)
        self.loss = tf.reduce_mean(tf.maximum(
            0.00, 0.25 + self.simi_N - self.simi_P))
        self.optimizer = tf.train.AdamOptimizer(learning_rate=0.01)
        self.opt = self.optimizer.minimize(self.loss)

        self.predict_sess = None
        self.saver = tf.train.Saver()
        if model_path is not None:
            self.predict_sess = self.load_model(model_path)

    def get_word2vec(self, word2vec):
        idx2vec = []
        index2word = word2vec.index2word
        word2idx = {}
        for i in range(len(index2word)):
            word2idx[index2word[i]] = i
            idx2vec.append(word2vec[index2word[i]])
        idx2vec = np.array(idx2vec)
        return word2idx, idx2vec

    def network(self, sentence, length, reuse=False):
        with tf.variable_scope('LSTM', reuse=reuse) as scope:
            # embedding
            with tf.device('/cpu:0'):
                sen = tf.nn.embedding_lookup(params=self.idx2vec, ids=sentence)
            with tf.variable_scope('lstm_cell'):
                lstm_cell_fwd = rnn.LSTMCell(self.hidden_size, reuse=reuse)
                lstm_cell_bwd = rnn.LSTMCell(self.hidden_size, reuse=reuse)

                # dropout
                lstm_cell_fwd = rnn.DropoutWrapper(
                    lstm_cell_fwd, output_keep_prob=self.keep_prob)
                lstm_cell_bwd = rnn.DropoutWrapper(
                    lstm_cell_bwd, output_keep_prob=self.keep_prob)

                outputs, _ = tf.nn.bidirectional_dynamic_rnn(
                    cell_fw=lstm_cell_fwd,
                    cell_bw=lstm_cell_bwd,
                    inputs=sen,
                    sequence_length=length,
                    dtype=tf.float32)
                outputs = tf.concat(outputs, 2)
                return outputs

    def max_pool(self, inputs):
        rep = tf.reduce_max(inputs, 1)
      #  rep = tf.expand_dims(rep, -1)
      #  rep = tf.squeeze(tf.layers.max_pooling1d(rep, 4, 4))
        return rep

    def train(self, epoch, batch_size, continued=False):
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True
        batches = data.get_batches(
            batch_size=batch_size, word2idx=self.word2idx, idx2vec=self.idx2vec)
        with tf.Session(config=config) as sess:
            if continued:
                ckpt_path = tf.train.latest_checkpoint('./checkpoint')
                print 'restore %s' % (ckpt_path)
                self.saver.restore(sess, ckpt_path)
            else:
                init = tf.global_variables_initializer()
                sess.run(init)
            for i in range(epoch):
                print 'epoch %d...' % (i + 1)
                train_size = int(0.9 * len(batches))
                for batch_num in range(train_size):
                    sess.run(self.opt, feed_dict={
                        self.Ques: batches[batch_num]['quests'],
                        self.Ques_seq_len: batches[batch_num]['quest_len'],
                        self.Pos_Ans: batches[batch_num]['pos_ans'],
                        self.Pos_Ans_len: batches[batch_num]['pos_ans_len'],
                        self.Neg_Ans: batches[batch_num]['neg_ans'],
                        self.Neg_Ans_len: batches[batch_num]['neg_ans_len'],
                        self.keep_prob: 0.5
                    })
                train_error = self.evaluate(
                    sess, batches[0:train_size], batch_size)
                print 'train error %f' % (train_error)
                test_error = self.evaluate(
                    sess, batches[train_size:], batch_size)
                print 'test error %f' % (test_error)
                self.saver.save(sess, './checkpoint/new.ckpt', global_step=i)

    def evaluate(self, sess, batches, batch_size):
        cost = [sess.run(self.loss, feed_dict={
            self.Ques: batches[batch_num]['quests'],
            self.Ques_seq_len: batches[batch_num]['quest_len'],
            self.Pos_Ans: batches[batch_num]['pos_ans'],
            self.Pos_Ans_len: batches[batch_num]['pos_ans_len'],
            self.Neg_Ans: batches[batch_num]['neg_ans'],
            self.Neg_Ans_len: batches[batch_num]['neg_ans_len'],
            self.keep_prob: 1.0
        }) for batch_num in range(len(batches))]
        return sum(cost) / len(cost)

    def load_model(self, path):
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True
        sess = tf.Session(config=config)
        self.saver.restore(sess, path)
        return sess

    def sentence2input(self, sentence):
        cut_sentence = jieba.lcut(sentence, cut_all=False)
        r = []
        for word in cut_sentence:
            try:
                r.append(self.word2idx[word.decode('utf-8')])
            except:
                pass
        return r

    def predict(self, question, text):
        input_question = self.sentence2input(question)
        sentences = list(SentenceSplitter.split(text))
        input_answers_temp = [self.sentence2input(
            sentence) for sentence in sentences]
        input_answers_len = np.array([len(a) for a in input_answers_temp])
        input_answers = tl.prepro.pad_sequences(input_answers_temp)
        input_questions = tl.prepro.pad_sequences(
            [input_question] * len(sentences))
        input_question_len = np.array([len(q) for q in input_questions])
        simi_list = self.predict_sess.run(self.simi_P,
                                          feed_dict={
                                              self.Ques: input_questions,
                                              self.Ques_seq_len: input_question_len,
                                              self.Pos_Ans: input_answers,
                                              self.Pos_Ans_len: input_answers_len,
                                              self.keep_prob: 1.0})
#    for sen,simi in zip(sentences,simi_list):
#           print simi, sen
        simi_list = np.array(simi_list)
        return sentences[np.argmax(simi_list)], max(simi_list)


print ("Loading model:answer_selection ......")
model_word2vec = modelWord2vec.model
model = AnswerSelectionModel(Config.model_answer_selection_path, model_word2vec)


def select(question, description):
    result, point = model.predict(question, description)
    return result, point

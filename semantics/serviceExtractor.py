# -*- coding: utf-8 -*-
import types
import os
import json
import codecs
from pyltp import Segmentor, Postagger, Parser, SentenceSplitter
from actkg import Config

model_ltp_path = Config.model_ltp_path
resource_path = Config.resource_path

class LTP_Parser:
    def __init__(self, ltp_path=''):
        LTP_DATA_DIR = ltp_path  # ltp模型目录的路径

        # print('load cws model...')
        cws_model_path = os.path.join(LTP_DATA_DIR, 'cws.model')  # 分词模型路径，模型名称为`cws.model`
        segmentor = Segmentor()  # 初始化实例
        segmentor.load(cws_model_path)  # 加载模型

        # print('load pos model...')
        pos_model_path = os.path.join(LTP_DATA_DIR, 'pos.model')  # 词性标注模型路径，模型名称为`pos.model`
        postagger = Postagger()  # 初始化实例
        postagger.load(pos_model_path)  # 加载模型

        # print('load parser model...')
        par_model_path = os.path.join(LTP_DATA_DIR, 'parser.model')  # 依存句法分析模型路径，模型名称为`parser.model`
        parser = Parser()  # 初始化实例
        parser.load(par_model_path)  # 加载模型

        self.segmentor = segmentor
        self.postagger = postagger
        self.parser = parser

    def parse(self, statement):
        words = self.segmentor.segment(statement)  # 分词
        postags = self.postagger.postag(words)  # 词性标注
        arcs = self.parser.parse(words, postags)  # 句法分析
        for arc in arcs:
            arc.head -= 1
        return words, postags, arcs

print 'Loading model:ltp parser ......'
ltp_parser = LTP_Parser(ltp_path=model_ltp_path)


def rule_based_extraction(words, postags, arcs):
    # print("\t".join(words))
    # print("\t".join(postags))
    # print("\t".join("%d:%s" % (arc.head, arc.relation) for arc in arcs))
    full_entity_cache = {}

    # 通过完整实体索引得到实体完整名
    def findFullEntity(index):  # index = 5
        if index not in full_entity_cache:
            full_ent = []
            if not (((postags[index][0] == 'n') and (len(postags[index]) > 1)) or (
                postags[index] == 'j')):  # 如果这个词已经是一个命名实体，那么不再追溯他的修饰成分
                for ii in range(len(words)):
                    if (arcs[ii].relation == 'ATT') and (arcs[ii].head == index) and (
                        (postags[ii][0] == 'n') or (postags[ii] == 'j')):
                        full_ent.append(ii)
            full_ent.append(index)  # 3 4 5
            full_entity_cache[index] = full_ent

        if index not in full_entity_cache or len(full_entity_cache[index]) <= 1:
            full_ent = []
            if not (((postags[index][0] == 'nd') and (len(postags[index]) > 1)) or (
                postags[index] == 'j')):  # 如果这个词已经是一个命名实体，那么不再追溯他的修饰成分
                for ii in range(len(words)):
                    if (arcs[ii].relation == 'ATT') and (arcs[ii].head == index) and (
                        (postags[ii][0] == 'n') or (postags[ii] == 'j')):
                        full_ent.append(ii)

            full_ent.append(index)  # 3 4 5
            full_entity_cache[index] = full_ent

        if True:
            # if index not in full_entity_cache or len(full_entity_cache[index]) == 2:
            full_ent = []
            if not (((postags[index][0] == 'n') and (len(postags[index]) > 1)) or (
                postags[index] == 'j')):  # 如果这个词已经是一个命名实体，那么不再追溯他的修饰成分
                for ii in range(len(words)):
                    if (arcs[ii].relation == 'ATT') and (arcs[ii].head == index) and (
                        (postags[ii][0] == 'm') or (postags[ii] == 'j')):
                        full_ent.append(ii)
                    if (arcs[ii].relation == 'ATT') and (arcs[ii].head == index) and (
                        (postags[ii][0] == 'n') or (postags[ii] == 'j')):
                        full_ent.append(ii)
            full_ent.append(index)  # 3 4 5
            full_entity_cache[index] = full_ent

        return full_entity_cache[index]

    # 通过完整实体索引判断是否是命名实体
    def isNamedEntity(indexs):
        for index in indexs:
            if ((postags[index][0] == 'n') and (len(postags[index]) > 1)) or (postags[index] == 'j'):
                return True
        return False

    # 通过单词索引获取完整实体索引
    def getFullEntityNameByIndex(ent_indexs):
        full_name = ''
        for ent_index in ent_indexs:
            full_name += words[ent_index]
        return full_name

    # 预处理：将带有 COO 关系的词语关系重定向
    for i in range(len(words)):
        # 名词关系重定向（小明和小强打了小兰和小花）
        if (arcs[i].relation == 'COO') and ((postags[i][0] == 'n') or (postags[i] == 'j')):
            arcs[i].relation = arcs[arcs[i].head].relation
            arcs[i].head = arcs[arcs[i].head].head
        # 动词关系重定向（主语缺失，小明出生在北京，居住在河北），此时需要将主语复制一份添加到后面
        if (arcs[i].relation == 'COO') and (postags[i] == 'v'):
            for j in range(len(words)):
                if (arcs[j].head == arcs[i].head) and (arcs[j].relation == 'SBV'):
                    words.append(words[j])
                    postags.append(postags[j])
                    arcs.append(arcs[j])
                    words[-1] = getFullEntityNameByIndex(findFullEntity(j))
                    arcs[-1].head = i

    # 规则抽取开始
    triples = []
    for i in range(len(words)):

        # rule 1 : 定中关系三元组
        if (postags[i][0] == 'n'):
            l_ent = None
            r_ent = [arcs[i].head]
            if (arcs[i].relation == 'ATT') and isNamedEntity(r_ent):
                for j in range(len(words)):
                    if (arcs[j].head == i) and (arcs[j].relation == 'ATT') and isNamedEntity([j]):
                        l_ent = [j]
                        triples.append([getFullEntityNameByIndex(l_ent), words[i], getFullEntityNameByIndex(r_ent)])

        # rule 2 : 定语后置关系三元组
        if (postags[i] == 'v'):
            l_ent = findFullEntity(arcs[i].head)
            r_ent = None
            if (arcs[i].relation == 'ATT') and isNamedEntity(l_ent):
                for j in range(len(words)):
                    r_ent = findFullEntity(j);
                    if (arcs[j].head == i) and (arcs[j].relation == 'VOB') and isNamedEntity(r_ent):
                        for k in range(len(words)):
                            if (arcs[k].head == i) and (arcs[k].relation == 'RAD'):
                                triples.append(
                                    [getFullEntityNameByIndex(l_ent), words[i], getFullEntityNameByIndex(r_ent)])

        '''
        #rule 3 : 主谓宾关系三元组
        if (postags[i] == 'v'):
            l_ent = None
            r_ent = None
            for j in range(len(words)):
                l_ent = findFullEntity(j)
                if (arcs[j].head == i) and (arcs[j].relation == 'SBV') and isNamedEntity(l_ent):
                    for k in range(len(words)):
                        r_ent = findFullEntity(k)
                        if (arcs[k].head == i) and (arcs[k].relation == 'VOB') and isNamedEntity(r_ent):
                            triples.append([getFullEntityNameByIndex(l_ent), words[i], getFullEntityNameByIndex(r_ent)])
        '''
        # rule 4 : 主谓动补关系三元组
        if (postags[i] == 'v'):
            l_ent = None
            r_ent = None
            for j in range(len(words)):
                l_ent = findFullEntity(j)
                if (arcs[j].head == i) and (arcs[j].relation == 'SBV') and isNamedEntity(l_ent):
                    for k in range(len(words)):
                        if (arcs[k].head == i) and (arcs[k].relation == 'CMP'):
                            for l in range(len(words)):
                                r_ent = findFullEntity(l)
                                if (arcs[l].head == k) and (arcs[l].relation == 'POB') and isNamedEntity(r_ent):
                                    triples.append([getFullEntityNameByIndex(l_ent), words[i] + words[k],
                                                    getFullEntityNameByIndex(r_ent)])

        '''
        #rule 5 : 把动被动关系三元组
        if (postags[i] == 'v'):
            l_ent = None
            r_ent = None
            for j in range(len(words)):
                if (arcs[j].head == i) and (arcs[j].relation == 'ADV'):
                    for k in range(len(words)):
                        r_ent = findFullEntity(k)
                        if (arcs[k].head == j) and (arcs[k].relation == 'POB') and isNamedEntity(r_ent):
                            for l in range(len(words)):
                                l_ent = findFullEntity(l)
                                if (arcs[l].head == i) and ((arcs[l].relation == 'FOB') or (arcs[l].relation == 'SBV')) and isNamedEntity(l_ent):
                                    if (arcs[l].relation == 'SBV'): # 把动关系
                                        triples.append([getFullEntityNameByIndex(l_ent), words[i], getFullEntityNameByIndex(r_ent)])
                                    elif (arcs[l].relation == 'FOB'): # 被动关系
                                        triples.append([getFullEntityNameByIndex(r_ent), words[i], getFullEntityNameByIndex(l_ent)])

        '''
        # rule 6: 解决指代问题
        # 柏林位于德国东北部，四面被勃兰登堡州环绕，施普雷河流经该市。
        '''
        抽取出（施普雷河 流经 柏林）
        '''

        if (postags[i] == 'v' and arcs[i].relation == 'COO'):  # 找到流经和环绕
            l_ents = []
            r_ents = []
            for j in range(len(words)):
                # 找到动词的主谓关系
                if (arcs[j].head == i) and (arcs[j].relation == 'SBV'):
                    l_ents.append(j)

                # 找到谓宾关系且为代词
                if (arcs[j].head == i) and (arcs[j].relation == 'VOB') and (postags[j] == 'r'):
                    # 找到代词所指代的主语
                    t = arcs[i].head  # t = 1 找到位于指的SBV
                    for k in range(len(words)):
                        if (arcs[k].head == t) and (arcs[k].relation == 'SBV'):
                            t = k
                            break;
                    r_ents.append(t)
            # 建立三元组
            for l_ent in l_ents:
                for r_ent in r_ents:
                    triples.append([words[l_ent], words[i], words[r_ent]])

        # 胡志元写的主谓宾
        if (postags[i] == 'v' and arcs[i].relation != 'COO'):
            l_ents = []
            r_ents = []
            for j in range(len(words)):
                if arcs[j].head == i and arcs[j].relation == 'SBV' and isNamedEntity(findFullEntity(j)):
                    l_ents.append(j)
                if (arcs[j].head == i) and (arcs[j].relation == 'VOB') and (postags[j] != 'v'):
                    r_ents.append(j)
            for l_ent in l_ents:
                for r_ent in r_ents:
                    triples.append([getFullEntityNameByIndex(findFullEntity(l_ent)), words[i],
                                    getFullEntityNameByIndex(findFullEntity(r_ent))])

        # rule 7 :缺主语的被动语句
        if (postags[i] == 'v' and arcs[i].relation == 'COO'):
            word1 = words[i]
            # print(word1)
            l_ents = []
            r_ents = []
            t = arcs[i].head
            for k in range(len(words)):
                if (arcs[k].head == t) and (arcs[k].relation == 'SBV'):
                    t = k
                    break;
            r_ents.append(t)
            # print(t)

            for j in range(len(words)):
                if words[j] == '被':  # j=6
                    if words[arcs[j].head] == word1:
                        for k in range(len(words)):
                            if arcs[k].head == j and arcs[k].relation == 'POB':
                                l_ents.append(k)

            for l_ent in l_ents:
                for r_ent in r_ents:
                    triples.append([words[l_ent], words[i], words[r_ent]])

        # rule 8 :不缺主语的被动语句  梵蒂冈被意大利所包围
        if (postags[i] == 'v'):
            l_ents = []
            r_ents = []
            for j in range(len(words)):
                if words[j] == '被':
                    for k in range(len(words)):
                        if arcs[k].head == j and arcs[k].relation == 'POB':
                            l_ents.append(k)
                if (arcs[j].head == i) and (arcs[j].relation == 'FOB'):
                    r_ents.append(j)
            for l_ent in l_ents:
                for r_ent in r_ents:
                    triples.append([words[l_ent], words[i], words[r_ent]])

        # rule 9 :被动句特殊
        '''
        美国“沃斯堡”号11日在南沙海域被中国海军盐城舰跟踪。
        抽取出（海军盐城舰 跟踪 沃斯堡）
        在此句中 追踪与 沃斯堡并非FOB的关系 而是SBV的关系 属于句法分析有误
        '''
        if (postags[i] == 'v'):
            word1 = words[i]
            l_ents = []
            r_ents = []
            for j in range(len(words)):
                if words[j] == '被':
                    if words[arcs[j].head] == word1:
                        for k in range(len(words)):
                            if arcs[k].head == j and arcs[k].relation == 'POB':
                                l_ents.append(k)
                if (arcs[j].head == i) and (arcs[j].relation == 'SBV'):
                    r_ents.append(j)
            for l_ent in l_ents:
                for r_ent in r_ents:
                    triples.append([getFullEntityNameByIndex(findFullEntity(l_ent)), words[i],
                                    getFullEntityNameByIndex(findFullEntity(r_ent))])

        # rule 8 :不缺主语的并列句子
        '''
        美方经常提到南海是太平洋与印度洋之间的重要航道，每年大批货船途经南海
        希望能将第二句话（货船 途径 南海）抽取出来
        柏林位于德国东北部，四面被勃兰登堡州环绕，施普雷河流经该市。
        长句子下此规则会出现（柏林 流经 该市）
        '''

        if (postags[i] == 'v' and arcs[i].relation == 'COO'):  # 寻找并列关系的动词
            l_ents = []
            r_ents = []
            for j in range(len(words) - 1):
                if (arcs[j].head == i) and (arcs[j].relation == 'SBV'):
                    l_ents.append(j)
                # print(j) # 5和10
                if (arcs[j].head == i) and (arcs[j].relation == 'VOB'):
                    r_ents.append(j)

            for l_ent in l_ents:
                for r_ent in r_ents:
                    triples.append([getFullEntityNameByIndex(findFullEntity(l_ent)), words[i],
                                    getFullEntityNameByIndex(findFullEntity(r_ent))])

    return triples


# statements.append('美国总统奥巴马出席了会议')
# statements.append('位于北三环的北京交通大学')
# statements.append('珠穆朗玛峰地处青藏高原')
# statements.append('东京坐落于日本')
# statements.append('梵蒂冈被意大利所包围')
# statements.append('意大利把梵蒂冈包围了')
# statements.append('美国人和法国人攻打中国人和日本人')
# statements.append('柏林位于德国东北部，是德国的首都')
# statements.append('柏林是德国首都，也是德国最大的城市，现有居民约340万人。柏林位于德国东北部，四面被勃兰登堡州环绕，施普雷河流经该市。柏林是德国十六个联邦州之一，和汉堡、不来梅同为德国仅有的三个城市州份。')
# statements.append('柏林位于德国东北部，四面被勃兰登堡州环绕，施普雷河流经该市。')
# statements.append('北京是中国首都，我很喜欢他。')
# statements.append('北京是首都，我很喜欢他。')
# statements.append('美国“沃斯堡”号11日在南沙海域被中国海军盐城舰跟踪。')
# statements.append('美方经常提到南海是太平洋与印度洋之间的重要航道，每年大批货船途经南海，维护“航行自由”至关重要。')
# statements.append('柏林也是德国十六个联邦州之一，和汉堡、不来梅同为德国仅有的三个城市州份。')
# statements.append('峰会前，习近平主席将出席二十国集团工商峰会开幕式并发表主旨演讲。')
# statements.append('女排主教练郎平表示，80年代的排球技术与现时无法比较，但女排精神的传承没有改变，队内每一名球员都是为集体荣誉而战。')
# statements.append('杜特尔特提到过与中国开展双边对话和在南海合作勘探资源的可能性，很多人就此认为他是亲华派。')
# statements.append('美国领导人准备参加北京奥运会。')
# statements.append('2月17日，美国航母战斗群进入南海海域。')
# statements.append('烤肉现在已成为台湾人中秋节最喜爱的活动之一。')
# statements.append('印度尼西亚表示，如果中国对南海的领土主张无法通过对话解决，可能将中国告上国际法院。')
# statements.append('中国外交部严辞警告“韩国配合美方加紧推进‘萨德’反导系统部署进程”，称“由此产生的一切后果由美韩承担。”')
# statements.append('国务院总理李克强10日致电巴基斯坦总理纳瓦兹·谢里夫，对巴基斯坦俾路支省奎达发生重大恐怖袭击事件表示慰问。')
# statements.append('有人反驳说，进入中国市场当然好，但如果被剥夺了获胜的机会，那就不好了。')
# statements.append('美国在韩国部署“萨德”。')
# statements.append('要支持宗教团体加强自身建设和人才培养，引导和支持藏传佛教代表人士用社会主义核心价值观引领教规教义阐释，促进藏传佛教与社会主义社会相适应。')
# statements.append('巴基斯坦俾路支省奎达发生重大恐怖袭击事件表示慰问。')
# statements.append('50余名沈阳市职业学校校长近日走进清华园，在沈阳市教育局与清华大学共同举办的首期沈阳市职业学校校长高级研修班上为自己，更为沈阳的职业教育而“充电”。沈阳市中等职业学校重组于上世纪80年代，绝大部分学校是由薄弱学校改造而成。近年来，随着国家、省、市各级政府对职业教育的重视，沈阳市职业教育有了较大发展。目前，沈阳市已有中等职业学校131所，中等职业学校教师9500人，专业教师4800人，在校生9万余人,年毕业生3万余人。2006年，为了让职业教育有一个更大的发展，沈阳市决定不仅在硬件上加大投入，按照国家级示范校的标准建6所万人规模的中等职业学校，同时，还要在在软件建设上有一个新突破，按照国家职业教育教学质量评估标准，全面提升沈阳市中等职业学校教育教学质量。为此，沈阳市教育局借助清华大学这样一个高层次的培训平台，举办各种层次的共10期研修班，对分管各项工作的副校长和专业教师约500人进行培训，通过国家教育部职业与成人教育司有关领导、国内优秀企业家、教育专家、知名学者和国内重点职业院校校长的讲座及经验交流，使参加研修人员政策水平、理论知识、教学管理能力及个人学养得到提高，从而全面提升沈阳市职业院校的内涵建设，进一步培养、打造出一支高水平的职业院校优秀的管理者和“双师型”教师队伍。沈阳市副市长王玲、沈阳市教育局局长李梦玲、教育部职成司副司长刘占山、清华大学副校长陈吉宁参加了首期研修班的开班仪式。他们表示，清华大学和沈阳市的这种合作，必将促进沈阳市职业教育的跨越式发展，双方在市、校人才合作培养模式上的有益探索，不仅会加深和扩大双方在各个领域的合作，也会对全国的职业教育提供有益的经验。')
# statements.append('日本海上自卫队9日宣布，将派海上自卫队“宙斯盾”舰参加美国即将于6月在夏威夷近海实施的海基型拦截导弹(SM3)的拦截试验，对目标进行雷达跟踪。“宙斯盾”护卫舰是首次参加此类拦截演习。海上自卫队幕僚长(相当于参谋长)斋藤隆表示，“将力争提高双方在海上的相互协调性”，由此可见，日美在MD方面共享信息等合作体制将进一步得到确立。据海上自卫队透露，预定参加此次演习的是曾经根据《反恐特别措施法》在阿拉伯海上进行过海上燃油补给活动的“雾岛(KIRISHIMA)”号(7250吨)。美国海军的“宙斯盾”舰计划用SM3对模拟弹道导弹进行拦截,而“雾岛”号将跟踪模拟弹道导弹的轨迹。“雾岛”号计划于本月从位于神奈川县的横须贺基地出发，在参加拦截试验结束后还将参加环太平洋联合演习。美国迄今为止曾6次成功地进行了SM3拦截试验。日本政府将于2007年度年底开始为海上自卫队的”宙斯盾”护卫舰装备SM3。')
# statements.append('目前，沈阳市已有中等职业学校131所，中等职业学校教师9500人，专业教师4800人，在校生9万余人,年毕业生3万余人。')
# statements.append('郑韶婕，出生于台湾台北，为中华民国女子羽球选手，有「-{羽球}-精灵」的外号。')
# statements.append('陶骏保，字璞青，江苏镇江人，中国民主革命家，光复会会员。')
# statements.append('刘铁男，男，汉族，祖籍山西祁县，出生于北京。')
# statements.append('621年，王世充投降后，王世恽和他一起被仇家独孤修德所杀。')
# statements.append('魏焌皓，身高178cm，体重70kg；现为香港无线电视经理人合约男艺员，毕业于第23期无线电视艺员训练班，2012年于剧集《OnCall36小时》饰演伤残人士「张一康」一角而开始为人熟悉。')


def Relation_Extraction(content):
    statements = SentenceSplitter.split(str(content))
    relation = json.load(open(resource_path+'all_relations.json'))
    all_triples = []
    for statement in statements:
        # print(statement)
        words, postags, arcs = ltp_parser.parse(statement)
        triples = rule_based_extraction(words, postags, arcs)

        tri = []

        for i in range(len(triples)):
            flag = 0
            for j in range(len(tri)):
                if triples[i][0] == tri[j][0] and triples[i][1] == tri[j][1] and triples[i][2] == tri[j][2]:
                    flag = 1
            if triples[i][0] == triples[i][2]:
                flag = 1
            if flag == 0:
                tri.append(triples[i])

        flag1 = 0
        if tri:
            # print('关系三元组:')
            for triple in tri:
                for i in relation:
                    if (triple[1] == i):
                        flag1 = 1
                        break
                if (flag1 == 1):
                    all_triples.append(triple)
    return all_triples

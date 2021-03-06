from glob import glob
import re

from sklearn.model_selection import train_test_split

from bert.tokenization import FullTokenizer

from ..utils import (get_or_make_label_encoder,
                     create_single_problem_generator,
                     create_pretraining_generator)

NER_TYPE = ['LOC',  # location
            'PER',  # person
            'ORG',  # organization
            'PRD',  # Product
            ]


def gold_horse_ent_type_process_fn(d):
    """golden horse ent type process fn
    Source: https://github.com/hltcoe/golden-ho rse

    Entity type:

        B, I, O: Begining \ In middle \ Outside of entity
        GPE: Country, City, District...
        LOC: Location, zoo, school...
        PER: Person
        ORG: Organiazation
        NAM: Entity
        NOM: More general, 女生, 男的...

        Example: 
            B-PER.NAM

    Only keep NAM here
    So after process:
        B-PER

    Arguments:
        ent_type {str} -- ent type from gold_horse data

    Returns:
        str -- processed enttype
    """
    ent_type = d.split('\t')[1].replace('\n', '')
    # keep nam only
    ent_type = ent_type if 'NAM' in ent_type else 'O'
    ent_type = ent_type.replace('.NAM', '')
    ent_type = ent_type.replace('GPE', 'LOC')
    return ent_type


def chinese_literature_ent_type_process_fn(d):
    """Not match my need

    Arguments:
        d {[type]} -- [description]

    Returns:
        [type] -- [description]
    """

    ent_type = d.split(' ')[1].replace('\n', '')
    return ent_type


def read_ner_data(file_pattern='data/ner/weiboNER*', proc_fn=None):
    """Read data from golden horse data


    Arguments:
        file_pattern {str} -- file patterns

    Returns:
        dict -- dict, key: 'train', 'eval', value: dict {'inputs', 'target'}
    """
    # if 'weiboNER' in file_pattern:
    #     proc_fn = gold_horse_ent_type_process_fn
    # elif 'Chinese-Literature' in file_pattern:
    #     proc_fn = chinese_literature_ent_type_process_fn

    result_dict = {
        'train': {
            'inputs': [],
            'target': []
        },
        'eval': {
            'inputs': [],
            'target': []
        }
    }
    file_list = glob(file_pattern)
    for file_path in file_list:
        raw_data = open(file_path, 'r', encoding='utf8').readlines()

        inputs_list = [[]]
        target_list = [[]]
        for d in raw_data:
            if d != '\n':
                # put first char to input
                inputs_list[-1].append(d[0])
                ent_type = proc_fn(d)
                target_list[-1].append(ent_type)
            else:
                inputs_list.append([])
                target_list.append([])

        # remove trailing empty str/list
        if not inputs_list[-1]:
            del inputs_list[-1]
        if not target_list[-1]:
            del target_list[-1]

        inputs_with_ent = []
        target_with_ent = []
        for inputs, target in zip(inputs_list, target_list):
            # if len(set(target)) > 1:
            inputs_with_ent.append(inputs)
            target_with_ent.append(target)

        if 'train' in file_path or 'dev' in file_path:
            result_dict['train']['inputs'] = inputs_with_ent
            result_dict['train']['target'] = target_with_ent
        else:
            result_dict['eval']['inputs'] = inputs_with_ent
            result_dict['eval']['target'] = target_with_ent
    return result_dict


def WeiboNER(params, mode):
    tokenizer = FullTokenizer(vocab_file=params.vocab_file)
    data = read_ner_data(file_pattern='data/ner/weiboNER*',
                         proc_fn=gold_horse_ent_type_process_fn)
    if mode == 'train':
        data = data['train']
    else:
        data = data['eval']
    inputs_list = data['inputs']
    target_list = data['target']

    flat_label = [item for sublist in target_list for item in sublist]

    label_encoder = get_or_make_label_encoder(
        'WeiboNER', mode, flat_label)

    return create_single_problem_generator('WeiboNER',
                                           inputs_list,
                                           target_list,
                                           label_encoder,
                                           params,
                                           tokenizer)


def WeiboFakeCLS(params, mode):
    """Just a test problem to test multiproblem support

    Arguments:
        params {Params} -- params
        mode {mode} -- mode
    """
    tokenizer = FullTokenizer(vocab_file=params.vocab_file)
    data = read_ner_data(file_pattern='data/ner/weiboNER*',
                         proc_fn=gold_horse_ent_type_process_fn)
    if mode == 'train':
        data = data['train']
    else:
        data = data['eval']
    inputs_list = data['inputs']
    target_list = data['target']

    new_target_list = [1 if len(set(t)) > 1 else 0 for t in target_list]

    label_encoder = get_or_make_label_encoder(
        'WeiboFakeCLS', mode, new_target_list, 'O')

    return create_single_problem_generator('WeiboFakeCLS',
                                           inputs_list,
                                           new_target_list,
                                           label_encoder,
                                           params,
                                           tokenizer)


def gold_horse_segment_process_fn(d):
    ent_type = d.split('\t')[0][-1]
    if ent_type not in ['0', '1', '2']:
        ent_type = '0'
    return ent_type


def WeiboSegment(params, mode):
    tokenizer = FullTokenizer(vocab_file=params.vocab_file)
    data = read_ner_data(file_pattern='data/ner/weiboNER*',
                         proc_fn=gold_horse_segment_process_fn)
    if mode == 'train':
        data = data['train']
    else:
        data = data['eval']
    inputs_list = data['inputs']
    target_list = data['target']

    flat_label = [item for sublist in target_list for item in sublist]

    label_encoder = get_or_make_label_encoder(
        'WeiboSegment', mode, flat_label, '0')

    return create_single_problem_generator('WeiboSegment',
                                           inputs_list,
                                           target_list,
                                           label_encoder,
                                           params,
                                           tokenizer)


def WeiboPretrain(params, mode):

    sentence_split = r'[.!?。？！]'

    tokenizer = FullTokenizer(vocab_file=params.vocab_file)
    data = read_ner_data(file_pattern='data/ner/weiboNER*',
                         proc_fn=gold_horse_segment_process_fn)
    if mode == 'train':
        data = data['train']
    else:
        data = data['eval']
    inputs_list = data['inputs']

    segmented_list = []
    for document in inputs_list:
        segmented_list.append([])
        doc_string = ''.join(document)
        splited_doc = re.split(sentence_split, doc_string)
        for sentence in splited_doc:
            if sentence:
                segmented_list[-1].append(list(sentence))
    segmented_list = [doc for doc in segmented_list if doc]

    return create_pretraining_generator('WeiboPretrain',
                                        segmented_list,
                                        None,
                                        None,
                                        params,
                                        tokenizer)


def read_bosonnlp_data(file_pattern, eval_size=0.2):
    file_list = glob(file_pattern)
    sentence_split = r'[!?。？！]'

    project_table = {
        'person_name': 'PER',
        'company_name': 'ORG',
        'location': 'LOC',
        'product_name': 'PRD'
    }
    input_list = []
    target_list = []

    if not file_list:
        raise FileNotFoundError('Please make sure you have downloaded BosonNLP\
        data and put it in the path you specified. \
        Download: https://bosonnlp.com/resources/BosonNLP_NER_6C.zip')

    for file_path in file_list:
        with open(file_path, 'r', encoding='utf8') as f:
            data_list = f.readlines()

        for doc in data_list:
            if '}}}}' in doc:
                continue
            splited_doc = re.split(sentence_split, doc)

            for sentence in splited_doc:

                # split doc into sentences

                input_list.append([])
                target_list.append([])

                # split by {{
                doc_chunk_list = sentence.split('{{')
                for chunk in doc_chunk_list:
                    if '}}' not in chunk or ':' not in chunk:
                        target_list[-1] += ['O']*len(chunk)
                        input_list[-1] += list(chunk)
                    else:
                        ent_chunk, text_chunk = chunk.split('}}')
                        punc_ind = ent_chunk.index(':')
                        ent_type = ent_chunk[:punc_ind]
                        ent = ent_chunk[punc_ind+1:]
                        if ent_type in project_table:
                            for char_ind, ent_char in enumerate(ent):
                                if char_ind == 0:
                                    loc_char = 'B'
                                else:
                                    loc_char = 'I'
                                target_list[-1].append(loc_char +
                                                       '-'+project_table[ent_type])
                                input_list[-1].append(ent_char)
                        else:
                            target_list[-1] += ['O']*len(ent)
                            input_list[-1] += list(ent)

                        target_list[-1] += ['O']*len(text_chunk)
                        input_list[-1] += list(text_chunk)

    return_input, return_target = [], []
    for inp, tar in zip(input_list, target_list):
        if inp and tar:
            return_input.append(inp)
            return_target.append(tar)
        assert len(inp) == len(tar)

    train_input, eval_input, train_target, eval_target = train_test_split(
        return_input, return_target, test_size=eval_size, random_state=1024)
    result_dict = {
        'train': {},
        'eval': {}
    }
    result_dict['train']['inputs'] = train_input
    result_dict['train']['target'] = train_target
    result_dict['eval']['inputs'] = eval_input
    result_dict['eval']['target'] = eval_target
    return result_dict


def read_msra(file_pattern, eval_size):
    file_list = glob(file_pattern)

    project_table = {
        'nr': 'PER',
        'nt': 'ORG',
        'ns': 'LOC'
    }

    input_list = []
    target_list = []

    for file_path in file_list:
        with open(file_path, 'r', encoding='utf8') as f:
            data_list = f.readlines()

        for sentence in data_list:
            sentence = sentence.replace('\n', '')
            input_list.append([])
            target_list.append([])
            sentence_word_list = sentence.split(' ')
            for word in sentence_word_list:
                if word:
                    ent, ent_type = word.split('/')
                    if ent_type not in project_table:
                        input_list[-1] += list(ent)
                        target_list[-1] += ['O'] * len(ent)
                    else:
                        for char_ind, ent_char in enumerate(ent):
                            if char_ind == 0:
                                loc_char = 'B'
                            else:
                                loc_char = 'I'

                            target_list[-1].append(loc_char +
                                                   '-'+project_table[ent_type])
                            input_list[-1].append(ent_char)

    return_input, return_target = [], []
    for inp, tar in zip(input_list, target_list):
        if inp and tar:
            return_input.append(inp)
            return_target.append(tar)
        assert len(inp) == len(tar)

    train_input, eval_input, train_target, eval_target = train_test_split(
        return_input, return_target, test_size=eval_size, random_state=1024)
    result_dict = {
        'train': {},
        'eval': {}
    }
    result_dict['train']['inputs'] = train_input
    result_dict['train']['target'] = train_target
    result_dict['eval']['inputs'] = eval_input
    result_dict['eval']['target'] = eval_target
    return result_dict


def NER(params, mode):
    tokenizer = FullTokenizer(vocab_file=params.vocab_file)
    weibo_data = read_ner_data(file_pattern='data/ner/weiboNER*',
                               proc_fn=gold_horse_ent_type_process_fn)
    boson_data = read_bosonnlp_data(
        file_pattern='data/ner/BosonNLP_NER_6C/BosonNLP*', eval_size=0.2)
    msra_data = read_msra(file_pattern='data/ner/MSRA/train*', eval_size=0.2)

    inputs_list = []
    target_list = []
    for data in [weibo_data, boson_data, msra_data]:
        if mode == 'train':
            inputs_list += data['train']['inputs']
            target_list += data['train']['target']

        else:
            inputs_list += data['eval']['inputs']
            target_list += data['eval']['target']

    flat_target_list = ['O',
                        'B-LOC',
                        'B-PER',
                        'B-ORG',
                        'B-PRD',
                        'I-LOC',
                        'I-PER',
                        'I-ORG',
                        'I-PRD', ]
    label_encoder = get_or_make_label_encoder(
        'NER', mode, flat_target_list, zero_class='O')
    return create_single_problem_generator('NER',
                                           inputs_list,
                                           target_list,
                                           label_encoder,
                                           params,
                                           tokenizer)

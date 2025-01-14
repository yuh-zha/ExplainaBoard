# -*- coding: utf-8 -*-
import explainaboard.error_analysis as ea
import explainaboard.data_utils as du
import os
import numpy


def get_aspect_value(sent_list, aspect_list, sample_list_tag, sample_list_tag_pred, dict_aspect_func):
    dict_span2aspect_val = {}
    dict_span2aspect_val_pred = {}

    for aspect, fun in dict_aspect_func.items():
        dict_span2aspect_val[aspect] = {}
        dict_span2aspect_val_pred[aspect] = {}

    dict_sid2sample = {}

    sample_id = 0
    for sent, asp, tag, tag_pred in zip(sent_list, aspect_list, sample_list_tag, sample_list_tag_pred):

        word_list = sent.split(" ")
        aspect_list = asp.split(" ")

        # for saving errorlist -- fine-grained version
        dict_sid2sample[str(sample_id)] = ea.format4json2(ea.format4json2(asp) + "|||" + ea.format4json2(sent))

        sent_length = len(word_list)
        aspect_length = len(aspect_list)

        asp_pos = 0
        if sent.find(asp) != -1:
            asp_pos_char = sent.find(asp)
            asp_pos = ea.dict_char2word(sent)[asp_pos_char] - 1

        sent_pos = ea.tuple2str((sample_id, tag))
        sent_pos_pred = ea.tuple2str((sample_id, tag_pred))

        # Sentence Length: sentALen
        aspect = "aspPos"
        if aspect in dict_aspect_func.keys():
            dict_span2aspect_val[aspect][sent_pos] = asp_pos * 1.0 / float(sent_length)
            dict_span2aspect_val_pred[aspect][sent_pos_pred] = asp_pos * 1.0 / float(sent_length)

        # Sentence Length: sentALen
        aspect = "senLen"
        if aspect in dict_aspect_func.keys():
            dict_span2aspect_val[aspect][sent_pos] = float(sent_length)
            dict_span2aspect_val_pred[aspect][sent_pos_pred] = float(sent_length)

        # Sentence Length: sentBLen
        aspect = "aspLen"
        if aspect in dict_aspect_func.keys():
            dict_span2aspect_val[aspect][sent_pos] = float(aspect_length)
            dict_span2aspect_val_pred[aspect][sent_pos_pred] = float(aspect_length)

        # Tag: tag
        aspect = "tag"
        if aspect in dict_aspect_func.keys():
            dict_span2aspect_val["tag"][sent_pos] = tag
            dict_span2aspect_val_pred[aspect][sent_pos_pred] = tag

        sample_id += 1
    # print(dict_span2aspect_val["bleu"])
    return dict_span2aspect_val, dict_span2aspect_val_pred, dict_sid2sample


def evaluate(task_type="ner", analysis_type="single", systems=[], dataset_name='dataset_name', model_name='model_name',
             output_filename="./output.json", is_print_ci=False,
             is_print_case=False, is_print_ece=False):
    path_text = systems[0] if analysis_type == "single" else ""
    path_comb_output = "model_name" + "/" + path_text.split("/")[-1]
    dict_aspect_func, dict_precomputed_path, obj_json = ea.load_task_conf(task_dir=os.path.dirname(__file__))

    aspect_list, sent_list, true_label_list, pred_label_list = du.tsv_to_lists(path_text, col_ids=(0,1,2,3))

    error_case_list = []
    if is_print_case:
        error_case_list = ea.get_error_case_classification(true_label_list, pred_label_list, aspect_list, sent_list)
        print(" -*-*-*- the number of error casse:\t", len(error_case_list))

    # Confidence Interval of Holistic Performance
    confidence_low, confidence_up = 0, 0
    if is_print_ci:
        confidence_low, confidence_up = ea.compute_confidence_interval_acc(true_label_list, pred_label_list,
                                                                           n_times=100)

    dict_span2aspect_val, dict_span2aspect_val_pred, dict_sid2sample = get_aspect_value(sent_list, aspect_list,
                                                                                        true_label_list,
                                                                                        pred_label_list,
                                                                                        dict_aspect_func)

    holistic_performance = ea.accuracy(true_label_list, pred_label_list)
    holistic_performance = format(holistic_performance, '.3g')

    print("------------------ Holistic Result----------------------")
    print(holistic_performance)

    dict_bucket2span = {}
    dict_bucket2span_pred = {}
    dict_bucket2f1 = {}
    aspect_names = []

    for aspect, func in dict_aspect_func.items():
        # print(aspect, dict_span2aspect_val[aspect])
        dict_bucket2span[aspect] = ea.select_bucketing_func(func[0], func[1], dict_span2aspect_val[aspect])
        # print(aspect, dict_bucket2span[aspect])
        # exit()
        dict_bucket2span_pred[aspect] = ea.bucket_attribute_specified_bucket_interval(dict_span2aspect_val_pred[aspect],
                                                                                      dict_bucket2span[aspect].keys())
        # dict_bucket2span_pred[aspect] = __select_bucketing_func(func[0], func[1], dict_span2aspect_val_pred[aspect])
        dict_bucket2f1[aspect] = get_bucket_acc_with_error_case(dict_bucket2span[aspect],
                                                                dict_bucket2span_pred[aspect], dict_sid2sample,
                                                                is_print_ci, is_print_case)
        aspect_names.append(aspect)
    print("aspect_names: ", aspect_names)

    print("------------------ Breakdown Performance")
    for aspect in dict_aspect_func.keys():
        ea.print_dict(dict_bucket2f1[aspect], aspect)
    print("")

    # Calculate databias w.r.t numeric attributes
    dict_aspect2bias = {}
    for aspect, aspect2Val in dict_span2aspect_val.items():

        if type(list(aspect2Val.values())[0]) != type("string"):
            # if isinstance(list(aspect2Val.values())[0], str):
            dict_aspect2bias[aspect] = numpy.average(list(aspect2Val.values()))

    print("------------------ Dataset Bias")
    for k, v in dict_aspect2bias.items():
        print(k + ":\t" + str(v))
    print("")

    dict_fine_grained = {}
    for aspect, metadata in dict_bucket2f1.items():
        dict_fine_grained[aspect] = []
        for bucket_name, v in metadata.items():
            # print("---------debug--bucket name old---")
            # print(bucket_name)
            bucket_name = ea.beautify_interval(bucket_name)
            # print("---------debug--bucket name new---")
            # print(bucket_name)

            # bucket_value = format(v[0]*100,'.4g')
            bucket_value = format(v[0], '.4g')
            n_sample = v[1]
            confidence_low = format(v[2], '.4g')
            confidence_up = format(v[3], '.4g')

            # for saving errorlist -- fine_grained version
            bucket_error_case = v[4]

            # instantiation
            dict_fine_grained[aspect].append({"bucket_name": bucket_name, "bucket_value": bucket_value, "num": n_sample,
                                              "confidence_low": confidence_low, "confidence_up": confidence_up,
                                              "bucket_error_case": bucket_error_case})

    # dict_fine_grained[aspect].append({"bucket_name":bucket_name, "bucket_value":bucket_value, "num":n_sample, "confidence_low":confidence_low, "confidence_up":confidence_up, "bucket_error_case":[]})

    obj_json["task"] = task_type
    obj_json["data"]["name"] = dataset_name
    obj_json["data"]["language"] = "English"
    obj_json["data"]["bias"] = dict_aspect2bias

    obj_json["model"]["name"] = model_name

    obj_json["model"]["results"]["overall"]["performance"] = holistic_performance
    obj_json["model"]["results"]["overall"]["confidence_low"] = confidence_low
    obj_json["model"]["results"]["overall"]["confidence_up"] = confidence_up
    obj_json["model"]["results"]["fine_grained"] = dict_fine_grained

    # add errorAnalysis -- holistic
    obj_json["model"]["results"]["overall"]["error_case"] = error_case_list

    # Calibration
    ece = 0
    dic_calibration = []
    if is_print_ece:
        ece, dic_calibration = ea.calculate_ece_by_file(path_text, prob_col=4, right_or_not_col=5,
                                                        size_of_bin=10, dataset="dataset_name", model="model_name")

    obj_json["model"]["results"]["calibration"] = dic_calibration

    #
    obj_json["data"]["output"] = path_comb_output

    ea.save_json(obj_json, output_filename)


def get_bucket_acc_with_error_case(dict_bucket2span, dict_bucket2span_pred, dict_sid2sentpair, is_print_ci,
                                   is_print_case):
    # The structure of span_true or span_pred
    # 2345|||Positive
    # 2345 represents sentence id
    # Positive represents the "label" of this instance

    dict_bucket2f1 = {}

    for bucket_interval, spans_true in dict_bucket2span.items():
        spans_pred = []

        # print('bucket_interval: ',bucket_interval)
        if bucket_interval not in dict_bucket2span_pred.keys():
            # print(bucket_interval)
            raise ValueError("Predict Label Bucketing Errors")
        else:
            spans_pred = dict_bucket2span_pred[bucket_interval]

        # loop over samples from a given bucket
        error_case_bucket_list = []

        if is_print_case:
            for info_true, info_pred in zip(spans_true, spans_pred):
                sid_true, label_true = info_true.split("|||")
                sid_pred, label_pred = info_pred.split("|||")
                if sid_true != sid_pred:
                    continue

                sent = dict_sid2sentpair[sid_true]
                if label_true != label_pred:
                    error_case_info = label_true + "|||" + label_pred + "|||" + sent
                    error_case_bucket_list.append(error_case_info)

        accuracy_each_bucket = ea.accuracy(spans_pred, spans_true)
        confidence_low, confidence_up = 0, 0
        if is_print_ci:
            confidence_low, confidence_up = ea.compute_confidence_interval_acc(spans_pred, spans_true)

        dict_bucket2f1[bucket_interval] = [accuracy_each_bucket, len(spans_true), confidence_low, confidence_up,
                                           error_case_bucket_list]

        # print(error_case_bucket_list)

        print("accuracy_each_bucket:\t", accuracy_each_bucket)

    return ea.sort_dict(dict_bucket2f1)

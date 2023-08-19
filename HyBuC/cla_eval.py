import numpy as np
import torch
from sklearn.metrics import (accuracy_score, f1_score, precision_recall_curve,
                             precision_score, recall_score, roc_auc_score,
                             roc_curve)
from tqdm import tqdm

from cla_model import PatchNetExtended
from cla_utils import mini_batches_PNExtended


def running_evaluation(model, data):
    model.eval()  # eval mode (batchnorm uses moving mean/variance instead of mini-batch mean/variance)
    with torch.no_grad():
        predicts, groundtruth = list(), list()
        for i, (batch) in enumerate(tqdm(data)):
            embedding_ftr, pad_msg, pad_added_code, pad_removed_code, labels = batch
            embedding_ftr = torch.tensor(embedding_ftr).cuda()
            pad_msg, pad_added_code, pad_removed_code, labels = torch.tensor(pad_msg).cuda(), torch.tensor(
                pad_added_code).cuda(), torch.tensor(pad_removed_code).cuda(), torch.cuda.FloatTensor(labels)
            predicts.append(model.forward(embedding_ftr, pad_msg,
                            pad_added_code, pad_removed_code))
            groundtruth.append(labels)

        predicts = torch.cat(predicts).cpu().detach().numpy()
        groundtruth = torch.cat(groundtruth).cpu().detach().numpy()
        predicts = np.argmax(predicts, axis=1)

        accuracy = accuracy_score(y_true=groundtruth, y_pred=predicts)
        prc = precision_score(y_true=groundtruth,
                              y_pred=predicts, average='micro')
        rc = recall_score(y_true=groundtruth, y_pred=predicts, average='micro')
        f1 = f1_score(y_true=groundtruth, y_pred=predicts, average='micro')
        # auc_score = roc_auc_score(groundtruth, predicts)

        # 计算每个类别的precision、recall和f1指标
        class_names = ['Assignment', 'Computation',
                       'Function', 'Interface', 'Logic', 'Others']
        precisions = precision_score(
            groundtruth, predicts, average=None, labels=range(len(class_names)))
        recalls = recall_score(groundtruth, predicts,
                               average=None, labels=range(len(class_names)))
        f1_scores = f1_score(groundtruth, predicts,
                             average=None, labels=range(len(class_names)))

        accuracy = accuracy_score(groundtruth, predicts)

        macro_precision = precision_score(
            groundtruth, predicts, average='macro', labels=range(len(class_names)))
        macro_recall = recall_score(
            groundtruth, predicts, average='macro', labels=range(len(class_names)))
        macro_f1 = f1_score(groundtruth, predicts,
                            average='macro', labels=range(len(class_names)))

        print("{:^80}".format("Overall Metrics"))
        print("{:^20}\t{:^20}\t{:^20}\t{:^20}".format(
            "", "precision", "recall", "f1-score"))
        for i in range(len(class_names)):
            print("{:^20}\t{:^20.4f}\t{:^20.4f}\t{:^20.4f}".format(
                class_names[i], precisions[i], recalls[i], f1_scores[i]))
        print("{:^20}\t{:^20}\t{:^20}\t{:^20.4f}".format("", "", "", accuracy))
        print("{:^20}\t{:^20.4f}\t{:^20.4f}\t{:^20.4f}".format(
            "macro avg", macro_precision, macro_recall, macro_f1))

        return


def evaluation_model(data, params):
    embedding_ftr, pad_msg, pad_added_code, pad_removed_code, labels, dict_msg, dict_code = data
    batches = mini_batches_PNExtended(X_ftr=embedding_ftr, X_msg=pad_msg, X_added_code=pad_added_code, X_removed_code=pad_removed_code,
                                      Y=labels, mini_batch_size=params.batch_size, shuffled=False)

    params.filter_sizes = [int(k) for k in params.filter_sizes.split(',')]
    params.vocab_msg, params.vocab_code = len(dict_msg), len(dict_code)
    params.embedding_ftr = embedding_ftr.shape[1]

    params.class_num = 6

    # Device configuration
    params.device = torch.device(
        'cuda' if torch.cuda.is_available() else 'cpu')
    model = PatchNetExtended(args=params)
    model.load_state_dict(torch.load(params.load_model))
    if torch.cuda.is_available():
        model = model.cuda()

    running_evaluation(model=model, data=batches)

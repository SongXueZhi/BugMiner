import datetime
import os

import torch
import torch.nn as nn
from tqdm import tqdm

from cla_model import PatchNetExtended
from cla_utils import mini_batches_PNExtended, save
from FCLLoss import focal_loss


def train_model(data, params):
    embedding_ftr, pad_msg, pad_added_code, pad_removed_code, labels, dict_msg, dict_code = data
    batches = mini_batches_PNExtended(X_ftr=embedding_ftr, X_msg=pad_msg, X_added_code=pad_added_code, X_removed_code=pad_removed_code,
                                      Y=labels, mini_batch_size=params.batch_size, shuffled=True)

    params.filter_sizes = [int(k) for k in params.filter_sizes.split(',')]
    params.save_dir = os.path.join(
        params.save_dir, datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    params.vocab_msg, params.vocab_code = len(dict_msg), len(dict_code)
    params.embedding_ftr = embedding_ftr.shape[1]

    params.class_num = 6

    # Device configuration
    params.device = torch.device(
        'cuda' if torch.cuda.is_available() else 'cpu')
    model = PatchNetExtended(args=params)

    if torch.cuda.is_available():
        model = model.cuda()

    # Loss and optimizer
    optimizer = torch.optim.Adam(model.parameters(), lr=params.l2_reg_lambda)

    criterion = focal_loss(
        alpha=[4.,  10.,   2.,  10.,   1.0000, 10.], gamma=2, num_classes=6)

    for epoch in range(1, params.num_epochs + 1):
        total_loss = 0
        for i, (batch) in enumerate(tqdm(batches)):
            embedding_ftr, pad_msg, pad_added_code, pad_removed_code, labels = batch
            embedding_ftr = torch.tensor(embedding_ftr).cuda()
            pad_msg, pad_added_code, pad_removed_code, labels = torch.tensor(pad_msg).cuda(), torch.tensor(
                pad_added_code).cuda(), torch.tensor(pad_removed_code).cuda(), torch.cuda.LongTensor(labels)

            optimizer.zero_grad()

            predict = model.forward(
                embedding_ftr, pad_msg, pad_added_code, pad_removed_code)
            loss = criterion(predict, labels)
            loss.backward()
            total_loss += loss.item()
            optimizer.step()

        print('Epoch %i / %i -- Total loss: %f' %
              (epoch, params.num_epochs, total_loss))
        save(model, params.save_dir, 'epoch', epoch)

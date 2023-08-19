import json
import os

import numpy as np
import torch
from torch.utils.data import (DataLoader, Dataset, RandomSampler,
                              SequentialSampler, TensorDataset)


class InputFeatures(object):
    """A single training/test features for a example."""

    def __init__(self,
                 input_tokens,
                 input_ids,
                 label,

                 ):
        self.input_tokens = input_tokens
        self.input_ids = input_ids
        self.label = label


class TextDataset(Dataset):
    def __init__(self, codes, labels, tokenizer, args):
        self.examples = []
        for code, label in zip(codes, labels):
            self.examples.append(
                        convert_examples_to_features(code,label, tokenizer, args))
            
    def __len__(self):
        return len(self.examples)

    def __getitem__(self, i):
        return torch.tensor(self.examples[i].input_ids), torch.tensor(self.examples[i].label)


def convert_examples_to_features(codes, label, tokenizer, args):
    # source
    if args.block_size <= 0:
        # Our input block size will be the max possible for the model
        args.block_size = tokenizer.max_len_single_sentence
    args.block_size = min(args.block_size, tokenizer.max_len_single_sentence)
    codestr = "".join(str(code) for code in codes)
    code_tokens = tokenizer.tokenize(codestr)[:args.block_size-2]
    source_tokens = [tokenizer.cls_token]+code_tokens+[tokenizer.sep_token]
    source_ids = tokenizer.convert_tokens_to_ids(source_tokens)
    padding_length = args.block_size - len(source_ids)
    source_ids += [tokenizer.pad_token_id]*padding_length
    return InputFeatures(source_tokens, source_ids, label)

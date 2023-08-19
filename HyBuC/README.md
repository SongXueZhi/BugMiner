# HyBuC
HyBuC takes bug-fixing/inducing locations and source code, commit messages, and bug reports as the input. It utilizes feature encoding networks to encode each source of input separately and concatenate the encoded feature representation vectors as a whole embedding vector of the bug. Finally, a fully connected neural network (FCNN) is used to produce a bug type label as the bug classification result.

## Implementation Environment

Please install the neccessary libraries before running our tool:

- python==3.8.5
- transformers==4.31.0
- torch==1.13.1
- tqdm==4.65.0
- nltk==3.7
- numpy==1.24.3
- scikit-learn==1.2.2

## Data & Pretrained models:

- pretrained data: ./data/pretrained/
- classification data: Defects4J and BugMiner can be downloaded from the link we provide. Data in ./data/classification is one of the example data
- pretrained models: ./model/cc2ftr.pt

## Running and evalutation
- Use this command to train our model:
```python
python cc2ftr.py -train -train_data [path of our training data] -dictionary_data [path of our dictionary data]
```

- The command will create a folder snapshot used to save our model. To extract the code change features, please follow this command:
```python
python cc2ftr.py -predict -predict_data [path of our data] -dictionary_data [path of our dictionary data] -load_model [path of our model] -name [name of our output file]
```

- Use this command to train classification model:

```python
python cla.py -train -train_data [path of our data] -train_data_cc2ftr [path of our code changes features extracted from training data] -dictionary_data [path of our dictionary data]
```

- To evaluate the model for bug classification, please follow this command:

```python
python cla.py -predict -pred_data [path of our data] -pred_data_cc2ftr [path of our code changes features extracted from our data] -dictionary_data [path of our dictionary data] -load_model [path of our model]
```
# -*- coding: utf-8 -*-

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, average_precision_score, f1_score, matthews_corrcoef, roc_auc_score
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer

from bionev.utils import *


def LinkPrediction(embedding_look_up, original_graph, train_graph, test_pos_edges, seed):
    random.seed(seed)

    train_neg_edges = generate_neg_edges(original_graph, len(train_graph.edges()), seed)

    # create a auxiliary graph to ensure that testing negative edges will not used in training
    G_aux = copy.deepcopy(original_graph)
    G_aux.add_edges_from(train_neg_edges)
    test_neg_edges = generate_neg_edges(G_aux, len(test_pos_edges), seed)

    x_train, y_train = get_xy_sets(embedding_look_up, train_graph.edges(), train_neg_edges)
    clf1 = LogisticRegression(random_state=seed)
    clf1.fit(x_train, y_train)
    x_test, y_test = get_xy_sets(embedding_look_up, test_pos_edges, test_neg_edges)
    y_pred_proba = clf1.predict_proba(x_test)[:, 1]
    y_pred = clf1.predict(x_test)
    AUC = roc_auc_score(y_test, y_pred_proba)
    ACC = accuracy_score(y_test, y_pred)
    F1 = f1_score(y_test, y_pred)
    MCC =matthews_corrcoef(y_test, y_pred)
    PRC = average_precision_score(y_test, y_pred_proba)
    print('#' * 10 + 'Link Prediction Performance' + '#' * 10)
    print('AUC: %.4f, ACC: %.4f, F1: %.4f, MCC: %.4f, Average precision score: %.4f' % (AUC, ACC, F1, MCC, PRC))
    print('#' * 50)
    return (AUC, ACC, F1, MCC, PRC)

def NodeClassification(embedding_look_up, node_list, labels, testing_ratio, seed):

    X_train, y_train, X_test, y_test = split_train_test_classify(embedding_look_up, node_list, labels,
                                                                 testing_ratio=testing_ratio)
    binarizer = MultiLabelBinarizer(sparse_output=True)
    y_all = np.append(y_train, y_test)
    binarizer.fit(y_all)
    y_train = binarizer.transform(y_train).todense()
    y_test = binarizer.transform(y_test).todense()
    model = OneVsRestClassifier(LogisticRegression(random_state=seed, solver='lbfgs'))
    model.fit(X_train, y_train)
    y_pred_prob = model.predict_proba(X_test)

    ## small trick : we assume that we know how many label to predict
    y_pred = get_y_pred(y_test, y_pred_prob)

    accuracy = accuracy_score(y_test, y_pred)
    mcc = matthews_corrcoef(y_test, y_pred)
    micro_f1 = f1_score(y_test, y_pred, average="micro")
    macro_f1 = f1_score(y_test, y_pred, average="macro")

    print('#' * 9 + ' Node Classification Performance ' + '#' * 9)
    print(f'Accuracy: {accuracy:.3f}, MCC: {mcc:.3f}, Micro-F1: {micro_f1:.3f}, Macro-F1: {macro_f1:.3f}')
    print('#' * 50)
    return accuracy, mcc, micro_f1, macro_f1
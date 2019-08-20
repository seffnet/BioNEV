import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, average_precision_score, f1_score, matthews_corrcoef, roc_auc_score
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer

from bionev.utils import *


def do_link_prediction(
        *,
        embeddings,
        original_graph,
        train_graph,
        test_pos_edges,
        seed,
        save_model=None,
):
    random.seed(seed)
    train_neg_edges = generate_neg_edges(original_graph, len(train_graph.edges()), seed=0)
    # create a auxiliary graph to ensure that testing negative edges will not used in training
    G_aux = copy.deepcopy(original_graph)
    G_aux.add_edges_from(train_neg_edges)
    test_neg_edges = generate_neg_edges(G_aux, len(test_pos_edges), seed)

    x_train, y_train = get_xy_sets(embeddings, train_graph.edges(), train_neg_edges)
    clf1 = LogisticRegression(random_state=seed, solver='lbfgs')
    clf1.fit(x_train, y_train)
    x_test, y_test = get_xy_sets(embeddings, test_pos_edges, test_neg_edges)
    y_pred_proba = clf1.predict_proba(x_test)[:, 1]
    y_pred = clf1.predict(x_test)
    auc_roc = roc_auc_score(y_test, y_pred_proba)
    auc_pr = average_precision_score(y_test, y_pred_proba)
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    mcc = matthews_corrcoef(y_test, y_pred)
    if save_model is not None:
        joblib.dump(clf1, save_model)
    print('#' * 9 + ' Link Prediction Performance ' + '#' * 9)
    print(f'AUC-ROC: {auc_roc:.3f}, AUC-PR: {auc_pr:.3f}, Accuracy: {accuracy:.3f}, F1: {f1:.3f}, MCC: {mcc:.3f}')
    print('#' * 50)
    return auc_roc, auc_pr, accuracy, f1, mcc


def create_prediction_model(
        *,
        embeddings,
        original_graph,
        seed,
        save_model=None
):
    train_neg_edges = generate_neg_edges(original_graph, len(original_graph.edges()), seed=0)
    x_train, y_train = get_xy_sets(embeddings, original_graph.edges(), train_neg_edges)
    clf1 = LogisticRegression(random_state=seed, solver='lbfgs')
    clf1.fit(x_train, y_train)
    if save_model is not None:
        joblib.dump(clf1, save_model)


def do_node_classification(
        *,
        embeddings,
        node_list,
        labels,
        testing_ratio=0.2,
        seed=0
):
    X_train, y_train, X_test, y_test = split_train_test_classify(embeddings, node_list, labels,
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
    joblib.dump(model, 'saved_model.pkl')

    print('#' * 9 + ' Node Classification Performance ' + '#' * 9)
    print(f'Accuracy: {accuracy:.3f}, MCC: {mcc:.3f}, Micro-F1: {micro_f1:.3f}, Macro-F1: {macro_f1:.3f}')
    print('#' * 50)
    return accuracy, mcc, micro_f1, macro_f1

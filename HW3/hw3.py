# Copy and paste your implementations right here to check your result
# (Of course you can add your classes not written here)
# return the probability of each classes
import random

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score


def gini(sequence, weight=None):
    # sorted unique
    if weight is None:
        class_seq, cnt = np.unique(sequence.astype(np.int32), return_counts=True)
        p = cnt / sequence.shape[0]
        return 1 - np.sum(p ** 2)
    if len(weight) == 0:
        return 0
    p = np.sum(weight[sequence == 0]) / np.sum(weight)
    return 1 - p ** 2 - (1-p) ** 2
    

def entropy(sequence, weight=None):
    if weight is None:
        class_seq, cnt = np.unique(sequence.astype(np.int32), return_counts=True)
        p = cnt / sequence.shape[0]
        # p != 0 because unique will not return an element that's not in the sequence
        return (-1) * np.sum(p * np.log2(p))
    if len(weight) == 0:
        return 0
    p = np.sum(np.where(sequence == 0, weight, 0)) / np.sum(weight)
    return (-1) * (p * np.log2(p) + (1-p) * np.log2((1-p)))



class Question():
    def __init__(self, column, value):
        self.column = column
        self.value = value
        pass

    def match(self, row):
        val = row[self.column]
        return val >= self.value


class DecisionTree():
    def __init__(self, criterion='gini', max_depth=None, k_features=None, sample_weight=None):
        self.criterion = criterion
        self.max_depth = max_depth
        self.n_features = None
        self.root = None
        self.k_features = k_features
        self.feature_count = {}
        self.sample_weight = sample_weight
        if criterion == 'gini':
            self.measureFunc = gini
        else:
            self.measureFunc = entropy
        return None

    class TreeNode():
        def __init__(self):
            self.rows = None
            self.gain = None
            self.question = None
            self.pred = None
            self.left = None
            self.right = None
            return None

    def Informationgain(self, left_rows, right_rows, currentImpurity, l_weight=None, r_weight=None):
        if l_weight is not None and r_weight is not None:
            p = np.sum(l_weight) / (np.sum(l_weight) + np.sum(r_weight))
        else:
            p = float(len(left_rows)) / (len(left_rows) + len(right_rows))
        return currentImpurity - p * self.measureFunc(left_rows[:, -1].astype(np.int32), weight=l_weight) - (1 - p) * self.measureFunc(right_rows[:, -1].astype(np.int32), weight=r_weight)

    def find_best_split(self, rows):
        """Find the best split by repeating asking whether a property of a data is greater than thresholds
        generated by sorting N data using each property

        Args:
            rows (N,21): includes 20 properties and 1 columns representing the class of each row.
        """
        best_gain = 0
        best_question = None
        current_impurity = self.measureFunc(rows[:, -1].astype(np.int32), weight=self.sample_weight)

        # for random forest
        if self.k_features is not None:
            # choose $(max_features) features from data
            if self.k_features > self.n_features-1:
                n_cols = np.arange(self.n_features-1) # [0,21)
            else:
                n_cols = random.sample(range(self.n_features-1), k=self.k_features)
        else:
            n_cols = np.arange(self.n_features-1) # [0, 21)
        # print(n_cols)
        # for each feature
        col_sort = rows
        for col in n_cols:
            # sort data using values in column `col`
            # extract the data sorted using current feature
            
            # except adaboost
            # sample weight is not None for adaboost -> don't do sorting
            if self.sample_weight is None:
                col_sort = rows[np.argsort(rows[:, col])]

            # Try N-1 threshold values
            for idx in range(len(col_sort)):
                # i-th and i+1-th sorted value as current threshold
                current_threshold = col_sort[idx, col]

                # is data[col] >= current_threshold ?
                # if it's binary, the threshold is 0.5, so it's ok to use '>=' to compare
                # if it's real value, also valid to use '>=' to compare
                question = Question(column=col,
                                    value=current_threshold)

                # split the data using current question
                # true and false are candidates for best split(potential child nodes)
                true_rows = col_sort[col_sort[:, col] >= current_threshold]
                false_rows = col_sort[col_sort[:, col] < current_threshold]
                if self.sample_weight is not None:
                    left_weight = self.sample_weight[col_sort[:, col] >= current_threshold]
                    right_weight = self.sample_weight[col_sort[:, col] < current_threshold]
                else:
                    left_weight = None
                    right_weight = None
                
                current_gain = self.Informationgain(left_rows=true_rows,
                                                    right_rows=false_rows,
                                                    currentImpurity=current_impurity,
                                                    l_weight=left_weight,
                                                    r_weight=right_weight)
                # left_impurity = self.measureFunc(true_rows[:, -1].astype(np.int32), weight=left_weight)
                # left_impurity = left_impurity * true_rows.shape[0]
                # right_impurity = self.measureFunc(false_rows[:, -1].astype(np.int32), weight=right_weight)
                # right_impurity = right_impurity * false_rows.shape[0]
                # current_impurity = (left_impurity + right_impurity) / col_sort.shape[0]

                if current_gain >= best_gain:
                    best_gain, best_question = current_gain, question

        # print(f'{train_df.columns[best_question.column]}: {best_question.value}, {best_gain}')
        print(f'maximum gain: {best_gain}')
        label = train_df.columns[best_question.column]
        if self.feature_count.get(label) is not None:
            self.feature_count[label] = self.feature_count[label] + 1
        else:
            self.feature_count[label] = 1
        return current_gain, best_question


    def generateTree(self, rows, cur_depth=None):
        """Generate the decision tree

        Args:
            rows (N,21): includes 20 properties and 1 columns representing the class of each row.
            cur_depth: keep subtract until 0, the recursion will terminate when cur_depth = 0 or the node is pure
            dist: for adaboost, use distribution to calculate the error and find best split
        """
        cur_node = self.TreeNode()
        if self.measureFunc(sequence=rows[:, -1].astype(np.int32)) == 0:
            cur_node.pred = int(rows[0, -1])
        elif cur_depth == 0:
            if np.count_nonzero(rows[:, -1].astype(np.int32)) >= rows.shape[0] / 2:
                cur_node.pred = 1
            else:
                cur_node.pred = 0
        else:
            best_gain, best_question = self.find_best_split(rows=rows)
            # print(f'{train_df.columns[best_question.column]}:{best_question.value}')
            cur_node.rows = rows
            cur_node.gain = best_gain
            cur_node.question = best_question
            left_child = rows[rows[:, best_question.column]
                            >= best_question.value]
            right_child = rows[rows[:, best_question.column]
                            < best_question.value]
            # print(f'# left child:{len(left_child)}, # right child:{len(right_child)}')
            if cur_depth is None:
                cur_node.left = self.generateTree(rows=left_child)
                cur_node.right = self.generateTree(rows=right_child)
            else:
                cur_node.left = self.generateTree(
                    rows=left_child, cur_depth=cur_depth-1)
                cur_node.right = self.generateTree(
                    rows=right_child, cur_depth=cur_depth-1)
        return cur_node

    # Generate Tree by fitting data
    def fit(self, x_data, y_data):
        # print(x_data.shape)
        # print(y_data.shape)
        self.feature_count = {}
        y_data = y_data[:, np.newaxis]
        rows = np.hstack((x_data, y_data))
        self.n_features = rows.shape[1] # 21
        self.root = self.generateTree(rows=rows, cur_depth=self.max_depth)
    

    def feature_importance(self):
        fi = []
        for key in self.feature_count.keys():
            fi.append(self.feature_count[key])
        return fi

    def traverse(self, cur_node, x_data):
        if cur_node is None:
            return
        if cur_node.question is None:
            return cur_node.pred
        if cur_node.question.match(x_data) == 1:
            return self.traverse(cur_node=cur_node.left, x_data=x_data)
        else:
            return self.traverse(cur_node=cur_node.right, x_data=x_data)

    def print_acc(self, ans, pred):
        diff = np.sum(np.where(ans != pred, 1, 0))
        acc = 1 - diff / len(pred)
        print(f'criterion = {self.criterion}')
        print(f'max depth = {self.max_depth}')
        print(f'acc       = {acc}')
        print('====================')
    def get_feature_count(self):
        print(self.feature_count)
        return

    # After fitting, use the gererated tree to predict x_data
    def predict(self, x_data): # x_data doesn't contain label
        pred = []
        for row in x_data:
            ans = self.traverse(cur_node=self.root, x_data=row)
            pred.append(ans)
        return np.array(pred)


class AdaBoost():
    def __init__(self, n_estimators, criterion='gini'):
        self.n_estimators = n_estimators
        self.criterion = criterion
        if criterion == 'gini':
            self.meas_func = gini
        else:
            self.meas_func = entropy
        self.n_trees = [DecisionTree(self.criterion, max_depth=1) for i in range(n_estimators)]
        self.distribution = None
        self.weight = []
        return None
    
    def feature_count(self):
        for iter in range(self.n_estimators):
            self.n_trees[iter].get_feature_count()
        return 

    def print_acc(self, ans, pred):
        diff = np.sum(np.where(ans != pred, 1, 0))
        acc = 1 - diff / len(pred)
        print(f'criterion = {self.criterion}')
        print(f'acc       = {acc}')
        print('====================')

    def fit(self, x_data, y_data):
        self.distribution = np.repeat(1 / x_data.shape[0], x_data.shape[0])
        for iter in range(self.n_estimators):
            print(f'tree {iter+1}')
            # print(f'sample_weight: {self.distribution[0:10]}')
            self.n_trees[iter].sample_weight = self.distribution
            self.n_trees[iter].fit(x_data=x_data, y_data=y_data)
            
            # predict
            pred = self.n_trees[iter].predict(x_data)
            pred = np.where(pred != y_data, 1, 0)
            # print(f'total misclassified: {np.sum(pred)}')

            error_t = np.sum(pred * self.distribution)
            # print(f'error_t {error_t}')
            weight_t = (0.5) * np.log((1-error_t) / (error_t))
            # print(f'weight_t {weight_t}')
            self.weight.append(weight_t)
        
            # wrong pred => -1, right pred => 1
            pred = np.where(pred == 0, 1, -1)
            # print(f'pred: {pred[0:10]}')
            self.distribution = self.distribution * np.exp((-1) * weight_t * pred)
            # print(f'new weight: {self.distribution[0:10]}')
            self.distribution = self.distribution / np.sum(self.distribution)
            
        self.weight = np.array(self.weight)

    def predict(self, x_data):
        pred = np.zeros((len(x_data), self.n_estimators))
        # print(pred.shape)
        rows = x_data[:, 0:20]
        for iter in range(self.n_estimators):
            # prediction of iter-th tree on all data
            pred_i = self.n_trees[iter].predict(x_data=rows)
            pred_i = np.where(pred_i == 0, -1, 1)
            pred[:, iter] = pred_i
        total = np.sum(self.weight[np.newaxis, :] * pred, axis=1)
        total = np.where(total >= 0, 1, 0)
        return total

class RandomForest():
    def __init__(self, n_estimators, max_features, bootstrap=True, criterion='gini', max_depth=None):
        self.n_estimators = n_estimators
        self.max_features = int(np.round(max_features))
        self.use_bootstrap = bootstrap
        self.criterion = criterion
        self.max_depth = max_depth
        self.n_trees = [DecisionTree(self.criterion, self.max_depth, self.max_features) for i in range(self.n_estimators)]
        return None

    def fit(self, x_data, y_data):
        for iter in range(self.n_estimators):
            if self.use_bootstrap == True:
                # # choose $(max_features) features from data
                # n_cols = random.sample(range(x_data.shape[1]), k=self.max_features)
                # draw N random samples from dataset
                n_rows = np.random.randint(x_data.shape[0], size=len(x_data))
                rows = x_data[n_rows]
                # print(train_df.columns[n_cols])
                # print(rows.shape)
                self.n_trees[iter].fit(rows, y_data[n_rows])
            else:
                self.n_trees[iter].fit(x_data=x_data, y_data=y_data)
            # print(f'{iter+1} tree done')
        return

    def print_acc(self, ans, pred):
        diff = np.sum(np.where(ans != pred, 1, 0))
        acc = 1 - diff / len(pred)
        print(f'n estimators = {self.n_estimators}')
        print(f'max features = {self.max_features}')
        print(f'boostrap     = {self.use_bootstrap}')
        print(f'criterion    = {self.criterion}')
        print(f'max depth    = {self.max_depth}')
        print(f'acc          = {acc}')
        print('====================')

    def predict(self, x_data):
        x_pred = []
        for row in x_data:
            row = row[np.newaxis, :]
            vote_now = []
            for tree_k in self.n_trees:
                pred = tree_k.predict(x_data=row)
                vote_now.append(pred)
            label, cnt = np.unique(vote_now, return_counts=True)
            vote_now = label[np.argmax(cnt)]
            x_pred.append(vote_now)
        return np.array(x_pred)


train_df = pd.read_csv('train.csv')
val_df = pd.read_csv('val.csv')
x_train = np.array(train_df)
x_test = np.array(val_df)
new_test_df = pd.read_csv('x_test.csv')
new_test = np.array(new_test_df)

def main1():
    print('Decision Tree')
    clf_depth3 = DecisionTree(criterion='gini', max_depth=3)
    clf_depth3.fit(x_data=x_train[:, 0:20], y_data=x_train[:, -1])
    clf_depth3.get_feature_count()
    pred = clf_depth3.predict(x_test[:, 0:20])
    clf_depth3.print_acc(ans=x_test[:, -1], pred=pred)

    clf_depth10 = DecisionTree(criterion='gini', max_depth=10)
    clf_depth10.fit(x_data=x_train[:, 0:20], y_data=x_train[:, -1])
    pred = clf_depth10.predict(x_test[:, 0:20])
    clf_depth10.print_acc(x_test[:, -1], pred)

    clf_gini = DecisionTree(criterion='gini', max_depth=3)
    clf_gini.fit(x_data=x_train[:, 0:20], y_data=x_train[:, -1])
    # clf_gini.get_feature_count()
    pred = clf_gini.predict(x_test[:, 0:20])
    clf_gini.print_acc(x_test[:, -1], pred)

    clf_entropy = DecisionTree(criterion='entropy', max_depth=3)
    clf_entropy.fit(x_data=x_train[:, 0:20], y_data=x_train[:, -1])
    # clf_entropy.get_feature_count()
    pred = clf_entropy.predict(x_test[:, 0:20])
    clf_entropy.print_acc(x_test[:, -1], pred)

def main2():
    print('Adaboost(not done)')
    ada_10est = AdaBoost(n_estimators=10)
    ada_10est.fit(x_data=x_train[:, 0:20], y_data=x_train[:, -1])
    pred = ada_10est.predict(x_data=x_test[:, 0:20])
    ada_10est.print_acc(x_test[:, -1], pred)

    ada_100est = AdaBoost(n_estimators=100)
    ada_100est.fit(x_data=x_train[:, 0:20], y_data=x_train[:, -1])
    pred = ada_100est.predict(x_data=x_test[:, 0:20])
    ada_100est.print_acc(x_test[:, -1], pred)

def main3():
    print('Random Forest()')
    clf_10tree = RandomForest(n_estimators=10, max_features=np.sqrt(x_train.shape[1]), max_depth=None, criterion='gini')
    clf_10tree.fit(x_data=x_train[:, 0:20], y_data=x_train[:, -1])
    pred = clf_10tree.predict(x_data=x_test[:, 0:20])
    clf_10tree.print_acc(x_test[:, -1], pred)

    clf_100tree = RandomForest(n_estimators=100, max_features=np.sqrt(
        x_train.shape[1]), max_depth=None, criterion='gini')
    clf_100tree.fit(x_data=x_train[:, 0:20], y_data=x_train[:, -1])
    pred = clf_100tree.predict(x_data=x_test[:, 0:20])
    clf_100tree.print_acc(x_test[:, -1], pred)

def main4():
    print('Random Forest-2()')
    clf_random_features = RandomForest(n_estimators=10, max_features=np.sqrt(x_train.shape[1]))
    clf_random_features.fit(x_data=x_train[:, 0:20], y_data=x_train[:, -1])
    pred = clf_random_features.predict(x_data=x_test[:, 0:20])
    clf_random_features.print_acc(x_test[:, -1], pred)

    clf_all_features = RandomForest(n_estimators=10, max_features=x_train.shape[1])
    clf_all_features.fit(x_data=x_train[:, 0:20], y_data=x_train[:, -1])
    pred = clf_all_features.predict(x_data=x_test[:, 0:20])
    clf_all_features.print_acc(x_test[:, -1], pred)

def train_your_model(data):
    ## Define your model and training 
    clf_random_features = RandomForest(n_estimators=10, max_features=np.sqrt(x_train.shape[1]))
    clf_random_features.fit(x_data=data[:, 0:20], y_data=data[:, -1])
    return clf_random_features

def others():
    my_model = train_your_model(np.array(train_df))

    y_pred = my_model.predict(new_test)

    assert y_pred.shape == (500, )


    y_test = pd.read_csv('y_test.csv')['price_range'].values

    print('Test-set accuarcy score: ', accuracy_score(y_test, y_pred))

def discrete_checker(score, thres, clf, name, x_train, y_train, x_test, y_test):
    clf.fit(x_train, y_train)
    y_pred = clf.predict(x_test)
    if accuracy_score(y_test, y_pred) - thres >= 0:
        return score
    else:
        print(f"{name} failed")
        return 0


def patient_checker(score, thres, CLS, kwargs, name,
                    x_train, y_train, x_test, y_test, patient=10):
    while patient > 0:
        patient -= 1
        clf = CLS(**kwargs)
        clf.fit(x_train, y_train)
        y_pred = clf.predict(x_test)
        if accuracy_score(y_test, y_pred) - thres >= 0:
            return score
    print(f"{name} failed")
    print("Considering the randomness, we will check it manually")
    return 0


def load_dataset():
    file_url = "http://storage.googleapis.com/download.tensorflow.org/data/abalone_train.csv"
    df = pd.read_csv(
        file_url,
        names=["Length", "Diameter", "Height", "Whole weight", "Shucked weight",
               "Viscera weight", "Shell weight", "Age"]
    )

    df['Target'] = (df["Age"] > 15).astype(int)
    df = df.drop(labels=["Age"], axis="columns")

    train_idx = range(0, len(df), 10)
    test_idx = range(1, len(df), 20)

    train_df = df.iloc[train_idx]
    test_df = df.iloc[test_idx]

    x_train = train_df.drop(labels=["Target"], axis="columns")
    feature_names = x_train.columns.values
    x_train = x_train.values
    y_train = train_df['Target'].values

    x_test = test_df.drop(labels=["Target"], axis="columns")
    x_test = x_test.values
    y_test = test_df['Target'].values
    return x_train, y_train, x_test, y_test, feature_names

def test():
    score = 0

    data = np.array([1, 2])
    if abs(gini(data) - 0.5) < 1e-4:
        score += 2.5
    else:
        print("gini test failed")

    if abs(entropy(data) - 1) < 1e-4:
        score += 2.5
    else:
        print("entropy test failed")

    print(score)
    x_train, y_train, x_test, y_test, feature_names = load_dataset()

    score += discrete_checker(5, 0.9337,
                          DecisionTree(criterion='gini', max_depth=3),
                          "DecisionTree(criterion='gini', max_depth=3)",
                          x_train, y_train, x_test, y_test
                          )

    score += discrete_checker(2.5, 0.9036,
                          DecisionTree(criterion='gini', max_depth=10),
                          "DecisionTree(criterion='gini', max_depth=10)",
                          x_train, y_train, x_test, y_test
                          )

    score += discrete_checker(2.5, 0.9096,
                          DecisionTree(criterion='entropy', max_depth=3),
                          "DecisionTree(criterion='entropy', max_depth=3)",
                          x_train, y_train, x_test, y_test
                          )

    print(score)
    print("*** We will check your result for Question 3 manually *** (5 points)")

    score += patient_checker(
    7.5, 0.91, AdaBoost, {"n_estimators": 10},
    "AdaBoost(n_estimators=10)",
    x_train, y_train, x_test, y_test
)

    score += patient_checker(
    7.5, 0.87, AdaBoost, {"n_estimators": 100},
    "AdaBoost(n_estimators=100)",
    x_train, y_train, x_test, y_test
)

    score += patient_checker(
    5, 0.91, RandomForest,
    {"n_estimators": 10, "max_features": np.sqrt(x_train.shape[1])},
    "RandomForest(n_estimators=10, max_features=sqrt(n_features))",
    x_train, y_train, x_test, y_test
)

    score += patient_checker(
    5, 0.91, RandomForest,
    {"n_estimators": 100, "max_features": np.sqrt(x_train.shape[1])},
    "RandomForest(n_estimators=100, max_features=sqrt(n_features))",
    x_train, y_train, x_test, y_test
)

    score += patient_checker(
    5, 0.92, RandomForest,
    {"n_estimators": 10, "max_features": x_train.shape[1]},
    "RandomForest(n_estimators=10, max_features=n_features)",
    x_train, y_train, x_test, y_test
)

    print("*** We will check your result for Question 6 manually *** (20 points)")
    print("Approximate score range:", score, "~", score + 25)
    print("*** This score is only for reference ***")

if __name__ == '__main__':
    main1() # done
    main2() # ada
    main3() # done
    main4() # done
    # others() #test1
    test() #test2
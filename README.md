# AI Internship Projects

These are my three Week 1 projects for the AI internship. I built a handwritten-digit classifier with NumPy, a rule-based chatbot, and a Tic-Tac-Toe game with a Minimax AI. I used the projects to practice turning the ideas from the assignment into working programs.

## Week 1 results

| Task | What it does | Result |
|---|---|---|
| Basic Neural Network | A NumPy neural network that classifies handwritten digits from Kaggle's MNIST Digit Recognizer dataset. | **97.60% validation accuracy** and **0.1804 validation cross-entropy loss** in my recorded run. Early stopping ended training after 12 epochs; the best validation loss was at epoch 9. |
| Rule-Based Chatbot | A terminal chatbot that uses regular expressions to match messages to topics and choose a response. | Covers AI, Python, study tips, project help, sleep, and water. It also has help/topics commands and fallback replies. |
| Tic-Tac-Toe | A Tkinter game where Minimax chooses moves. | Play Human vs AI or AI vs AI. The game checks wins and draws and keeps score across rounds. |

## Screenshots

These screenshots show the projects running. The neural network reached 97.60% validation accuracy in the run shown below.

### Basic Neural Network — validation predictions

![Ten validation digits with true labels, predictions, and confidence scores](screenshots/mnist-validation.png)

### Basic Neural Network — Kaggle test predictions

![Predictions for ten unlabeled Kaggle test images](screenshots/mnist-kaggle-predictions.png)

### Rule-Based Chatbot

![Chatbot demonstrating its topics, AI and Python responses, and exit command](screenshots/chatbot.png)

### Tic-Tac-Toe

![Tic-Tac-Toe GUI showing a completed draw and score display](screenshots/tic-tac-toe.png)
## Files

~~~text
ai-internship-projects/
├── .gitignore
├── README.md
└── AI-intern week 1/
    ├── chatbot.py
    ├── neural_network.py
    ├── present_network.py
    ├── predict_test.py
    ├── tic_tac_toe.py
    ├── mnist_model.npz
    ├── requirements.txt
    └── data/  # Download Kaggle CSVs here; ignored by Git
~~~

## 1. Basic Neural Network

I wrote the network with **NumPy**, without using a machine-learning framework. Its main parts are:

- Input: 784 pixel values from each 28×28 grayscale image, scaled to the range 0–1.
- Hidden layer: 128 units with ReLU activation.
- Output: 10 digit classes with softmax probabilities.
- Training: mini-batches, cross-entropy loss, backpropagation, momentum, a stratified validation split, and early stopping.
- Visualizations: training/validation loss and accuracy, a validation confusion matrix, and example predictions.

The trained weights are saved in `mnist_model.npz`, so the presentation and prediction scripts can use the model without training it again.

### Dataset

To train the network or make Kaggle test predictions, download the **Digit Recognizer** files and put `train.csv`, `test.csv`, and `sample_submission.csv` in `AI-intern week 1/data/`. The CSVs are not included in this repository.

### Setup and run (Windows)

From the repository root, enter the Week 1 folder:

~~~bat
cd "AI-intern week 1"
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
~~~

Train the network and save its weights:

~~~bat
python neural_network.py
~~~

Show validation predictions using the saved model, without retraining:

~~~bat
python present_network.py
~~~

Predict the unlabeled Kaggle test images and create a submission file:

~~~bat
python predict_test.py
~~~

predict_test.py writes submission.csv. Kaggle's test file does not contain labels, so this script cannot calculate test accuracy.

## 2. Rule-Based Chatbot

Run from the Week 1 folder:

~~~bat
python chatbot.py
~~~

It normalizes capitalization, checks regular-expression patterns for supported topics, selects a topic-specific response, and uses a fallback if no intent matches. Type help or topics for the topic list; type bye to exit.

The chatbot's answers come from the patterns and response lists in `chatbot.py`. It doesn't use a trained language model or remember earlier messages.

## 3. Tic-Tac-Toe

Run from the Week 1 folder:

~~~bat
python tic_tac_toe.py
~~~

Choose **Human vs AI** or **AI vs AI** from the mode selector. Minimax looks ahead at possible moves. The score display tracks X wins, O wins, and draws; **New Game** clears the board and keeps the totals.

## Notes

- The neural network score is from my recorded validation run. It may change if the data split or training settings change.
- These are learning projects, built to practice the ideas and show how they work.
- Kaggle attribution: dataset from the [Digit Recognizer competition](https://www.kaggle.com/competitions/digit-recognizer/data).


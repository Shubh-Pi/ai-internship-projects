# AI Internship — Week 1 Projects

Three Python projects built for the AI Internship Week 1 tasks. The goal was to implement the required ideas and understand how each part works.

## Project results

| Task | What it does | Result |
|---|---|---|
| Basic Neural Network | Classifies handwritten digits from the Kaggle MNIST Digit Recognizer dataset using NumPy. | **97.60% validation accuracy** and **0.1804 validation cross-entropy loss**. Training stopped early after 12 epochs; the best validation loss was reached at epoch 9. |
| Rule-Based Chatbot | Matches user messages to topics with regular expressions and chooses a response from the matching intent. | Supports six topics: AI, Python, study tips, project help, sleep, and water; includes help/topics commands, fallback replies, and avoids repeating the same topic reply immediately. |
| Tic-Tac-Toe | Tkinter GUI game with Minimax decision-making. | Supports Human vs AI and AI vs AI, detects wins and draws, prefers faster wins, and tracks X wins, O wins, and draws across rounds. |

## 1. Basic Neural Network

The network is implemented with **NumPy**, without a machine-learning framework:

- Input: 784 pixel values from each 28×28 grayscale image, scaled to the range 0–1.
- Hidden layer: 128 units with ReLU activation.
- Output: 10 digit classes with softmax probabilities.
- Training: mini-batches, cross-entropy loss, backpropagation, momentum, a stratified validation split, and early stopping.
- Visualizations: training/validation loss and accuracy, a validation confusion matrix, and example predictions.

The saved weights are in mnist_model.npz.

### Run

1. Download the Kaggle **Digit Recognizer** files. Put train.csv, test.csv, and sample_submission.csv in a data/ directory.
2. Train and create the saved model:

   ~~~bash
   python neural_network.py
   ~~~

3. Show validation predictions using the saved model, without retraining:

   ~~~bash
   python present_network.py
   ~~~

4. Predict the unlabeled Kaggle test images and create a submission file:

   ~~~bash
   python predict_test.py
   ~~~

predict_test.py writes submission.csv. Kaggle's test file does not contain labels, so this script cannot calculate test accuracy.

## 2. Rule-Based Chatbot

Run the command-line chatbot:

~~~bash
python chatbot.py
~~~

It normalizes capitalization, checks regular-expression patterns for supported topics, selects a topic-specific response, and uses a fallback if no intent matches. Type help or topics for the topic list; type bye to exit.

This is a rule-based chatbot: its responses depend on the patterns and response lists in chatbot.py. It does not use a trained language model or retain conversational context.

## 3. Tic-Tac-Toe

Run the GUI:

~~~bash
python tic_tac_toe.py
~~~

Choose **Human vs AI** or **AI vs AI** from the mode selector. Minimax searches possible future moves; terminal scores favor quicker wins and delay unavoidable losses. The score display tracks X wins, O wins, and draws. **New Game** clears the board while preserving the score totals.

## Setup (Windows)

From the project directory:

~~~bat
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
~~~

Then place the Kaggle CSV files under data/ as described above. The dataset and virtual environment are intentionally excluded from this repository; download the dataset from Kaggle rather than committing the large CSV files.

## Files

~~~text
ai-internship/
├── chatbot.py
├── neural_network.py
├── mnist_model.npz
├── predict_test.py
├── present_network.py
├── requirements.txt
├── tic_tac_toe.py
└── data/                 # Download Kaggle CSVs here; not tracked by Git
~~~

## Notes

- The neural network result is from the recorded validation run; results can vary if training settings or data split change.
- The model is a learning project intended to demonstrate the neural-network workflow, not a production OCR system.
- Kaggle attribution: dataset from the [Digit Recognizer competition](https://www.kaggle.com/competitions/digit-recognizer/data).

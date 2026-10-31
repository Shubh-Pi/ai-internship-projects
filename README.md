# AI Internship — Week 1

I finished these three projects for Week 1 of my AI internship. I knew some of the theory, but needed practice building things myself. The digit recognizer took the most work: I had to get the image data into the right shape, train the network, and check its predictions.

## What I made

### Handwritten digit recognizer

I built a small neural network with NumPy to recognize digits from the Kaggle Digit Recognizer dataset. It got **97.60% accuracy on my validation set**. The code also plots training results and shows example predictions.

![Validation digits with labels and predictions](screenshots/mnist-validation.png)

I saved the trained weights in `AI-intern week 1/mnist_model.npz`. That lets the presentation script show results without training the network every time. The Kaggle test predictions are shown here:

![Predictions for sample Kaggle test images](screenshots/mnist-kaggle-predictions.png)

### Rule-based chatbot

The chatbot runs in the terminal. It looks for words and phrases in what you type, then replies about AI, Python, studying, projects, sleep, or water. Type `topics` or `help` to see the list, and `bye` to leave.

![Chatbot running in the terminal](screenshots/chatbot.png)

### Tic-Tac-Toe

I made a Tkinter game with Human vs AI and AI vs AI modes. Minimax picks the AI's moves, and the game keeps track of wins and draws.

![Tic-Tac-Toe game showing a draw](screenshots/tic-tac-toe.png)

## Run the projects

These steps are for Windows. In Command Prompt, go into the project folder and install the requirements:

~~~bat
cd "AI-intern week 1"
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
~~~

### Digit recognizer

Download `train.csv`, `test.csv`, and `sample_submission.csv` from the [Kaggle Digit Recognizer page](https://www.kaggle.com/competitions/digit-recognizer/data) and put them in `AI-intern week 1/data/`. The CSV files aren't included here.

Train the network:

~~~bat
python neural_network.py
~~~

After that, these use the saved model and don't train again:

~~~bat
python present_network.py
python predict_test.py
~~~

`predict_test.py` creates `submission.csv`. Kaggle's test images don't have labels, so the script can't report test accuracy.

### Chatbot

~~~bat
python chatbot.py
~~~

### Tic-Tac-Toe

~~~bat
python tic_tac_toe.py
~~~

## A note about the model file

`mnist_model.npz` contains the weights learned from training; it isn't the Kaggle image data. I included it so the saved-model demos can run without retraining. The training CSVs stay out of the repository.

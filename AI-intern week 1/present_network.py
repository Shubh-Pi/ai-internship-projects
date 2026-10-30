from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

DATA_PATH = Path("data/train.csv")
MODEL_PATH = Path("mnist_model.npz")
NUM_CLASSES = 10
VALIDATION_FRACTION = 0.15
SEED = 42
NUM_EXAMPLES = 10

if not DATA_PATH.exists():
    raise FileNotFoundError(f"Could not find {DATA_PATH.resolve()}")

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Could not find {MODEL_PATH.resolve()}")

raw_data = np.loadtxt(
    DATA_PATH, 
    delimiter = ",", 
    skiprows = 1, 
    dtype = np.uint8,
    )
labels_all = raw_data[:, 0].astype(np.int64)
images_all = raw_data[:, 1:].astype(np.float32)/ 255.0

rng = np.random.default_rng(SEED)
validation_parts = []
training_parts = []

for digit in range(NUM_CLASSES):
    digit_indices = np.flatnonzero(labels_all == digit)
    rng.shuffle(digit_indices)
    validation_count = int(round(len(digit_indices) * VALIDATION_FRACTION))
    validation_parts.append(digit_indices[:validation_count])
    training_parts.append(digit_indices[validation_count:])

# Concatenate only after every class has been split.
validation_indices = np.concatenate(validation_parts)
training_indices = np.concatenate(training_parts)
rng.shuffle(validation_indices)
rng.shuffle(training_indices)
X_val = images_all[validation_indices]
y_val = labels_all[validation_indices]

with np.load(MODEL_PATH) as saved_model:
    W1 = saved_model["W1"]
    b1 = saved_model["b1"]
    W2 = saved_model["W2"]
    b2 = saved_model["b2"]
    
def predict_probabilites(inputs):
    z1 = inputs @ W1 + b1
    a1 = np.maximum(0.0, z1)
    z2 = a1 @ W2 +b2
    z2 = z2 - np.max(z2, axis=1, keepdims=True)
    exp_scores  = np.exp(z2)
    return exp_scores / np.sum(exp_scores, axis=1, keepdims=True)

all_probabilities = predict_probabilites(X_val)
all_predictions = np.argmax(all_probabilities, axis=1)
accuracy = np.mean(all_predictions == y_val)
print(f"Loaded saved model:{MODEL_PATH}")
print(f"Validation accuracy: {accuracy:.2%}")

demo_rng = np.random.default_rng(7)
sample_count = min(NUM_EXAMPLES, len(y_val))
sample_positions = demo_rng.choice(len(y_val), size=sample_count, replace=False)
figure, axes = plt.subplots(2,5, figsize=(12,5))

for axis in axes.flat:
    axis.axis("off")

for axis, position in zip(axes.flat, sample_positions):
    image = X_val[position].reshape(28, 28)
    probabilities = all_probabilities[position]
    prediction = all_predictions[position]
    confidence = probabilities[prediction]
    axis.imshow(image, cmap="gray_r", interpolation="nearest")
    axis.set_title(f"True: {y_val[position]} | Guess: {prediction}\nConfidence: {confidence:.1%}")
    
figure.suptitle(f"Numpy MNIST classifier - validation accuracy {accuracy:.2%}")
figure.tight_layout()
plt.show()    
    

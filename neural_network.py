from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

DATA_PATH = Path("data/train.csv")
MODEL_PATH = Path("mnist_model.npz")
SEED = 42
HIDDEN_UNITS = 128
NUM_CLASSES = 10
VALIDATION_FRACTION = 0.15
BATCH_SIZE = 128
LEARNING_RATE = 0.05
MOMENTUM = 0.9
MAX_EPOCHS = 20
PATIENCE = 3

if not DATA_PATH.exists():
    raise FileNotFoundError(f"Could not find{DATA_PATH.resolve()}")

raw_data = np.loadtxt(
    DATA_PATH, 
    delimiter = ",", 
    skiprows = 1, 
    dtype = np.uint8,
    )

if raw_data.ndim != 2 or raw_data.shape[1] != 785:
    raise ValueError(f"Expected 785 columns(label + 784 pixels), got shape {raw_data.shape}")

labels_all = raw_data[:, 0].astype(np.int64)
pixels_all = raw_data[:, 1:].astype(np.float32)/ 255.0

if not np.array_equal(np.unique(labels_all), np.arange(NUM_CLASSES)):
    raise ValueError(f"Expected labels 0 through 9 in the training CSV.")

rng = np.random.default_rng(SEED)
validation_indices_by_class = []
training_indices_by_class = []

for digit in range(NUM_CLASSES):
    digit_indices = np.flatnonzero(labels_all == digit)
    rng.shuffle(digit_indices)
    number_for_validation = int(round(len(digit_indices) * VALIDATION_FRACTION))
    validation_indices_by_class.append(digit_indices[:number_for_validation])
    training_indices_by_class.append(digit_indices[number_for_validation:])
    
validation_indices = np.concatenate(validation_indices_by_class)
training_indices = np.concatenate(training_indices_by_class)
rng.shuffle(validation_indices)
rng.shuffle(training_indices)

X_val = pixels_all[validation_indices]
y_val = labels_all[validation_indices]
X_train = pixels_all[training_indices]
y_train = labels_all[training_indices]

input_units = X_train.shape[1]
output_units = NUM_CLASSES

W1 = rng.normal(
    loc = 0.0,
    scale = np.sqrt(2.0 / input_units),
    size = (input_units, HIDDEN_UNITS),
).astype(np.float32)
b1 = np.zeros((1, HIDDEN_UNITS), dtype = np.float32)

W2 = rng.normal(
    loc = 0.0,
    scale = np.sqrt(2.0 / (HIDDEN_UNITS + output_units)),
    size = (HIDDEN_UNITS, output_units),
).astype(np.float32)
b2 = np.zeros((1, output_units), dtype = np.float32)

velocity_W1 = np.zeros_like(W1)
velocity_b1 = np.zeros_like(b1)
velocity_W2 = np.zeros_like(W2)
velocity_b2 = np.zeros_like(b2)

def softmax(logits): 
    shifted_logits = logits - np.max(logits, axis=1, keepdims = True)
    exp_values = np.exp(shifted_logits)
    return exp_values / np.sum(exp_values, axis=1, keepdims = True)

def forward_pass(inputs, weights1, bias1,weights2, bias2):
    z1 = inputs @ weights1 + bias1
    a1 = np.maximum(0.0, z1)
    z2 = a1 @ weights2 + bias2
    probabilities = softmax(z2)
    return z1, a1, probabilities

def cross_entropy(probabilities, labels):
    row_indices = np.arange(labels.shape[0])
    correct_probabilities = probabilities[row_indices, labels]
    correct_probabilities = np.clip(correct_probabilities, 1e-12, 1.0)
    return -np.mean(np.log(correct_probabilities))

def evaluate(inputs, labels, weights1, bias1, weights2, bias2):
    total_loss = 0.0
    total_correct = 0
    
    for start in range(0, inputs.shape[0], BATCH_SIZE):
        end = start + BATCH_SIZE
        batch_x = inputs[start:end]
        batch_y = labels[start:end]
        _, _, probabilities = forward_pass(batch_x, weights1, bias1, weights2, bias2)
        batch_loss = cross_entropy(probabilities, batch_y)
        predictions = np.argmax(probabilities, axis=1)
        total_loss += batch_loss * batch_y.shape[0]
        total_correct += np.count_nonzero(predictions == batch_y)
    
    mean_loss = total_loss / labels.shape[0]
    accuracy = total_correct / labels.shape[0]
    return mean_loss, accuracy

training_losses = []
validation_losses = []
training_accuracies = []
validation_accuracies = []

best_validation_loss = float("inf")
best_weights = None
epochs_without_improvement = 0

for epoch in range(MAX_EPOCHS):
    shuffled_training_rows = rng.permutation(X_train.shape[0])
    
    for start in range(0, X_train.shape[0]):
        batch_rows = shuffled_training_rows[start : start + BATCH_SIZE]
        batch_x = X_train[batch_rows]
        batch_y = y_train[batch_rows]
        z1, a1, probabilities = forward_pass(batch_x, W1, b1, W2, b2)
        
        batch_row_indices = np.arange(batch_y.shape[0])
        dz2 = probabilities.copy()
        dz2[batch_row_indices, batch_y] -= 1.0
        dz2 /= batch_y.shape[0]
        
        dW2 = a1.T @ dz2 
        db2 = np.sum(dz2, axis=0, keepdims = True)
        da1 = dz2 @ W2.T
        dz1 = da1 * (z1 > 0.0)
        dW1 = batch_x.T @ dz1
        db1 = np.sum(dz1, axis=0, keepdims = True)
        
        velocity_W2 = MOMENTUM * velocity_W2 + dW2
        velocity_b2 = MOMENTUM * velocity_b2 + db2
        velocity_W1 = MOMENTUM * velocity_W1 + dW1
        velocity_b1 = MOMENTUM * velocity_b1 + db1

        W2 -= LEARNING_RATE * velocity_W2
        b2 -= LEARNING_RATE * velocity_b2
        W1 -= LEARNING_RATE * velocity_W1
        b1 -= LEARNING_RATE * velocity_b1
        
    training_loss, training_accuracy = evaluate(X_train, y_train, W1, b1, W2, b2)
    validation_loss, validation_accuracy = evaluate(X_val, y_val, W1, b1, W2, b2)
    training_losses.append(training_loss)
    validation_losses.append(validation_loss)
    training_accuracies.append(training_accuracy)
    validation_accuracies.append(validation_accuracy)
    
    print(
        f" Epoch {epoch + 1:02d}/{MAX_EPOCHS}  |"
        f" train_loss{training_loss:.4f}, acc{training_accuracy:.2%} |"
        f" val_loss{validation_loss:.4f}, acc {validation_accuracy:.2%}"
    )
    
    if validation_loss < best_validation_loss - 1e-4:
        best_validation_loss = validation_loss
        best_weights =(W1.copy(), b1.copy(), W2.copy(), b2.copy())
        epochs_without_improvement = 0
    else:
        epochs_without_improvement +=1
        
    if epochs_without_improvement >= PATIENCE:
        print("Early stopping: validation loss stopped improving.")
        break
    
W1, b1, W2, b2 = best_weights

final_validation_loss, final_validation_accuracy = evaluate(
    X_val, y_val, W1, b1, W2, b2
)
print(f"Best validation loss: {final_validation_loss:.4f}")
print(f"Best validation accuracy: {final_validation_accuracy:.2%}")

np.savez(
    MODEL_PATH,
    W1=W1,
    b1=b1,
    W2=W2,
    b2=b2,
)
print(f"Saved trained weights to {MODEL_PATH}")

epoch_numbers =np.arange(1, len(training_losses)+1)
figure, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].plot(epoch_numbers, training_losses, marker="o", label="Training")
axes[0].plot(epoch_numbers, validation_losses, marker="o", label="Validation")
axes[0].set_title("Cross-entropy loss")
axes[0].set_xlabel("Epoch")
axes[0].set_ylabel("Loss")
axes[0].legend()
axes[0].grid(True)
axes[1].plot(epoch_numbers, training_accuracies, marker="o", label="Training")
axes[1].plot(epoch_numbers, validation_accuracies, marker="o", label="Validation")
axes[1].set_title("Classification accuracy")
axes[1].set_xlabel("Epoch")
axes[1].set_ylabel("Accuracy")
axes[1].set_ylim(0.0, 1.0)
axes[1].legend()
axes[1].grid(True)
figure.tight_layout()
plt.show

_, _, validation_probabilities = forward_pass(X_val, W1, b1, W2, b2)
validation_predictions = np.argmax(validation_probabilities, axis=1)
confusion = np.zeros((NUM_CLASSES, NUM_CLASSES), dtype=np.int64)
np.add.at(confusion, (y_val, validation_predictions), 1)

figure, axis = plt.subplots(figsize=(7,6))
matrix_image = axis.imshow(confusion, cmap="Blues", interpolation="nearest")
figure.colorbar(matrix_image, ax=axis, label="Number of Images")
axis.set_title("Validation confusion matrix")
axis.set_xlabel("Predicted digit")
axis.set_ylabel("true digit")
axis.set_xticks(np.arange(NUM_CLASSES))
axis.set_yticks(np.arange(NUM_CLASSES))
for true_digit in range(NUM_CLASSES):
    for predicted_digit in range(NUM_CLASSES):
        axis.text(predicted_digit, true_digit, str(confusion[true_digit, predicted_digit]), ha="center", va="center")
figure.tight_layout()
plt.show

figure, image_axes = plt.subplots(2,5, figsize=(12, 5))
for index, axis in enumerate(image_axes.flat):
    axis.imshow(X_val[index].reshape(28,28), cmap="gray_r", interpolation="nearest")
    axis.set_title(f"True: {y_val[index]} | Guess: {validation_predictions[index]}")
    axis.axis("off")
figure.tight_layout()
plt.show()        
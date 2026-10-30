from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

DATA_PATH = Path("data/test.csv")
SAMPLE_PATH = Path("data/sample_submission.csv")
MODEL_PATH = Path("mnist_model.npz")
OUTPUT_PATH = Path("submission.csv")
BATCH_SIZE = 512
NUM_TO_DISPLAY = 10

for file_path in (DATA_PATH, SAMPLE_PATH, MODEL_PATH):
    if not file_path.exists():
        raise FileNotFoundError(f"Could not find{file_path.resolve}")
    
test_raw = np.loadtxt(DATA_PATH, delimiter = ",", skiprows = 1, dtype=np.uint8)
sample_rows = np.loadtxt(SAMPLE_PATH, delimiter = ",", skiprows=1, dtype=np.int64)

if test_raw.ndim != 2 or test_raw.shape[1] != 784:
    raise ValueError(f"Expected test data with 784 pixel columns, got shape{test_raw.shape}")
if sample_rows.ndim !=2 or sample_rows.shape[1]!= 2:
    raise ValueError(f"Esxpected two sample-submission columns, got shape {sample_rows.shape}")
if len(test_raw) != len(sample_rows):
    raise ValueError("test.csv and sample_submission.csv have different row counts.")

X_test = test_raw.astype(np.float32) / 255.0

with np.load(MODEL_PATH) as saved_model:
    W1 = saved_model["W1"]
    b1 = saved_model["b1"]
    W2 = saved_model["W2"]
    b2 = saved_model["b2"]
    
def predict_probabilities(inputs):
        z1 = inputs @ W1 + b1
        a1 = np.maximum(0.0, z1)
        z2 = a1 @ W2 + b2
        z2 -= np.max(z2, axis=1, keepdims=True)
        exp_scores = np.exp(z2)
        return exp_scores / np.sum(exp_scores, axis=1, keepdims=True)
    
predictions = np.empty(len(X_test), dtype=np.int64)
top_probabilities = np.empty(len(X_test), dtype=np.float32)
    
for start in range(0, len(X_test), BATCH_SIZE):
    end = min(start + BATCH_SIZE, len(X_test))
    batch_probabilities = predict_probabilities(X_test[start:end])
    predictions[start:end] = np.argmax(batch_probabilities, axis=1)
    top_probabilities[start:end] = np.max(batch_probabilities, axis=1)
        
submission = np.column_stack((sample_rows[:, 0], predictions))
np.savetxt(
    OUTPUT_PATH,
    submission,
    delimiter=",",
    fmt="%d",
    header="ImageId,Label",
    comments="",
    )

print(f"Loaded saved model: {MODEL_PATH}")
print(f"Predicted {len(predictions)} test images without retraining.")
print(f"Created kaggle-format predicitions: {OUTPUT_PATH}")

figure, axes = plt.subplots(2, 5, figsize=(12, 5))
for index, axis in enumerate(axes.flat):
    axis.imshow(X_test[index].reshape(28, 28))
    axis.set_title(
        f"Image {sample_rows[index, 0]} | Guess: {predictions[index]}\n"
        f"Top probability: {top_probabilities[index]:.1%}"
    )
    axis.axis("off")
    
figure.suptitle("Predictions on kaggle test images")
figure.tight_layout()
plt.show()

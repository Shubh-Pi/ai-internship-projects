import tkinter as tk

board = [""]* 9

root = tk.Tk()
root.title("TIC-TAC-TOE")

status  = tk.StringVar(value= "X's turn")
scores = {"X": 0, "O": 0, "Draws": 0}
score_text = tk.StringVar()

buttons = []

game_mode = tk.StringVar(value="Human vs AI")
current_player = "X"
game_id = 0

WIN_LINES = [
    (0,1,2), (3,4,5), (6,7,8), # Rows
    (0,3,6), (1,4,7), (2,5,8), # Columns
    (0,4,8), (2,4,6)           # Diagonals
]

def get_winner():
    for first, second, third in WIN_LINES:
        if board[first] and board[first] == board[second] == board [third]:
            return board[first]
    return None

def minimax(player, depth=0):
    winner = get_winner()
    
    if winner == "O":
        return 10-depth
    if winner == "X":
        return depth - 10
    if "" not in board:
        return 0
    
    scores = []
    
    for index in range(9):
        if board[index] == "":
            board[index] = player
            
            next_player = "X" if player == "O" else "O"
            scores.append(minimax(next_player, depth +1))
            
            board[index] = ""
            
    return max(scores) if player == "O" else min(scores)

def find_best_ai_move(player):
    best_score = float("-inf") if player == "O" else float("inf")
    best_move = None
    
    for index in range(9):
        if board[index] == "":
            board[index] = player
            
            next_player = "X" if player == "O" else "O"
            score = minimax(next_player, depth = 1)
            
            board[index] = ""
            
            if player == "O" and score > best_score:
                best_score = score
                best_move = index
            elif player == "X" and score < best_score:
                best_score = score
                best_move = index
    
    return best_move

def update_score_label():
    score_text.set(
        f"X wins: {scores['X']} |"
        f"O wins: {scores['O']} |"
        f"Draws: {scores['Draws']}"
    )
def finish_if_game_over():
    winner = get_winner()
    
    if winner:
        status.set(f"{winner} wins!")
        scores[winner] +=1
    elif "" not in board:
        status.set("It's a draw")
        scores["Draws"] +=1
    else:
        return False
    
    update_score_label()
    
    for button in buttons:
        button.config(state="disabled")
        
    return True

def take_ai_turn(this_game):
    global current_player
    
    if this_game != game_id:
        return
    
    player = current_player
    move = find_best_ai_move(player)
    board[move] = player
    buttons[move].config(text=player)
    
    if finish_if_game_over():
        return
    
    if game_mode.get() == "Human vs AI":
        current_player = "X"
        status.set("X's turn")
    else:
        current_player = "X" if player == "O" else "O"
        status.set(f"AI ({current_player}) is thinking...")
        root.after(500, take_ai_turn, this_game)
        
def reset_game(_selected_mode=None):
    global current_player, game_id
    
    game_id += 1
    current_player = "X"
    board[:] = [""] * 9
    
    for button in buttons:
        button.config(text="", state="normal")
        
    if game_mode.get() == "AI vs AI":
        status.set("AI (X) is thinking...")
        root.after(500, take_ai_turn, game_id)
    else:
        status.set("X's turn")
        
                
def display_move(index):
    global current_player
    
    if game_mode.get() != "Human vs AI":
        return
    if current_player != "X" or board[index] != "":
        return
    
    board[index] = "X"
    buttons[index].config(text="X")
    
    if finish_if_game_over():
        return
    
    current_player = "O"
    status.set("AI (O) is thinking...")
    root.after(250, take_ai_turn, game_id)
  
root.configure(bg="#f3f4f6")
tk.Label(root, text="Mode:", font=("Arial", 11), bg="#f3f4f6").grid(row=0, column=0, padx=8, pady=8)

tk.OptionMenu(
    root,
    game_mode,
    "Human vs AI",
    "AI vs AI",
    command=reset_game,
).grid(row=0, column=1, columnspan=2, pady=8)
      
tk.Label(root, textvariable=status, font=("Arial", 16, "bold"), bg="#f3f4f6").grid(
    row=1, column=0, columnspan=3, pady=8
)

tk.Label(
    root, textvariable=score_text, font=("Arial", 16, "bold"), bg="#f3f4f6"
).grid(row=2, column=0, columnspan=3, pady=5)

for index in range(9):
    button = tk.Button(
        root,
        text="",
        font=("Arial", 28),
        width=4,
        height=2,
        command=lambda cell=index: display_move(cell),
    )
    button.grid(row=3 + index // 3, column=index % 3, padx=3, pady=3)
    buttons.append(button)
    
tk.Button(
    root, text="New Game", font=("Arial", 11), command=reset_game,
).grid(row=6, column=0, columnspan=3, pady=10)

update_score_label()
    
root.mainloop()
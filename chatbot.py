import re
import random

INTENTS = {
    "AI": {
        "pattern": re.compile(
            r"\b(ai|artificial intelligence|machine learning|neural network|deep learning)\b"
        ),
        "replies":[
            "AI is the study of making computers perform tasks that usually need human intelligence.",
            "Machine learning is one part of AI: a program learns patterns from examples.",
            "A neural network learns by adjusting weights to reduce its prediction errors.",
        ],
    },
    "Python": {
            "pattern": re.compile(
                r"\b(python|numpy|matplotlib|programming|coding|code)\b"
            ),
            "replies":[
                "Python is a readable programming language. What are you trying to build with it?.",
                "NumPy is useful for working with arrays, while Matplotlib helps create plots.",
                "A good way to learn coding is to write a small piece, run it, and inspect the result.",
            ],
        },
    "Study tips": {
            "pattern": re.compile(
                r"\b(study|studying|exam|revision|revise|focus|remember|learning tips)\b"
            ),
            "replies":[
                "Try a focused 25-minute study block, then take a short break.",
                "After studying a topic, close your notes and explain the idea from memory.",
                "Break a large task into small steps and set a clear goal for each study session.",
            ],
        },
    "Project help": {
            "pattern": re.compile(
                r"\b(project|assignment|internship|deadline|presentation)\b"
            ),
            "replies":[
                "Break the project into input, processing, and output, and then build one part at a time.",
                "Start with the required features, get them working, and polish the presentation afterward.",
                "A short demo is easier to explain when you can describe what goes in and what comes out.",
            ],
        },
    "Sleep": {
        "pattern": re.compile(
            r"\b(sleep|bedtime|tired|rest)\b"
        ),
        "replies": [
            "A consistent sleep schedule can make it easier to get enough rest.",
            "Try winding down with a calm, screen-free routine before bed.",
            "Are you asking about a sleep routine or feeling tired during the day?"
        ],
    },
    "Water": {
        "pattern": re.compile(
            r"\b(water|hydration|drink|thirsty)\b"
        ),
        "replies": [
            "Keeping water nearby can remind you to drink throughout the day.",
            "You can make hydration a habit by drinking water with meals.",
            "Are you looking for a simple way to remember to drink water?",
        ],
    },
}

GREETING_PATTERN = re.compile(
    r"(hi|hello|hey)(there)?|good morning|good afternoon|good evening"
)

FALLBACK_REPLIES = [
    "I don't know that topic yet. Ask me about AI, Python, study tips, sleep, water, or project help.",
    "I'm not sure how to answer. Try mentioning AI, Python, studying, sleep, water, or a project.",
    "I can discuss AI, Python, study tips, sleep, water, and project help. Which one interests you?",
]

HELP_COMMANDS ={"help", "topics"}

EXIT_COMMANDS = {"bye", "goodbye", "exit", "quit"}

LAST_REPLY = {}

def get_response(user_text):
    text = user_text.casefold().strip()
    
    if not text:
        return "I didn't catch that. Please type a message."
    
    greeting_text = text.strip(" .!?")
    if GREETING_PATTERN.fullmatch(greeting_text):
        return random.choice(
            ["Hello! What would you like to talk about?", "HI there!", "Hey! ASk me about one of my topics."]
        ) 
        
    matching_topics = [
        topic_name
        for topic_name, topic_data in INTENTS.items()
        if topic_data["pattern"].search(text)
    ]    
    
    if len(matching_topics) == 1:
        topic_name = matching_topics[0]
        replies = INTENTS[topic_name]["replies"]
        
        previous_reply = LAST_REPLY.get(topic_name)
        available_replies = [reply for reply in replies if reply != previous_reply]
        
        chosen_reply = random.choice(available_replies)
        LAST_REPLY[topic_name] = chosen_reply
        return chosen_reply
        
    if len(matching_topics) > 1:
        topics = ",".join(matching_topics)
        return f"I spotted a few topics({topics}). Ask me about one at a time."
    
    return random.choice(FALLBACK_REPLIES)

def main():
    print("TopicBot: Hi! I can discuss AI, Python, study tips, sleep, water, and project help.")
    print("TopicBot: Type 'topics' to see the topics or 'bye' to leave.")
    
    while True:
        try:
            user_text = input("You:").strip()
        except(EOFError, KeyboardInterrupt):
            print("\nTopicBot: Goodbye!")
            break
        
        normalized_text = user_text.casefold()
        
        if normalized_text in EXIT_COMMANDS:
            print("TopicBot: Goodbye!")
            break
        
        if normalized_text in HELP_COMMANDS:
            print("TopicBot: I can discuss AI, python, study tips, sleep, water, and project help.")
            continue
        
        response = get_response(user_text)
        print("TopicBot:", response)
        
if __name__ == "__main__":
    main()


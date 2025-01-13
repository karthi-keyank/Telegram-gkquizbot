import nest_asyncio
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
import signal
import random
import json
import logging

nest_asyncio.apply()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# Load the JSON data from the file
with open(r"quizzes.json", "r") as file:
    data = json.load(file)

# Define states for conversation
QUIZ_LOOP = range(1)

class QuizBot:
    def __init__(self):
        self.points = {}

    def get_random_item(self):
        return random.choice(data)
 
quiz_instance = QuizBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = update.effective_user
    user_id = user.id
    username = user.username or "No username"
    first_name = user.first_name or "No first name"
    last_name = user.last_name or "No last name"

    # Save user details to a file
    with open("users.txt", "a") as file:
        file.write(f"{user_id}, {username}, {first_name}, {last_name}\n")

    logger.info(f"User ID: {user_id}, Username: {username}, Name: {first_name} {last_name}")


    quiz_instance.points[user_id] = 0
    await update.message.reply_text(f"Hello {first_name}! Welcome to the bot.")
    await update.message.reply_text(
        "Dai! Nadhanda Quiz Bot by karthi.\nType /quiz to start answering questions or /stop to exit."
    )
  
async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    quiz_instance.points[user_id] = quiz_instance.points.get(user_id, 0)
    await update.message.reply_text(
        "Let's start the quiz! Type /stop anytime to end the quiz."
    )
    return await ask_question(update, context)

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    question_data = quiz_instance.get_random_item()
    context.user_data["current_question"] = question_data

    question = question_data["question"]
    options = question_data["options"]
    option_text = "\n".join([f"{key}: {value}" for key, value in options.items()])

    await update.message.reply_text(
        f"Question: {question}\n\n{option_text}\n\nType 'z' for a clue (you lose 1 point)."
    )
    return QUIZ_LOOP

async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_points = quiz_instance.points.get(user_id, 0)
    user_answer = update.message.text.strip()
    question_data = context.user_data.get("current_question", {})

    if not question_data:
        await update.message.reply_text("No active question. Type /quiz to start.")
        return ConversationHandler.END

    correct_answer = question_data["answer"]
    clue = question_data["clue"]

    if user_answer.lower() == "z":
        user_points -= 1
        quiz_instance.points[user_id] = user_points
        await update.message.reply_text(f"Clue: {clue}\n\nEnter your answer:")
        return QUIZ_LOOP

    if user_answer.lower() == correct_answer:
        user_points += 4
        quiz_instance.points[user_id] = user_points
        await update.message.reply_text(f"Correct! Your points: {user_points}")
    else:
        await update.message.reply_text(
            f"Incorrect! The correct answer was: {correct_answer}\nYour points: {user_points}"
        )

    # Ask the next question
    return await ask_question(update, context)

async def stop_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_points = quiz_instance.points.get(user_id, 0)
    await update.message.reply_text(f"Thanks for playing! Your final score is: {user_points}")
    return ConversationHandler.END

async def main():
    application = Application.builder().token("7759064478:AAFrZ3kDgcksZxggsZdAyJTxDN8NbrBUG5s").build()

    # Define conversation handler
    quiz_handler = ConversationHandler(
        entry_points=[CommandHandler("quiz", start_quiz)],
        states={
            QUIZ_LOOP: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer)],
        },
        fallbacks=[CommandHandler("stop", stop_quiz)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(quiz_handler)

    # Start the bot
    await application.run_polling()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda signum, frame: asyncio.get_event_loop().stop())
    asyncio.run(main())

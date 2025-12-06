import asyncio
import json
import random

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile, KeyboardButton

from config import TOKEN, ADMINS, AUTHORIZED_USERS

bot = Bot(token=TOKEN)
dp = Dispatcher()

# =================
# Загрузка вопросов
# =================
# with open("questions.json", "r", encoding="utf-8") as f:
with open("questions_markdown_v2.json", "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

# =======================
# Сессии прохождения user
# =======================
user_state = {}
fail_message = [
    "🖕 Дружище, ты бля реально НЕ ПРАВ\\.",
    "😝 А\\-а, сука, не попал, как в тире на похмелье\\!",
    "😤 День прошел, число сменилось, нихуя не изменилось\\!\nМимо, бля, внимательнее надо\\!",
    "😡 Да ебаный рот\\. Давай, не унывай, второй заход\\!",
    "😭 Братан, ну ты и лошара\\. Подумай, а не паникуй\\!",
    "💩 Фуфло полное, как просрочка в ларьке\\."
]
success_message = [
    "😇 Братан, уважение тебе\\. КРАСАВА \\!\\!\\!",
    "👊 Вот это, сука, в точку\\! Молодца, братан\\!",
    "😉 Вот так надо, мать твою, чисто угадал\\!",
    "💯 Не, пацан, это топчик\\! Прямо уважуха\\!",
    "🔥 Охуенно, чувак\\. Ты сечешь в теме\\!\\!\\!",
    "💪 Да ты АХУЕННЫЙ тип\\!\\!\\! Респект\\."

]
welcome_text = (
    "😎 Эй, чувачок\\! 🕶️\n"
    "Квиз стартует — телефон должен быть полный, иначе хер тебе, а не клад\\.\n"
    "Не зарядил\\? С нуля начинаешь, и никто не спасёт\\.\n"
    "Врубай мозги, жми кнопки, покажи кто тут реальный пацан\\!"
)

# =================
# Проверка доступа
# =================
def is_allowed(user_id):
    return user_id in AUTHORIZED_USERS or user_id in ADMINS

# =================
# Главное меню
# =================
main_kb = types.ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Погнали"), KeyboardButton(text="Админ")]
    ],
    resize_keyboard=True,
)

# ======
# Start
# ======
@dp.message(Command("start"))
async def start_cmd(message: Message):
    if not is_allowed(message.from_user.id):
        await message.answer("⛔ Извини, братуха. Это дело не для тебя. Подрасти :)")
        return

    # user_state[message.from_user.id] = {'current': 0, 'step': 0}
    if not user_state.get(message.from_user.id):
        await message.answer(welcome_text, parse_mode='MarkdownV2')
        await message.answer(
            "💥 Эй, братан! Выбери режим:",
            reply_markup=main_kb
        )
    # await send_question(message.from_user.id)


# ==========
# Admin
# ==========
@dp.message(Command("admin"))
async def admin_cmd(message: Message):
    await admin_panel(message)

async def admin_panel(message: Message):
    if message.from_user.id not in ADMINS:
        await message.answer("⛔ Братан извини, но хуй ты сюда попадешь. ТЫ НЕ ПРОЙДЕШЬ !!!")
        return

    await message.answer("Привет, босс! ⚡ Здесь твои админские функции.", reply_markup=types.ReplyKeyboardRemove())

    text = "📋 Список вопросов:\n\n"
    for q in QUESTIONS:
        text += f"ID: {q['id']} | Question: {q['question'][:100]}...\n"
        if q.get('answer'):
            text += f"ОТВЕТ: {q['answer']}\n\n"

    await message.answer(text)


# ========================
# Обработка выбора кнопок
# ========================
@dp.message(lambda message: message.text in ["Погнали", "Админ"])
async def menu_choice(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    state = user_state.get(user_id)

    if message.text == "Админ":
        if user_id in ADMINS:
            await admin_panel(message)
            return

            # await message.answer("Привет, босс! ⚡ Здесь твои админские функции.", reply_markup=types.ReplyKeyboardRemove())
            # # Показываем список вопросов
            # text = "📋 Список вопросов:\n\n"
            # for q in QUESTIONS:
            #     text += f"ID: {q['id']} | Question: {q['question'][:100]}...\n"
            #     if q.get('answer'):
            #         text += f"ОТВЕТ: {q['answer']}\n\n"
            # await message.answer(text)

        # else:
        #     await message.answer("🚫 Ты не админ, братан!", reply_markup=types.ReplyKeyboardRemove())
        # return

    elif message.text == "Погнали":

        if not state:
            user_state[user_id] = {'current': 0, 'step': 0}
            state = user_state[user_id]

        elif user_id not in ADMINS:
            if state and state['current'] < len(QUESTIONS):
                await message.answer("⛔ Братан, ты уже в квизе. Заканчивай текущий, потом сможешь выбрать меню.")
                return
            else:
                # Квиз был завершён → сбрасываем и начинаем заново
                user_state[user_id] = {'current': 0, 'step': 0}
                state = user_state[user_id]

        else:
            # Если админ - рестарт разрешен всегда
            user_state[user_id] = {'current': 0, 'step': 0}
            state = user_state[user_id]

        await message.answer(
            "🎮 Начинаем кутеж !!! 🕺",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await send_question(user_id)

# =================
# Отправка вопроса
# =================
async def send_question(user_id):
    state = user_state[user_id]
    q_idx = state['current']
    q = QUESTIONS[q_idx]

    # ==== ЛОГ В КОНСОЛЬ ====
    print(f"[LOG] Пользователю {user_id} отправлен вопрос #{q_idx + 1}: {q['question']}")
    # =======================

    if q["type"] == "single":
        await bot.send_message(user_id, q["question"], parse_mode="MarkdownV2")

    elif q["type"] == "image":
        photo = FSInputFile(f"data/images/{q['image']}")
        await bot.send_photo(user_id, photo, caption=q["question"], parse_mode="MarkdownV2")

    elif q["type"] == "multistep":
        step = state["step"]

        # Логируем шаг вопроса
        print(f"[LOG]   └ step {step + 1}/{len(q['steps'])}: {q['steps'][step]['question']}")

        if step == 0:
            await bot.send_message(user_id, q["question"], parse_mode="MarkdownV2")
        await bot.send_message(user_id, q["steps"][step]["question"], parse_mode="MarkdownV2")

# =======================
#      ОБРАБОТКА ОТВЕТОВ
# =======================
@dp.message(F.text)
async def process_answer(message: Message):
    user_id = message.from_user.id
    state = user_state.get(user_id)
    text = message.text.strip()

    # ===== ЛОГ ОТВЕТА =====
    if state:
        q_idx = state['current']
        if q_idx < len(QUESTIONS):
            q = QUESTIONS[q_idx]
            print(f"[LOG] Ответ от {user_id}: '{text}' (вопрос #{q_idx + 1}: '{q['question'][:50]}')")
    else:
        print(f"[LOG] Ответ от {user_id}, но квиз не начат: '{text}'")
    # ======================

    # Если нет прогресса или пользователь не стартанул квиз
    if text in ["Погнали", "Админ"] or text.startswith("/"):
        return

    if not state or state['current'] >= len(QUESTIONS):
        # Игнорируем команды меню
        await message.answer("Братан, сначала нажми 'Погнали' чтобы стартовать квиз.")
        return

    if not is_allowed(user_id):
        await message.answer("⛔ Братан извини. Это дело не для тебя. Подрасти :)")


    q_idx = state['current']
    q = QUESTIONS[q_idx]

    # ------------------ SINGLE ------------------
    if q["type"] == "single":
        if text.lower() in q["answer"]:
            await message.answer(random.choice(success_message), parse_mode="MarkdownV2")
            if q.get('info') and q.get('info') != "":
                await message.answer(f"{q["info"]}", parse_mode="MarkdownV2")
            state["current"] += 1
            state["step"] = 0

            # Проверяем: вопросы закончились
            if state["current"] >= len(QUESTIONS):
                await send_video(user_id, fail=False)
                await message.answer(
                    "🎉🎉🎉 Братан, ты прошёл все вопросы!\nНайдите свой схрон и отпразднуйте с братками на всю катушку !!!\n🎉🎉🎉")
                await message.answer(
                    "🎉🎉🎉 Респект вам и уважуха. Теперь двигайтесь в хату – в баньку.\nЭтот клад уже у себя дома откроете. Но будьте осторожны, там лежит одно очень хрупкое дело.\nНе уроните малину !!!🎉🎉🎉")

                del user_state[user_id]
                return

        else:
            # await send_video(user_id)
            await message.answer(random.choice(fail_message), parse_mode="MarkdownV2")

        await send_question(user_id)
        return

    # ------------------ IMAGE -------------------
    if q["type"] == "image":
        if text.lower() in q["answer"]:
            await message.answer(random.choice(success_message), parse_mode="MarkdownV2")
            if q.get('info') and q.get('info') != "":
                await message.answer(f"{q["info"]}", parse_mode="MarkdownV2")
            state["current"] += 1
            state["step"] = 0

            # Проверяем: вопросы закончились
            if state["current"] >= len(QUESTIONS):
                await send_video(user_id, fail=False)
                await message.answer(
                    "🎉🎉🎉 Братан, ты прошёл все вопросы!\nНайдите свой схрон и отпразднуйте с братками на всю катушку !!!\n🎉🎉🎉")
                await message.answer(
                    "🎉🎉🎉 Респект вам и уважуха. Теперь двигайтесь в хату – в баньку.\nЭтот клад уже у себя дома откроете. Но будьте осторожны, там лежит одно очень хрупкое дело.\nНе уроните малину !!!🎉🎉🎉")

                del user_state[user_id]
                return

        else:
            await message.answer(random.choice(fail_message), parse_mode="MarkdownV2")

        await send_question(user_id)
        return

    # ---------------- MULTISTEP -----------------
    if q["type"] == "multistep":
        step = state["step"]
        if text.lower() == q["steps"][step]["answer"].lower():
            state["step"] += 1

            if state["step"] >= len(q["steps"]):
                await message.answer("✔ Чики\\-брики и в дамки\\!\\!\\!\n" + q["info"], parse_mode="MarkdownV2")
                await send_video(user_id, fail=False)
                state["current"] += 1
                state["step"] = 0

                # Проверяем: вопросы закончились
                if state["current"] >= len(QUESTIONS):
                    await send_video(user_id, fail=False)
                    await message.answer("🎉🎉🎉 Братан, ты прошёл все вопросы!\nНайдите свой схрон и отпразднуйте с братками на всю катушку !!!\n🎉🎉🎉")
                    await message.answer("🎉🎉🎉 Респект вам и уважуха. Теперь двигайтесь в хату – в баньку.\nЭтот клад уже у себя дома откроете. Но будьте осторожны, там лежит одно очень хрупкое дело.\nНе уроните малину !!!🎉🎉🎉")
                    del user_state[user_id]
                    return

        else:
            await message.answer(q["fail_message"], parse_mode="MarkdownV2")
            # await send_video(user_id, fail=False, multi=True)
            state["step"] = 0

        await send_question(user_id)
        return

    # На всякий случай, если type неизвестен
    await message.answer("❌ Неизвестный тип вопроса")
    return

# ===============
# Отправка Video
# ===============
async def send_video(user_id, fail: bool = True, multi: bool = False):
    video_fail_path_list = [
        "fail_1.mp4",
        "fail_2.mp4",
        "fail_3.mp4",
        "fail_4.mp4",
        "fail_5.mp4",
        "fail_6.mp4",
        "fail_7.mp4",
        "fail_8.mp4",
        "fail_9.mp4",
        "fail_10.mp4",
    ]
    video_success_path_list = [
        "success_1.mp4",
    ]
    video_fail_multi_path_list = [
        "fail_multisteps.mp4",
    ]

    if multi:
        video_path = f"data/video/{random.choice(video_fail_multi_path_list)}"
    elif fail:
        video_path = f"data/video/{random.choice(video_fail_path_list)}"
    else:
        video_path = f"data/video/{random.choice(video_success_path_list)}"

    video_file = FSInputFile(path=video_path)
    await bot.send_video(chat_id=user_id, video=video_file)


# =====
# Main
# =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
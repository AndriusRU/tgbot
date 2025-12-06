import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('API_TOKEN')

# Пользователи, которым разрешён доступ
users_str = os.getenv('AUTHORIZED_USERS')
AUTHORIZED_USERS = [int(x) for x in users_str.split(',') if x.strip()]

# ID организаторов
admins_str = os.getenv('ADMINS')
ADMINS = [int(x) for x in admins_str.split(',') if x.strip()]
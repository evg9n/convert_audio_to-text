# Логгер
from os import listdir, path
from time import time, sleep

from loguru import logger
from requests import get, post
from rev_ai import JobStatus
from rev_ai.apiclient import RevAiAPIClient

from os.path import abspath, join
# Константы
from constants import Constants

constants = Constants()
logger.remove()
logger.add(
    abspath(join('logs', '{time:YYYY-MM-DD  HH.mm.ss}.log')),  # Путь к файлу логов с динамическим именем
    rotation=constants.ROTATION_LOGGER,  # Ротация логов каждый день
    compression="zip",  # Использование zip-архива
    level=constants.LEVEL_FILE_LOGGER,  # Уровень логирования
    format=constants.FORMAT_LOGGER,  # Формат вывода
    serialize=constants.SERIALIZE_LOGGER,  # Сериализация в JSON
)

# Вывод лога в консоль
logger.add(
    sink=print,
    level=constants.LEVEL_CONSOLE_LOGGER,
    format=constants.FORMAT_LOGGER,
)


def decorator_time_work(func):
    """
    Декоратор для опредления времени работы функции
    """
    def wrapper(*args, **kwargs):
        start = time()

        func(*args, **kwargs)

        stop = time()
        all_time = round(stop - start, 2)

        hour = int(all_time / 60 // 60)
        minutes = int(all_time // 60 - 60 * hour)
        seconds = int(round(all_time - (hour * 60 * 60 + minutes * 60), 0))

        hour = hour if hour > 9 else f"0{hour}"
        minutes = minutes if minutes > 9 else f"0{minutes}"
        seconds = seconds if seconds > 9 else f"0{seconds}"

        print(f"Выполнено за {hour}:{minutes}:{seconds}")

    return wrapper


def send(client: RevAiAPIClient, path_file: str, language: str) -> str | None:

    # отправка локального файла
    job = client.submit_job_local_file(path_file, language=language)
    job_id = job.id
    logger.debug(f'{path_file} отправлен на обработку. id задачи {job_id}')

    return job_id


def check_status(client: RevAiAPIClient, job_id: str) -> str | None:
    while True:
        # проверить статус задания
        job_details = client.get_job_details(job_id)
        logger.debug(f"{job_details.status}")

        if job_details.status == JobStatus.TRANSCRIBED:
            # получить расшифровку в виде текста
            transcript_text = client.get_transcript_text(job_id)
            logger.info(f'{job_id} - Готово')
            return transcript_text

        elif job_details.status == JobStatus.IN_PROGRESS:
            logger.debug(f'{job_id} Еще ждем')
            sleep(10)
            continue

        else:
            logger.error(f'{job_details}')
            logger.error('Не удалось')

        return


@decorator_time_work
def main():
    # создание клиента
    client = RevAiAPIClient(constants.REV_TOKEN)
    path_get = path.abspath('media')
    list_file = listdir(path_get)
    list_results = listdir(path.abspath('results'))
    path_save = path.abspath('results')
    for file in list_file:
        if (file.endswith('.txt') or file.replace('.mp3', '.txt') in list_results or
                file.replace('.ogg', '.txt') in list_results or
                file.replace('.mp4', '.txt') in list_results):
            continue
        path_file = path.join(path_get, file)
        job_id = send(client, path_file, 'ru')
        result = check_status(client, job_id)
        if result:
            with open(path.join(path_save, file[:-4] + ".txt"), 'w',
                      encoding='utf-8') as f:
                f.write(result)
        else:
            print(f'файл {path_file} не удалось распознать')


if __name__ == '__main__':
    logger.info('RUN PROJECT')
    main()

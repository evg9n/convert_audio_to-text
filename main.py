# Логгер
from os import listdir, path
from time import time, sleep

from loguru import logger
from requests import get, post
from rev_ai import apiclient, JobStatus

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


def check(job_id: str):
    url = f"https://api.rev.ai/speechtotext/v1/jobs/{job_id}/transcript"
    headers = {
        "Authorization": f"Bearer {constants.REV_TOKEN}",  # Замените <REVAI_ACCESS_TOKEN> на ваш токен доступа
        "Accept": "text/plain"
    }
    response = get(url, headers=headers)
    return response


def send_file():
    url = "https://api.rev.ai/speechtotext/v1/jobs"
    headers = {
        "Authorization": f"Bearer {constants.REV_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "source_config": {"url": "https://www.rev.ai/FTC_Sample_1.mp3"},
        "metadata": "This is a test"
    }

    response = post(url, headers=headers, json=data)
    # print(response)
    # print(response.text)
    return response


def get_result(job_id: str):
    url = f"https://api.rev.ai/speechtotext/v1/jobs/{job_id}/transcript"
    headers = {
        "Authorization": f"Bearer {constants.REV_TOKEN}",  # Замените <REVAI_ACCESS_TOKEN> на ваш токен доступа
        "Accept": "text/plain"
    }

    response = get(url, headers=headers)
    # print(response.text)
    return response


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


def send(path_file: str):
    # create your client
    client = apiclient.RevAiAPIClient(constants.REV_TOKEN)

    # send a local file
    job = client.submit_job_local_file(path_file, language='ru')
    # logger.debug(job)

    sleep(30)
    while True:
        # проверить статус задания
        job_details = client.get_job_details(job.id)
        # logger.info(job_details.failure_detail())
        if job_details.status == JobStatus.TRANSCRIBED:
            # получить расшифровку в виде текста
            transcript_text = client.get_transcript_text(job.id)
            return transcript_text
        elif job_details.status == JobStatus.IN_PROGRESS:
            sleep(10)
            continue
        else:
            logger.error(f'{job_details}')
            logger.error('Не удалось')

        return


@decorator_time_work
def main():
    list_file = listdir(path.abspath('media'))
    list_results = listdir(path.abspath('results'))
    path_save = path.abspath('results')
    for file in list_file:
        if (file.endswith('.txt') or file.replace('.mp3', '.txt') in list_results or
                file.replace('.ogg', '.txt') in list_results or
                file.replace('.mp4', '.txt') in list_results):
            continue
        path_file = path.abspath(path.join('results', file))
        result = send(path_file)
        if result:
            with open(path.join(path_save, path_file.replace(file[-4:], '.txt')), 'w',
                      encoding='utf-8') as f:
                f.write(result)
        else:
            print(f'файл {path_file} не удалось распознать')


if __name__ == '__main__':
    logger.info('RUN PROJECT')
    main()

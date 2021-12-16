import logging
from asyncio import CancelledError
from pathlib import Path
import argparse

import asyncio
from aiohttp import web
import aiofiles

from settings import DEBUG_MODE, MEDIA_DIR, DEFAULT_BYTES_FOR_READ, INTERVAL_SECS


parser = argparse.ArgumentParser(description="async-zipper")
parser.add_argument('--path')
parser.add_argument('--port')
logger = logging.getLogger(__name__)
if DEBUG_MODE:
    logging.basicConfig(level=logging.DEBUG)


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


async def archivate(request):
    response = web.StreamResponse()

    # Большинство браузеров не отрисовывают частично загруженный контент, только если это не HTML.
    # Поэтому отправляем клиенту именно HTML, указываем это в Content-Type.
    archive_hash = request.match_info.get('archive_hash')
    response.headers['Content-Disposition'] = f'filename = "{archive_hash}.zip"'

    path_to_archive = Path(MEDIA_DIR, f'{archive_hash}')
    if not path_to_archive.exists() or not path_to_archive.is_dir() or not archive_hash:
        raise web.HTTPNotFound()
    cmd = f"zip -r - * | cat"
    proc = await asyncio.create_subprocess_shell(
        cmd,
        cwd=path_to_archive.as_posix(),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    # Отправляет клиенту HTTP заголовки
    await response.prepare(request)
    stdout = proc.stdout

    try:
        while not stdout.at_eof():
            logger.info('start read bytes')
            stdout_bytes = await stdout.read(DEFAULT_BYTES_FOR_READ)
            # Отправляет клиенту очередную порцию ответа
            logger.info(f'[Sending archive chunk ... ] {len(stdout_bytes)}')

            await response.write(stdout_bytes)
            if INTERVAL_SECS:
                await asyncio.sleep(INTERVAL_SECS)

        return response
    except CancelledError:
        logger.info('Download was interrupted')
    except Exception as e:
        logger.exception(f'Unexpected exception caught {e}')
    finally:
        proc_pid = proc.pid
        # kill child processes
        kill_proc = await asyncio.create_subprocess_shell(
            f'./rkill.sh {proc_pid}',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await kill_proc.wait()
        if proc.returncode is None:
            logger.info(f'Kill {proc_pid}')
            proc.kill()
            outs, errs = proc.communicate()


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([
        web.get('/archive/{archive_hash}/', archivate),
        web.get('/', handle_index_page),

    ])
    args = parser.parse_args()
    web.run_app(app, path=args.path, port=args.port)

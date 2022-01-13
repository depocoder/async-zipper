import os
from asyncio import CancelledError
from pathlib import Path

import asyncio
from aiohttp import web
import aiofiles

from utils import create_logger, create_parser
from settings import DEFAULT_BYTES_FOR_READ, INTERVAL_SECS, MEDIA_DIR

parser = create_parser()
logger = create_logger()


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


async def archivate(request):
    response = web.StreamResponse()

    # Большинство браузеров не отрисовывают частично загруженный контент, только если это не HTML.
    # Поэтому отправляем клиенту именно HTML, указываем это в Content-Type.
    archive_hash = request.match_info['archive_hash']
    response.headers['Content-Disposition'] = f'filename = "{archive_hash}.zip"'

    path_to_archive = Path(app['media_dir'], f'{archive_hash}')
    if not path_to_archive.exists() or not path_to_archive.is_dir():
        raise web.HTTPNotFound()
    cmd = 'zip', '-r', '-', '.',
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=path_to_archive.as_posix(),
        stdout=asyncio.subprocess.PIPE,)

    # Отправляет клиенту HTTP заголовки
    await response.prepare(request)
    response.enable_chunked_encoding()
    stdout = proc.stdout

    try:
        while not stdout.at_eof():
            logger.debug('start read bytes')
            stdout_bytes = await stdout.read(DEFAULT_BYTES_FOR_READ)
            # Отправляет клиенту очередную порцию ответа
            logger.debug(f'[Sending archive chunk ... ] {len(stdout_bytes)}')

            await response.write(stdout_bytes)
            if INTERVAL_SECS:
                await asyncio.sleep(INTERVAL_SECS)

        return response
    except CancelledError:
        logger.debug('Download was interrupted')
        raise
    except Exception as e:
        logger.debug(f'Unexpected exception caught {e}', exc_info=True)
        raise
    finally:
        proc.kill()
        outs, errs = proc.communicate()


if __name__ == '__main__':
    app = web.Application()
    app['media_dir'] = MEDIA_DIR
    app.add_routes([
        web.get('/archive/{archive_hash}/', archivate),
        web.get('/', handle_index_page),

    ])
    args = parser.parse_args()
    web.run_app(app, path=args.path, port=args.port)

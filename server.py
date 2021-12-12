import asyncio
from aiohttp import web
import aiofiles
from pathlib import Path


INTERVAL_SECS = 1
DEFAULT_BYTES_FOR_READ = 1024 * 1024 * 8


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

    path_to_archive = Path(f'test_photos/{archive_hash}')
    if not path_to_archive.exists() or not path_to_archive.is_dir() or not archive_hash:
        raise web.HTTPNotFound()
    cmd = f"zip -r - {path_to_archive} | cat"
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    # Отправляет клиенту HTTP заголовки
    await response.prepare(request)

    stdout = proc.stdout
    while not stdout.at_eof():
        stdout_bytes = await stdout.read(DEFAULT_BYTES_FOR_READ)

        if stdout:
            print(f'[stdout]\n{len(stdout_bytes)}')
        # Отправляет клиенту очередную порцию ответа
        await response.write(stdout_bytes)
        await asyncio.sleep(INTERVAL_SECS)
    return response


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([
        web.get('/archive/{archive_hash}/', archivate),
        web.get('/', handle_index_page),

    ])
    web.run_app(app)


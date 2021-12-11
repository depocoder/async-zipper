import asyncio
import uuid


FILE_NAME = uuid.uuid1()


async def arhivate(path_to_folder):
    cmd = f"zip -r - {path_to_folder} | cat"
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    print(f'[{cmd!r} exited with {proc.returncode}]')
    stdout = proc.stdout
    while not stdout.at_eof():
        stdout_bytes = await stdout.read(10)

        if stdout:
            print(f'[stdout]\n{stdout_bytes}')
        with open(f'{FILE_NAME}.zip', 'ab') as file:
            file.write(stdout_bytes)


if __name__ == '__main__':
    asyncio.run(arhivate('folder_for_zip/'))
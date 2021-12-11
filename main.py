import asyncio

async def arhivate(path_to_folder):
    cmd = f"zip -r - {path_to_folder} | cat"
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    print(f'[{cmd!r} exited with {proc.returncode}]')
    if stdout:
        print(f'[stdout]\n{stdout}')
    if stderr:
        print(f'[stderr]\n{stderr.decode()}')
    with open('some.zip', 'wb') as file:
        file.write(stdout)



if __name__ == '__main__':
    asyncio.run(arhivate('folder_for_zip/'))
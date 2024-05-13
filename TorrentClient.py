import asyncio
import threading


class Torrent:
    def __init__(self):
        self.lines = []
        self.lock = threading.Lock()
        self.torrent_name = ""
        self.path = ""
        self.speed = ""
        self.downloaded = ""
        self.uploaded = ""
        self.running_time = ""
        self.remaining_time = ""
        self.peers = ""
        self.running = False

    async def run_webtorrent_command(self, command):
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            while True:
                stdout = await process.stdout.readline()
                if not stdout:
                    break
                yield stdout.decode().strip()
            await process.wait()
        except Exception as e:
            yield str(e)

    async def get_torrent_status(self, command):
        command = f'webtorrent {command} -o "$HOME/Downloads"'
        async for output_line in self.run_webtorrent_command(command):
            with self.lock:
                if output_line != "":
                    self.lines.append(output_line)
                    if "Downloading:" in output_line:
                        self.torrent_name = output_line.split("Downloading: ")[1]
                    elif "Downloading to:" in output_line:
                        self.path = output_line.split("Downloading to: ")[1]
                    elif "Speed:" in output_line:
                        split_by_space = output_line.split()
                        self.speed = split_by_space[1] + " " + split_by_space[2]
                        self.downloaded = split_by_space[4] + " " + split_by_space[5] + " " + split_by_space[6]
                        self.uploaded = split_by_space[8] + " " + split_by_space[9]
                    elif "Running time:" in output_line:
                        split_by_space = output_line.split()
                        self.running_time = split_by_space[2] + " " + split_by_space[3]
                        self.remaining_time = output_line.split("Peers:")[0].split()[6::]
                        self.peers = output_line.split("Peers:")[1]
                if output_line == "webtorrent is exiting...":
                    self.running = False
                    return

    async def start_monitoring(self, command):
        if not self.running:
            self.running = True
            while self.running:
                await self.get_torrent_status(command)
                await asyncio.sleep(1)

    def stop_monitoring(self):
        self.running = False

    def get_info(self):
        return {"torrent name": self.torrent_name,
                "path": self.path,
                "speed": self.speed,
                "downloaded": self.downloaded,
                "uploaded": self.uploaded,
                "running_time": self.running_time,
                "remaining_time": self.remaining_time,
                "peers": self.peers}


class TorrentManager:
    def __init__(self):
        self.torrents = []
        self.lock = threading.Lock()
        self.active_torrents = 0
        self.tasks = []

    def add_torrent(self, command):
        new_torrent = Torrent()
        task = asyncio.create_task(new_torrent.start_monitoring(command))
        self.tasks.append(task)
        self.torrents.append(new_torrent)
        self.active_torrents += 1

    def get_all_info(self):
        info = {'data': []}
        for torrent in self.torrents:
            info['data'].append(torrent.get_info())
        return info

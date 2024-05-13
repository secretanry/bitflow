from quart import Quart, jsonify, request
from TorrentClient import TorrentManager

app = Quart(__name__)
torrent_manager = TorrentManager()


@app.route('/add_torrent', methods=['POST'])
async def add_torrent():
    data = await request.get_json()
    link = data.get('link')
    if link:
        torrent_manager.add_torrent(command=link)
        return jsonify({"message": "Torrent added successfully"}), 200
    else:
        return jsonify({"error": "Torrent link is missing"}), 400


@app.route('/list_torrents', methods=['GET'])
async def list_torrents():
    torrents = torrent_manager.get_all_info()
    return jsonify(torrents), 200


if __name__ == '__main__':
    app.run(port=5000, debug=True)

import hashlib
import qrcode
from flask import Flask, request, send_file, Response
from markupsafe import escape
from sqlitedict import SqliteDict
from io import BytesIO

mydict = SqliteDict('./my_db.sqlite', autocommit=True)
app = Flask(__name__)
app.debug = True

@app.route('/api/bookmarks', methods=['POST'])
def create_bookmarks():
    content = request.get_json()
    id = hashlib.sha224(str.encode(content['url'])).hexdigest()
    if id in mydict.keys():
        return {'reason': "The given URL already existed in the system."}, 400
    mydict[id] = { 'id': id, 'name': content['name'], 'url': content['url'], 'description': content['description'], 'count': 0}
    return {'id': id}, 201

@app.route('/api/bookmarks/<bookmark_id>/qrcode', methods=['GET'])
def get_bookmark_qrcode(bookmark_id):
    bookmark_id = escape(bookmark_id)
    if mydict.get(bookmark_id):
        bookmark = mydict.get(bookmark_id)
        pil_img = qrcode.make(bookmark['url'])
        img_io = BytesIO()
        pil_img.save(img_io, 'PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png')
    else:
        return {'reason': "Not Found"}, 404

@app.route('/api/bookmarks/<bookmark_id>/stats', methods=['GET'])
def get_bookmark_stats(bookmark_id):
    bookmark_id = escape(bookmark_id)
    etag = request.headers.get('Etag')
    if mydict.get(bookmark_id):
        bookmark = mydict.get(bookmark_id)
        count = str(bookmark['count'])
        if etag == count:
            return Response(headers={'Etag':count}, status=304)
        else:
            return Response(headers={'Etag':count}, status=200, response=count)
    else:
        return {'reason': "Not Found"}, 404

@app.route('/api/bookmarks/<bookmark_id>', methods=['GET', 'DELETE'])
def get_or_delete_bookmark(bookmark_id):
    bookmark_id = escape(bookmark_id)
    if request.method == 'GET':
        if mydict.get(bookmark_id):
            bookmark = mydict.get(bookmark_id)
            bookmark['count'] += 1
            mydict[bookmark_id] = bookmark
            return bookmark, 200
        else:
            return {'reason': "Not Found"}, 404
    else:
        del mydict[bookmark_id]
        return '', 204

if __name__ == '__main__':
    app.run(debug=True)
import os, time, datetime
from hurry.filesize import size
from flask import jsonify, send_from_directory


class Logs:
    def __init__(self, log_dir):
        self.__log_dir = log_dir

    def process(self, request, user):
        user_id = user.id

        if user.is_admin():
            user_id = request.args.get('user-id')

        user_log_dir = os.path.join(self.__log_dir, 'user-logs', str(user_id))

        file = request.args.get('file')

        if file is not None and len(file) > 0:
            return send_from_directory(directory=user_log_dir, filename=file)

        if not os.path.exists(user_log_dir):
            return jsonify([])

        user_log_files = os.listdir(user_log_dir)

        if not user_log_files:
            return jsonify([])

        log_files = []

        for log_file in user_log_files:
            file_path = os.path.join(user_log_dir, log_file)
            file_c_time = time.ctime(os.path.getctime(file_path))
            log_files.append({
                'log file': log_file,
                'date': datetime.datetime.strptime(file_c_time, "%a %b %d %H:%M:%S %Y"),
                'size': size(os.path.getsize(file_path)),
            })

        return jsonify(log_files)

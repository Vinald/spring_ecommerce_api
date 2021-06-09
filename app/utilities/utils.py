def error(msg, e):
    return {'status': 'error', 'message': f'{msg}: {str(e)}'}


def error_message(msg):
    return {'status': 'error', 'message': msg}


def success(msg):
    return {'status': 'success', 'message': msg}


def un_auth():
    return {'msg': 'This operation will be reported'}, 401

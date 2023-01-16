from datetime import datetime

def get_current_time() -> str:
    return str(datetime.now()).split('.')[0].replace(':', '-')

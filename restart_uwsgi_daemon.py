#どうもdaemonが落ちてしまうことがあるので、それを検知したら再起動するようなプログラムを作成します。
#daemonizeするために　nohup python3 restart_uwsgi_daemon.py > restart_uwsgi_daemon.out 2>&1 &　を実行してこれを動作させてください
import subprocess
import time 
import os
os.chdir("/usr/local/git/Yuruyuru_Search/") #subprocessではcdは変更できない
while True:
    ret = subprocess.run(["ps", "aux"], capture_output=True, text=True).stdout
    ret_lies = ret.split("\n")
    _isActive = False
    for l in ret_lies:
        # print(l)
        if all([word in l for word in ["uwsgi","--ini","wsgi.ini"]]):
            _isActive=True
            break
    
    if not _isActive:
        ret = subprocess.run(["uwsgi", "--ini","wsgi.ini"], capture_output=True, text=True).stdout
        print(ret)
    else:
        # print("_isActive")
        time.sleep(5)
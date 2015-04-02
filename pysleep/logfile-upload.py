__author__ = 'dano'
import os
from socket import error as socket_error
from ftplib import FTP, error_perm as permission_error
import glob

from pysleep.pysleeplogging import log


MIN_SIZE_FOR_UPLOAD = 1000000

def upload_new_logfiles(hostname=None, user=None, password=None):

    """
    Global function which quickly scans for log files which exist locally, but not on the remote fileserver.
    Any files which meet the criteria are uploaded, then removed locally.

    Uploaded files are sent to a remote fileserver via FTP. The credentials and hostnames are gathered in the following
    prioritized order:
    1.) passed in via function calls
    2.) in the file credentials.py
    3.) in the file settings.py
    """
    if hostname is None:
        try:
            from settings import HOSTNAME as hostname
        except ImportError:
            try:
                from default_settings import HOSTNAME as hostname
            except ImportError:
                log.warning("No hostname provided in function call, credentials file, or default credentials file")
                return

    if user is None:
        try:
            from settings import USER as user
        except ImportError:
            try:
                from default_settings import USER as user
            except ImportError:
                log.warning("No user provided in function call, credentials file, or default credentials file")
                return

    if password is None:
        try:
            from settings import PASSWORD as password
        except ImportError:
            try:
                from default_settings import PASSWORD as password
            except ImportError:
                log.warning("No password provided in function call, credentials file, or default credentials file")
                return


    # Setup FTP
    log.info("Connecting to FTP site")
    try:
        ftp = FTP(timeout=5)
        ftp.connect(hostname)
        log.info("FTP Connected")
        ftp.login(user, password)
        ftp.cwd('logs')

        sleep_logs = glob.glob('./logs/*.slp.csv')
        log.info("Found local logfiles: %s" % sleep_logs)
        for sleep_log in sleep_logs:
            sleep_log_filename = os.path.basename(sleep_log)
            if os.stat(sleep_log).st_size < MIN_SIZE_FOR_UPLOAD:
                log.info("Skipping %s: sleeplog is < %s bytes " % (sleep_log_filename, MIN_SIZE_FOR_UPLOAD))
                continue

            # Check if file is already on the server
            files_on_server = []
            ftp.retrlines('LIST %s' % sleep_log_filename, files_on_server.append)
            if files_on_server:
                log.info("Skipping %s: sleeplog is already on server" % sleep_log_filename, MIN_SIZE_FOR_UPLOAD)
                continue

            # If not, upload it
            log.info("Uploading %s" % sleep_log_filename)
            opened_sleep_log = open(sleep_log)
            transfer_cmd = 'STOR %s' % sleep_log_filename
            upload_result = ftp.storbinary(transfer_cmd, opened_sleep_log)
            if upload_result == '226 Transfer complete.':
                # Successful upload. remove the logfile
                log.info("Upload successful")
                os.remove(sleep_log)
            else:
                log.warning("Upload unsuccessful")

        ftp.close()
        log.info("FTP closed")
    except socket_error:
        log.warning("FTP Connection refused")
    except permission_error:
        log.warning("FTP invalid credentials")
    except Exception as e:
        log.error("Unknown ftp error encountered: %s" % e)


if __name__ == '__main__':
    upload_new_logfiles()

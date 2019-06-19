#pylint: disable-msg=R0913,R0904

""" Driver and worker thread that executes it. """

import select
import threading
import time
import md5
import logging
from kvring import KeyValueRing
try:
    from museek import messages, driver
except ImportError as error:
    print "Missing museek python bindings."

WORKER_THREAD_DELAY = 0.1

# import ConfigParser
# import sys
# import os

# parser = ConfigParser.ConfigParser()
# config_dir = str(os.path.expanduser("~/.museekd/"))
# config_file = config_dir + "museekcontrol.config"

logging.basicConfig(level=logging.INFO)

class MuseekDriver(driver.Driver):
    """ Driver that abstracts communication with MuSeek. """

    states = {
        0: "Finished",
        1: "Transferring",
        2: "Negotiating",
        3: "Waiting",
        4: "Establishing",
        5: "Initiating",
        6: "Connecting",
        7: "Queued",
        8: "Address",
        9: "Status",
        10: "Offline",
        11: "Closed",
        12: "Can't Connect",
        13: "Aborted",
        14: "Not Shared"
    }

    def __init__(self):
        driver.Driver.__init__(self)
        self.is_connected = False
        self.__uploads = {}
        self.__downloads = {}
        self.__search_results = {}
        self.__users = KeyValueRing(100)

    @staticmethod
    def print_transfer(direction, transfer):
        """ Log MuSeek transfer object. """

        logging.debug("%s user: %s, path: %s, fsize: %d, pos: %s, rate: %d, " \
                      "state: %s, err: %s", direction, transfer.user, \
                      transfer.path, transfer.filesize, transfer.filepos, \
                      transfer.rate, MuseekDriver.states[int(transfer.state)], \
                      transfer.error)

    @staticmethod
    def build_user_info(user, free=None, speed=None, queue=None, info=None,
                        image=None, uploads=None):
        """ Create dictionary object representing SoulSeek user. """

        return {"user": user, "free": free, "speed": speed, "queue": queue,
                "info": info, "image": image, "uploads": uploads}

    @staticmethod
    def transfer_to_dict(transfer):
        """ Convert MuSeek transfer object to dictionary representation. """

        return {"user": transfer.user, "path": transfer.path,
                "size": transfer.filesize, "pos": transfer.filepos,
                "rate": transfer.rate, "state": transfer.state}

    #
    # Methods for executing driver by a thread
    ##########

    def connect(self):
        """ Start MuSeek driver. Should be called by worker thread. """

        logging.info("connect")
        try:
            driver.Driver.connect(self, "localhost:2240", "password",
                                  (messages.EM_CHAT | messages.EM_USERINFO |
                                   messages.EM_PRIVATE | messages.EM_TRANSFERS |
                                   messages.EM_USERSHARES | messages.EM_CONFIG))
        except Exception, err:
            logging.error(err)

    def process(self):
        """ Tick function that should be executed by worker thread. """

        rd_ready, wr_ready, exec_ready = select.select([self.socket], [],
                                                       [self.socket], 0)
        if self.socket in rd_ready:
            logging.debug("process: %s %s %s", str(rd_ready), str(wr_ready),
                          str(exec_ready))
            driver.Driver.process(self)

    def disconnect(self):
        """ Stop MuSeek driver. """

        driver.Driver.close(self)

    #
    # Interface for server application
    ##########

    def get_uploads(self):
        """ Return dictionary of all upload transfers. """

        return self.__uploads

    def get_downloads(self):
        """ Return dictionary of all download transfers. """

        return self.__downloads

    def abort_download(self, md5hash):
        """ Abort MuSeek download transfer corresponding to provided MD5
            hash. """

        logging.info("abort_download: %s", md5hash)
        dload = self.__downloads[md5hash]
        logging.info("abort_download: user: %s, path: %s", dload["user"],
                     dload["path"])
        self.send(messages.TransferAbort(0, dload["user"], dload["path"]))

    def abort_upload(self, md5hash):
        """ Abort MuSeek upload transfer corresponding to provided MD5 hash. """

        logging.info("abort_upload: %s", md5hash)
        uload = self.__uploads[md5hash]
        logging.info("abort_upload: user: %s, path: %s", uload["user"],
                     uload["path"])
        self.send(messages.TransferAbort(1, uload["user"], uload["path"]))

    def remove_download(self, md5hash):
        """ Remove MuSeek download transfer corresponding to provided MD5
            hash. """

        logging.info("remove_download: %s", md5hash)
        dload = self.__downloads[md5hash]
        logging.info("remove_download: user: %s, path: %s", dload["user"],
                     dload["path"])
        self.send(messages.TransferRemove(0, dload["user"], dload["path"]))

    def remove_upload(self, md5hash):
        """ Remove MuSeek upload transfer corresponding to provided MD5
            hash. """

        logging.info("remove_upload: %s", md5hash)
        uload = self.__uploads[md5hash]
        logging.info("remove_upload: user: %s, path: %s", uload["user"],
                     uload["path"])
        self.send(messages.TransferRemove(1, uload["user"], uload["path"]))

    def start_search(self, query):
        """ Kick off SoulSeek search. """

        logging.info("start_search: %s", query)
        self.send(messages.Search(0, query))

    def start_file_download(self, ticket, user, index):
        """ Start MuSeek download. """

        logging.info("start_file_download: ticket: %d, user: %s, index: %d",
                     ticket, user, index)
        uresults = self.get_search_results_for_user(ticket, user)
        if uresults is not None and index < len(uresults):
            logging.debug("path: %s", uresults[index][0])
            self.send(messages.DownloadFile(user, uresults[index][0]))

    def stop_search(self, ticket):
        """ Unsupported """

        logging.info("stop_search: %s", ticket)
        self.send(messages.SearchReply(ticket=ticket))

    def get_search_results_for_ticket(self, ticket):
        """ Returns dictionary object for search results of search
            corresponding to specified ticket. """

        if ticket not in self.__search_results:
            return None
        return self.__search_results[ticket]

    def get_search_results_for_user(self, ticket, user):
        """ TODO: """

        tresults = self.get_search_results_for_ticket(ticket)
        if tresults is None or user not in tresults:
            return None
        return tresults[user]

    def get_searches(self):
        """ Returns list of search tickets. """

        return list(self.__search_results.keys())

    def get_user(self, user):
        """ Issue request for user info and return current info. """

        self.send(messages.UserInfo(user))
        uinfo = self.__users.get(user)
        if uinfo is not None:
            return uinfo
        return MuseekDriver.build_user_info(user)

    def get_users(self):
        """ Return list of all cached users and their parameters. """
        return self.__users.get_all()

    #
    # Private methods
    ##########

    def __set_search_results_for_user(self, ticket, user, results):
        """ Cache search results for one user in results for specified
            ticket. """

        if ticket not in self.__search_results:
            self.__search_results[ticket] = {}
        tresults = self.__search_results[ticket]
        if user in tresults:
            logging.critical("__set_search_results_for_user: user %s should "\
                             "not exist", user)
        tresults[user] = results

    def __set_user(self, user, free, speed, queue, info=None, image=None, uploads=None):
        """ Cache user info. """

        uinfo = MuseekDriver.build_user_info(user, free, speed, queue, info,
                                             image, uploads)
        self.__users.set(user, uinfo)

    #
    # driver.Driver callbacks
    ##########

    def cb_transfer_state(self, downloads, uploads):
        """ List of MuSeek download and upload transfers. """

        logging.debug("cb_transfer_state(downloads, uploads)")
        for xfer in uploads:
            MuseekDriver.print_transfer("uploading...", xfer)
            mdhash = md5.new(str(xfer.user + xfer.path)).hexdigest()
            self.__uploads[mdhash] = MuseekDriver.transfer_to_dict(xfer)
        for xfer in downloads:
            MuseekDriver.print_transfer("downloading...", xfer)
            mdhash = md5.new(str(xfer.user + xfer.path)).hexdigest()
            self.__downloads[mdhash] = MuseekDriver.transfer_to_dict(xfer)

    def cb_transfer_update(self, transfer):
        """ State update for one MuSeek transfer. """

        logging.debug("cb_transfer_update(transfer)")
        if transfer.is_upload:
            MuseekDriver.print_transfer("uploading...", transfer)
            mdhash = md5.new(str(transfer.user + transfer.path)).hexdigest()
            self.__uploads[mdhash] = MuseekDriver.transfer_to_dict(transfer)
        else:
            MuseekDriver.print_transfer("downloading...", transfer)
            mdhash = md5.new(str(transfer.user + transfer.path)).hexdigest()
            self.__downloads[mdhash] = MuseekDriver.transfer_to_dict(transfer)

    def cb_transfer_abort(self, transfer):
        """ MuSeek transfer aborted. """

        logging.debug("cb_transfer_abort: %s", str(transfer))

    def cb_transfer_remove(self, transfer):
        """ MuSeek transfer removed. """

        logging.debug("cb_transfer_remove: %s %d", str(transfer), transfer[0])
        if transfer[0] > 0:
            del self.__uploads[md5.new(str(transfer[1] + transfer[2])).hexdigest()]
        else:
            del self.__downloads[md5.new(str(transfer[1] + transfer[2])).hexdigest()]

    def cb_server_state(self, state, username):
        """ MuSeek daemon state update. """

        logging.debug("cb_server_state: %s %s", str(state), username)

    def cb_disconnected(self):
        """ TODO: """

        logging.debug("cb_disconnected")

    def cb_login_error(self, reason):
        """ TODO: """

        logging.debug("cb_login_error")

    def cb_login_ok(self):
        """ TODO: """

        logging.debug("cb_login_ok")
        self.is_connected = True

    def cb_search_results(self, ticket, user, free, speed, queue, results):
        """ MuSeek search results for one user for one ticket. """

        logging.debug("cb_search_results: ticket: %s, user: %s, free: %s, " \
                      "speed: %s, queue: %s, results: %s", ticket, user, free,
                      speed, queue, results)
        # MONKEY: if len(results) == 0:
        if not results:
            return
        uresults = self.get_search_results_for_user(ticket, user)
        if uresults is not None:
            logging.critical("cb_search_results: results for user %s should "\
                             "be empty", user)
        self.__set_search_results_for_user(int(ticket), user, results)
        self.__set_user(user, free, speed, queue)

    def cb_user_info(self, user, info, picture, uploads, queue, free):
        """ Received user info. """

        logging.debug("cb_user_info: user: %s, info: %s, image: %s, " \
                      "uploads: %d, queue: %d, free: %d", user, info, picture,
                      uploads, queue, free)
        self.__set_user(user, free, 0, queue, info, picture, uploads)

class MuseekWorker(threading.Thread):
    """ Thread that executes MuseekDriver. """

    def __init__(self, mudrvr):
        super(MuseekWorker, self).__init__()
        self.driver = mudrvr
        self.event_stop = threading.Event()

    def run(self):
        self.driver.connect()
        while not self.event_stop.isSet():
            time.sleep(WORKER_THREAD_DELAY)
            self.driver.process()

    def join(self, timeout=None):
        self.event_stop.set()
        super(MuseekWorker, self).join(timeout)

MUDRIVER = MuseekDriver()
MUWORKER = MuseekWorker(MUDRIVER)

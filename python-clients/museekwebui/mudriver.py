import ConfigParser, sys, os, select, threading, time, md5
from kvring import KeyValueRing
import logging
try:
  from museek import messages, driver
except:
 	print "Missing museek python bindings."

WORKER_THREAD_DELAY = 0.1

# parser = ConfigParser.ConfigParser()
# config_dir = str(os.path.expanduser("~/.museekd/"))
# config_file = config_dir + "museekcontrol.config"

logging.basicConfig(level=logging.DEBUG)

class MuseekDriver(driver.Driver):
  def __init__(self):
    driver.Driver.__init__(self)
    self.states = {0: "Finished", 1: "Transferring", 2: "Negotiating", 3: "Waiting", 4: "Establishing", 5: "Initiating", 6: "Connecting", 7: "Queued", 8: "Address", 9: "Status", 10: "Offline", 11: "Closed", 12: "Can't Connect", 13: "Aborted", 14: "Not Shared" }
    self.is_connected = False
    self.__uploads = {}
    self.__downloads = {}
    self.__search_results = {}
    self.__users = KeyValueRing(100)

  def connect(self):
    logging.info("connect")
    try:
      driver.Driver.connect(self, "localhost:2240", "password", messages.EM_CHAT | messages.EM_USERINFO | messages.EM_PRIVATE | messages.EM_TRANSFERS | messages.EM_USERSHARES | messages.EM_CONFIG)
    except Exception, e:
      logging.error(e)

  def process(self):
    # select(ready_read_list, ready_write_list, exception_list, timeout_s)
    r, w, x = select.select([self.socket], [], [self.socket], 0)
    if self.socket in r:
      logging.debug("process: " + str(r) + " " + str(w) + " " + str(x))
      driver.Driver.process(self)

  def disconnect(self):
    driver.Driver.close(self)

  def get_uploads(self):
    return self.__uploads

  def get_downloads(self):
    return self.__downloads

  def abort_download(self, md5hash):
    logging.info("abort_download: %s" % (md5hash))
    d = self.__downloads[md5hash]
    logging.info("abort_download: user: %s, path: %s" % (d["user"], d["path"]))
    self.send(messages.TransferAbort(0, d["user"], d["path"]))

  def abort_upload(self, md5hash):
    logging.info("abort_upload: %s" % (md5hash))
    u = self.__uploads[md5hash]
    logging.info("abort_upload: user: %s, path: %s" % (u["user"], u["path"]))
    self.send(messages.TransferAbort(1, u["user"], u["path"]))

  def remove_download(self, md5hash):
    logging.info("remove_download: %s" % (md5hash))
    d = self.__downloads[md5hash]
    logging.info("remove_download: user: %s, path: %s" % (d["user"], d["path"]))
    self.send(messages.TransferRemove(0, d["user"], d["path"]))

  def remove_upload(self, md5hash):
    logging.info("remove_upload: %s" % (md5hash))
    u = self.__uploads[md5hash]
    logging.info("remove_upload: user: %s, path: %s" % (u["user"], u["path"]))
    self.send(messages.TransferRemove(1, u["user"], u["path"]))

  def start_search(self, query):
    logging.info("start_search: %s" % (query))
    self.send(messages.Search(0, query))

  def start_file_download(self, ticket, user, index):
    logging.info("start_file_download: ticket: %d, user: %s, index: %d" % (ticket, user, index))
    ur = self.get_sresults_for_user(ticket, user)
    if ur is not None and index < len(ur):
      logging.debug("path: %s" % (ur[index][0]))
      self.send(messages.DownloadFile(user, ur[index][0]))

  def stop_search(self, ticket):
    logging.info("stop_search: %s" % (ticket))
    self.send(messages.SearchReply(ticket=ticket))

  def print_transfer(self, direction, transfer):
    logging.debug("%s user: %s, path: %s, fsize: %d, pos: %s, rate: %d, state: %s, err: %s" % (direction, transfer.user, transfer.path, transfer.filesize, transfer.filepos, transfer.rate, self.states[int(transfer.state)], transfer.error))

  def get_sresults_for_ticket(self, ticket):
    if ticket not in self.__search_results:
      return None
    return self.__search_results[ticket]

  def get_sresults_for_user(self, ticket, user):
    ts = self.get_sresults_for_ticket(ticket)
    if ts is None or user not in ts:
      return None
    return ts[user]

  def get_searches(self):
    return list(self.__search_results.keys())

  def get_user(self, user):
    """ issue request for user info, return current info """
    self.send(messages.UserInfo(user))
    u = self.__users.get(user)
    if u is not None:
      return u
    return MuseekDriver.build_user_info(user)

  def get_users(self):
    return self.__users.get_all()

  def __transfer_to_dict(self, transfer):
    return {"user": transfer.user, "path": transfer.path, "size": transfer.filesize, "pos": transfer.filepos, "rate": transfer.rate, "state": transfer.state}

  def __set_sresults_for_user(self, ticket, user, results):
    if ticket not in self.__search_results:
      self.__search_results[ticket] = {}
    tr =  self.__search_results[ticket]
    if user in tr:
      print "MONKEY: should not exist"
    tr[user] = results

  @staticmethod
  def build_user_info(user, free=None, speed=None, queue=None, info=None, image=None, uploads=None):
    return {"user": user, "free": free, "speed": speed, "queue": queue, "info": info, "image": image, "uploads": uploads}

  def __set_user(self, user, free, speed, queue, info=None, image=None, uploads=None):
    self.__users.set(user, MuseekDriver.build_user_info(user, free, speed, queue, info, image, uploads))

  def cb_transfer_state(self, downloads, uploads):
    logging.debug("cb_transfer_state")
    for t in uploads:
      self.print_transfer("uploading...", t)
      self.__uploads[md5.new(str(t.user + t.path)).hexdigest()] = self.__transfer_to_dict(t)
    for t in downloads:
      self.print_transfer("downloading...", t)
      self.__downloads[md5.new(str(t.user + t.path)).hexdigest()] = self.__transfer_to_dict(t)

  def cb_transfer_update(self, transfer):
    logging.debug("cb_transfer_update")
    if transfer.is_upload:
      self.print_transfer("uploading...", transfer)
      self.__uploads[md5.new(str(transfer.user + transfer.path)).hexdigest()] = self.__transfer_to_dict(transfer)
    else:
      self.print_transfer("downloading...", transfer)
      self.__downloads[md5.new(str(transfer.user + transfer.path)).hexdigest()] = self.__transfer_to_dict(transfer)

  def cb_transfer_abort(self, transfer):
    logging.debug("cb_transfer_abort: %s" % (str(transfer)))

  def cb_transfer_remove(self, transfer):
    logging.debug("cb_transfer_remove: %s %d"  % (str(transfer), transfer[0]))
    if transfer[0] > 0:
      del self.__uploads[md5.new(str(transfer[1] + transfer[2])).hexdigest()]
    else:
      del self.__downloads[md5.new(str(transfer[1] + transfer[2])).hexdigest()]

  def cb_server_state(self, state, username):
    logging.debug("cb_server_state: " + str(state) + " " + username)

  def cb_disconnected(self):
    logging.debug("cb_disconnected")

  def cb_login_error(self, reason):
    logging.debug("cb_login_error")

  def cb_login_ok(self):
    logging.debug("cb_login_ok")
    self.is_connected = True

  def cb_search_results(self, ticket, user, free, speed, queue, results):
    # MONKEY: logging.debug("cb_search_results: ticket: %s, user: %s, free: %s, speed: %s, queue: %s, results: %s" % (ticket, user, free, speed, queue, results))
    logging.info("cb_search_results: ticket: %s, user: %s, free: %s, speed: %s, queue: %s, results: %s" % (ticket, user, free, speed, queue, results))
    if len(results) == 0:
      return
    us = self.get_sresults_for_user(ticket, user)
    if us is not None:
      print "MONKEY: should be empty"
    self.__set_sresults_for_user(int(ticket), user, results)
    self.__set_user(user, free, speed, queue)

  def cb_user_info(self, user, info, picture, uploads, queue, free):
    # MONKEY: logging.debug("cb_user_info: user: %s, info: %s, image: %s, uploads: %d, queue: %d, free: %d" % (user, info, picture, uploads, queue, free))
    logging.info("cb_user_info: user: %s, info: %s, image: %s, uploads: %d, queue: %d, free: %d" % (user, info, picture, uploads, queue, free))
    self.__set_user(user, free, 0, queue, info, picture, uploads)

class MuseekWorker(threading.Thread):
  def __init__(self, driver):
    super(MuseekWorker, self).__init__()
    self.driver = driver
    self.event_stop = threading.Event()

  def run(self):
    self.driver.connect()
    while not self.event_stop.isSet():
      time.sleep(WORKER_THREAD_DELAY)
      self.driver.process()

  def join(self, timeout=None):
    self.event_stop.set()
    super(MuseekWorker, self).join(timeout)

mudriver = MuseekDriver()
muworker = MuseekWorker(mudriver)


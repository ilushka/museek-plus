class KeyValueRing:
  def __init__(self, max_count):
    self.d = {}
    self.q = []
    self.max_count = max_count

  def set(self, key, value):
    print "KeyValueRing.set: key: %s; value: %s" % (key, value)

    # do we need to remove existing key from queue?
    oldval = self.d.get(key, None)
    if oldval is not None:
      del self.q[oldval["qindex"]]

    if len(self.q) >= self.max_count:
      del self.d[self.q.pop(0)]

    # at this point only <= max_count of elements should be stored in ring
    # and we know that new key will be at len(self.q) position

    # insert key/value
    self.d[key] = {"qindex": len(self.q), "value": value}
    self.q.append(key)

    # MONKEY:
    if len(self.d) != len(self.q):
      print "MONKEY: should not happen"

  def get(self, key):
    value = self.d.get(key, None)
    if value is not None:
      value = value["value"]
    return value

  def get_all(self):
    return self.d

  def __len__(self):
    return len(self.q)

  def __str__(self):
    s = ""
    for k in self.q:
      s += (k + ": " + self.d[k] + ", ")
    return s


from collections import namedtuple

ceremony_status = namedtuple('CEREMONY_STATUS', "started stopped")
CEREMONY_STATUS = ceremony_status(1, 2)

coven_trust = namedtuple('COVEN_TRUST', "unknown in_coven in_inner_sanctum")
COVEN_TRUST = coven_trust(0, 1, 2)

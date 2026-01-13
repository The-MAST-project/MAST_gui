import sys
sys.path.insert(0, '/path/to/MAST_common')

from common.notifications import Notifier

# Test focuser position update
Notifier().send_update(
    path=['focuser', 'position'],
    value=12345,
    update_cache=True,
    update_dom_as='text'
)

print("Notification sent!")

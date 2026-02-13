from django.dispatch import Signal


work_changed = Signal()
""" A user has created or made changes to a work.
"""


work_approved = Signal()
""" A user has approved a work.
"""


work_unapproved = Signal()
""" A user has unapproved a work (marked it as a work in progress).
"""


document_published = Signal()
""" A user has changed a document from draft to published.
"""


task_assigned = Signal()
""" A user has been assigned to a task
"""


task_closed = Signal()
""" A user has closed a task
"""

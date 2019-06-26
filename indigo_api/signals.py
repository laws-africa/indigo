from django.dispatch import Signal


work_changed = Signal(providing_args=["work", "request"])
""" A user has created or made changes to a work.
"""


document_published = Signal(providing_args=["document", "request"])
""" A user has changed a document from draft to published.
"""


task_closed = Signal(providing_args=["task"])
""" A user has closed a task
"""

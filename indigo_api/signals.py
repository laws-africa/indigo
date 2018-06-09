from django.dispatch import Signal


document_published = Signal(providing_args=["document", "request"])
""" A user has changed a from draft to published.
"""

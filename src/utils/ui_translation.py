"""Shared translations for the optional model-evaluation workflow UI."""
from PySide6.QtCore import QCoreApplication


def tr_ui(source):
    # Only fixed application text belongs here; never pass model/user text.
    return QCoreApplication.translate('WorkflowUI', source)

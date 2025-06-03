from PyQt5.QtWidgets import (
    QMainWindow,
    QTableWidgetItem,
    QWidget,
    QTableView,
    QHBoxLayout,
)
from PyQt5.QtGui import QIcon, QPixmap
import csv
from .data import Entry
from .table import EntryTableModel, EntryFilterProxy, FilterPanel
import uuid
import os

def try_float(x):
    try:
        return float(x)
    except ValueError:
        return 0.0



def load_entries():
    with open("image_db_amended.csv") as f:
        r = csv.DictReader(f)
        return [
            Entry(
                id=uuid.uuid4().hex,
                prompt_text=l["prompt"],
                filepath=f"http://127.0.0.1:8000/images/{os.path.basename(l["file"])}" ,
                is_upscale=l["upscale"] == "is_upscale",
                has_upscale=l["upscale"] == "has_upscale",
                score_mu=try_float(l["mu"]),
                score_sigma=try_float(l["sigma"]),
                width=l["width"],
                height=l["height"],
            )
            for l in r
        ]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Image Workflow Manager")

        entries = load_entries()
        model = EntryTableModel(entries)
        proxy = EntryFilterProxy()
        proxy.setSourceModel(model)

        self.table = QTableView()
        self.table.setModel(proxy)
        self.table.setSortingEnabled(True)

        self.filter_panel = FilterPanel(proxy)

        container = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(self.filter_panel)
        layout.addWidget(self.table)
        container.setLayout(layout)

        self.setCentralWidget(container)

    def add_entry_row(self, entry):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Thumbnail
        if entry.filepath:
            pixmap = QPixmap(entry.filepath).scaled(64, 64)
            item = QTableWidgetItem()
            item.setIcon(QIcon(pixmap))
        else:
            item = QTableWidgetItem("N/A")
        self.table.setItem(row, 0, item)

        # Prompt
        self.table.setItem(row, 1, QTableWidgetItem(entry.prompt_text))

        # Status
        status = (
            "Good"
            if entry.is_good
            else ("Broken" if entry.is_good is False else "Unmarked")
        )
        self.table.setItem(row, 2, QTableWidgetItem(status))

        # Upscale info
        upscale = (
            "Yes"
            if entry.is_upscale
            else ("Has Upscale" if entry.has_upscale else "No")
        )
        self.table.setItem(row, 3, QTableWidgetItem(upscale))

        # Score
        self.table.setItem(row, 4, QTableWidgetItem(str(entry.ranking_score)))



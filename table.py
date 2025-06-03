from PyQt5.QtCore import Qt, QAbstractTableModel, QVariant, QSortFilterProxyModel
from PyQt5.QtGui import QPixmap, QIcon

class EntryTableModel(QAbstractTableModel):
    def __init__(self, entries):
        super().__init__()
        self.entries = entries
        self.headers = [
            "Thumbnail", "Prompt", "Broken", "Upscale", "Score μ", "Score σ",
            "Deleted", "Width", "Height", "Seed"
        ]

    def rowCount(self, parent=None):
        return len(self.entries)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        entry = self.entries[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 1:
                return entry.prompt_text
            elif col == 2:
                return "Yes" if entry.broken else ("No" if entry.broken is False else "Unmarked")
            elif col == 3:
                if entry.is_upscale:
                    return f"Upscale of {entry.upscale_of}"
                elif entry.has_upscale:
                    return "Has Upscale"
                else:
                    return "None"
            elif col == 4:
                return f"{entry.score_mu:.3f}"
            elif col == 5:
                return f"{entry.score_sigma:.3f}"
            elif col == 6:
                return "Yes" if entry.deleted else "No"
            elif col == 7:
                return str(entry.width) if entry.width else "-"
            elif col == 8:
                return str(entry.height) if entry.height else "-"
            elif col == 9:
                return str(entry.seed) if entry.seed else "-"
        elif role == Qt.DecorationRole and col == 0 and entry.filepath:
            pixmap = QPixmap(entry.filepath).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            return QIcon(pixmap)
        return QVariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return QVariant()

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QCheckBox,
    QLabel, QSpinBox, QDoubleSpinBox, QPushButton
)

class FilterPanel(QWidget):
    def __init__(self, proxy_model):
        super().__init__()
        self.proxy = proxy_model
        layout = QVBoxLayout()

        # Prompt search
        self.prompt_search = QLineEdit()
        self.prompt_search.setPlaceholderText("Search prompt...")
        self.prompt_search.textChanged.connect(self.proxy.set_prompt_search)
        layout.addWidget(self.prompt_search)

        # Seed search
        self.seed_search = QLineEdit()
        self.seed_search.setPlaceholderText("Search seed...")
        self.seed_search.textChanged.connect(self.proxy.set_seed_search)
        layout.addWidget(self.seed_search)

        # Broken checkboxes
        broken_layout = QHBoxLayout()
        broken_layout.addWidget(QLabel("Broken:"))
        self.broken_true = QCheckBox("True")
        self.broken_false = QCheckBox("False")
        self.broken_true.stateChanged.connect(self.apply_broken_filter)
        self.broken_false.stateChanged.connect(self.apply_broken_filter)
        broken_layout.addWidget(self.broken_true)
        broken_layout.addWidget(self.broken_false)
        layout.addLayout(broken_layout)

        # Deleted checkboxes
        deleted_layout = QHBoxLayout()
        deleted_layout.addWidget(QLabel("Deleted:"))
        self.deleted_true = QCheckBox("True")
        self.deleted_false = QCheckBox("False")
        self.deleted_true.stateChanged.connect(self.apply_deleted_filter)
        self.deleted_false.stateChanged.connect(self.apply_deleted_filter)
        deleted_layout.addWidget(self.deleted_true)
        deleted_layout.addWidget(self.deleted_false)
        layout.addLayout(deleted_layout)

        # Upscale checkboxes
        upscale_layout = QHBoxLayout()
        upscale_layout.addWidget(QLabel("Upscale:"))
        self.is_upscale = QCheckBox("Is Upscale")
        self.has_upscale = QCheckBox("Has Upscale")
        self.is_upscale.stateChanged.connect(self.apply_upscale_filter)
        self.has_upscale.stateChanged.connect(self.apply_upscale_filter)
        upscale_layout.addWidget(self.is_upscale)
        upscale_layout.addWidget(self.has_upscale)
        layout.addLayout(upscale_layout)

        # Width range
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Width min:"))
        self.min_width = QSpinBox()
        self.min_width.setMaximum(10000)
        width_layout.addWidget(self.min_width)
        width_layout.addWidget(QLabel("max:"))
        self.max_width = QSpinBox()
        self.max_width.setMaximum(10000)
        width_layout.addWidget(self.max_width)
        self.min_width.valueChanged.connect(self.apply_width_filter)
        self.max_width.valueChanged.connect(self.apply_width_filter)
        layout.addLayout(width_layout)

        # Height range
        height_layout = QHBoxLayout()
        height_layout.addWidget(QLabel("Height min:"))
        self.min_height = QSpinBox()
        self.min_height.setMaximum(10000)
        height_layout.addWidget(self.min_height)
        height_layout.addWidget(QLabel("max:"))
        self.max_height = QSpinBox()
        self.max_height.setMaximum(10000)
        height_layout.addWidget(self.max_height)
        self.min_height.valueChanged.connect(self.apply_height_filter)
        self.max_height.valueChanged.connect(self.apply_height_filter)
        layout.addLayout(height_layout)

        # μ range
        mu_layout = QHBoxLayout()
        mu_layout.addWidget(QLabel("μ min:"))
        self.min_mu = QDoubleSpinBox()
        mu_layout.addWidget(self.min_mu)
        mu_layout.addWidget(QLabel("max:"))
        self.max_mu = QDoubleSpinBox()
        mu_layout.addWidget(self.max_mu)
        self.min_mu.valueChanged.connect(self.apply_mu_filter)
        self.max_mu.valueChanged.connect(self.apply_mu_filter)
        layout.addLayout(mu_layout)

        # σ range
        sigma_layout = QHBoxLayout()
        sigma_layout.addWidget(QLabel("σ min:"))
        self.min_sigma = QDoubleSpinBox()
        sigma_layout.addWidget(self.min_sigma)
        sigma_layout.addWidget(QLabel("max:"))
        self.max_sigma = QDoubleSpinBox()
        sigma_layout.addWidget(self.max_sigma)
        self.min_sigma.valueChanged.connect(self.apply_sigma_filter)
        self.max_sigma.valueChanged.connect(self.apply_sigma_filter)
        layout.addLayout(sigma_layout)

        # Reset button
        reset_btn = QPushButton("Reset Filters")
        reset_btn.clicked.connect(self.reset_filters)
        layout.addWidget(reset_btn)

        self.setLayout(layout)

    def apply_broken_filter(self):
        if self.broken_true.isChecked():
            self.proxy.set_broken_filter(True)
        elif self.broken_false.isChecked():
            self.proxy.set_broken_filter(False)
        else:
            self.proxy.set_broken_filter(None)

    def apply_deleted_filter(self):
        if self.deleted_true.isChecked():
            self.proxy.set_deleted_filter(True)
        elif self.deleted_false.isChecked():
            self.proxy.set_deleted_filter(False)
        else:
            self.proxy.set_deleted_filter(None)

    def apply_upscale_filter(self):
        if self.is_upscale.isChecked():
            self.proxy.set_upscale_filter('is_upscale')
        elif self.has_upscale.isChecked():
            self.proxy.set_upscale_filter('has_upscale')
        else:
            self.proxy.set_upscale_filter(None)

    def apply_width_filter(self):
        self.proxy.set_width_range(self.min_width.value(), self.max_width.value())

    def apply_height_filter(self):
        self.proxy.set_height_range(self.min_height.value(), self.max_height.value())

    def apply_mu_filter(self):
        self.proxy.set_mu_range(self.min_mu.value(), self.max_mu.value())

    def apply_sigma_filter(self):
        self.proxy.set_sigma_range(self.min_sigma.value(), self.max_sigma.value())

    def reset_filters(self):
        self.broken_true.setChecked(False)
        self.broken_false.setChecked(False)
        self.deleted_true.setChecked(False)
        self.deleted_false.setChecked(False)
        self.is_upscale.setChecked(False)
        self.has_upscale.setChecked(False)
        self.min_width.setValue(0)
        self.max_width.setValue(0)
        self.min_height.setValue(0)
        self.max_height.setValue(0)
        self.min_mu.setValue(0.0)
        self.max_mu.setValue(0.0)
        self.min_sigma.setValue(0.0)
        self.max_sigma.setValue(0.0)
        self.prompt_search.clear()
        self.seed_search.clear()
        self.proxy.set_broken_filter(None)
        self.proxy.set_deleted_filter(None)
        self.proxy.set_upscale_filter(None)
        self.proxy.set_width_range(None, None)
        self.proxy.set_height_range(None, None)
        self.proxy.set_mu_range(None, None)
        self.proxy.set_sigma_range(None, None)
        self.proxy.set_prompt_search("")
        self.proxy.set_seed_search("")

class EntryFilterProxy(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.filter_broken = None  # True / False / None
        self.filter_deleted = None  # True / False / None
        self.filter_upscale = None  # 'is_upscale' / 'has_upscale' / None
        self.min_width = None
        self.max_width = None
        self.min_height = None
        self.max_height = None
        self.prompt_search = ""
        self.seed_search = ""
        self.min_mu = None
        self.max_mu = None
        self.min_sigma = None
        self.max_sigma = None

    def set_broken_filter(self, value): self.filter_broken = value; self.invalidateFilter()
    def set_deleted_filter(self, value): self.filter_deleted = value; self.invalidateFilter()
    def set_upscale_filter(self, value): self.filter_upscale = value; self.invalidateFilter()
    def set_prompt_search(self, text): self.prompt_search = text.lower(); self.invalidateFilter()
    def set_seed_search(self, text): self.seed_search = text.lower(); self.invalidateFilter()
    def set_width_range(self, min_w, max_w): self.min_width = min_w; self.max_width = max_w; self.invalidateFilter()
    def set_height_range(self, min_h, max_h): self.min_height = min_h; self.max_height = max_h; self.invalidateFilter()
    def set_mu_range(self, min_mu, max_mu): self.min_mu = min_mu; self.max_mu = max_mu; self.invalidateFilter()
    def set_sigma_range(self, min_sigma, max_sigma): self.min_sigma = min_sigma; self.max_sigma = max_sigma; self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        entry = self.sourceModel().entries[source_row]

        if self.filter_broken is not None and entry.broken != self.filter_broken:
            return False
        if self.filter_deleted is not None and entry.deleted != self.filter_deleted:
            return False
        if self.filter_upscale == 'is_upscale' and not entry.is_upscale:
            return False
        if self.filter_upscale == 'has_upscale' and not entry.has_upscale:
            return False
        if self.min_width is not None and (entry.width is None or entry.width < self.min_width):
            return False
        if self.max_width is not None and (entry.width is None or entry.width > self.max_width):
            return False
        if self.min_height is not None and (entry.height is None or entry.height < self.min_height):
            return False
        if self.max_height is not None and (entry.height is None or entry.height > self.max_height):
            return False
        if self.prompt_search and self.prompt_search not in entry.prompt_text.lower():
            return False
        if self.seed_search and (entry.seed is None or self.seed_search not in str(entry.seed)):
            return False
        if self.min_mu is not None and entry.score_mu < self.min_mu:
            return False
        if self.max_mu is not None and entry.score_mu > self.max_mu:
            return False
        if self.min_sigma is not None and entry.score_sigma < self.min_sigma:
            return False
        if self.max_sigma is not None and entry.score_sigma > self.max_sigma:
            return False

        return True

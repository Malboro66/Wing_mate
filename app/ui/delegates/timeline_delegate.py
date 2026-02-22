from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import QStyledItemDelegate, QStyle, QStyleOptionViewItem


class TimelineDelegate(QStyledItemDelegate):
    """Renderiza uma barra/marker de progressão temporal sem setCellWidget."""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        ratio_raw = index.data(Qt.UserRole)
        try:
            ratio = float(ratio_raw)
        except (TypeError, ValueError):
            ratio = 0.0
        ratio = max(0.0, min(1.0, ratio))

        # fundo seleção/normal
        painter.save()
        if opt.state & QStyle.State_Selected:
            painter.fillRect(opt.rect, opt.palette.highlight())
        painter.restore()

        # trilha
        track_rect = opt.rect.adjusted(8, opt.rect.height() // 2 - 3, -8, -(opt.rect.height() // 2 - 3))
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(120, 120, 120, 80))
        painter.drawRoundedRect(track_rect, 3, 3)

        # preenchimento proporcional
        fill_w = int(track_rect.width() * ratio)
        if fill_w > 0:
            fill_rect = track_rect.adjusted(0, 0, -(track_rect.width() - fill_w), 0)
            painter.setBrush(QColor(53, 132, 228))
            painter.drawRoundedRect(fill_rect, 3, 3)

        # marcador pontual
        marker_x = track_rect.left() + int(track_rect.width() * ratio)
        marker_pen = QPen(QColor(255, 255, 255) if (opt.state & QStyle.State_Selected) else QColor(30, 30, 30))
        marker_pen.setWidth(1)
        painter.setPen(marker_pen)
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(marker_x - 3, track_rect.center().y() - 3, 6, 6)
        painter.restore()

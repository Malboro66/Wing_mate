# -*- coding: utf-8 -*-
"""Utilitários de feedback de erro orientado ao usuário."""

from __future__ import annotations

from typing import Optional, Any


def build_actionable_error_text(
    title: str,
    summary: str,
    action_hint: str,
    file_path: Optional[str] = None,
) -> str:
    lines = [summary]
    if file_path:
        lines.append(f"Arquivo: {file_path}")
    lines.append(f"Ação sugerida: {action_hint}")
    return "\n".join(lines)


def show_actionable_error(
    parent: Optional[Any],
    title: str,
    summary: str,
    action_hint: str,
    technical_details: str,
    file_path: Optional[str] = None,
) -> None:
    from PyQt5.QtWidgets import QApplication, QMessageBox

    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle(title)
    msg.setText(build_actionable_error_text(title, summary, action_hint, file_path))
    msg.setDetailedText(technical_details)

    copy_button = msg.addButton("Copiar erro", QMessageBox.ActionRole)
    msg.addButton(QMessageBox.Ok)
    msg.exec_()

    if msg.clickedButton() == copy_button:
        QApplication.clipboard().setText(technical_details)

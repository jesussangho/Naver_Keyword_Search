"""
황금키워드채굴기 - 통합 GUI 앱
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable, List, Optional, Tuple

import customtkinter as ctk

try:
    import config  # noqa: F401 — .env 로드 및 API 키 검증
except RuntimeError as exc:
    print(exc, file=sys.stderr)
    sys.exit(1)

import 문서수정
import 연관키워드검색
import 월간검색량

APP_NAME = "황금키워드채굴기"
APP_VERSION = "1.0.0"

COLORS = {
    "bg": "#0f1419",
    "sidebar": "#151b24",
    "card": "#1c2430",
    "card_hover": "#243040",
    "gold": "#d4af37",
    "gold_hover": "#e8c547",
    "gold_dim": "#9a7b1f",
    "text": "#f0f4f8",
    "text_dim": "#8b9cb3",
    "success": "#34d399",
    "danger": "#f87171",
    "border": "#2d3a4d",
}


def get_output_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.getcwd()


def open_path(path: str) -> None:
    folder = os.path.dirname(path) if os.path.isfile(path) else path
    if sys.platform == "darwin":
        subprocess.run(["open", folder], check=False)
    elif sys.platform == "win32":
        os.startfile(folder)  # type: ignore[attr-defined]
    else:
        subprocess.run(["xdg-open", folder], check=False)


class ToolPage(ctk.CTkFrame):
    def __init__(
        self,
        master,
        title: str,
        subtitle: str,
        columns: Tuple[str, ...],
        column_widths: Optional[Tuple[int, ...]] = None,
    ):
        super().__init__(master, fg_color="transparent")
        self.columns = columns
        self.column_widths = column_widths or tuple(120 for _ in columns)
        self._stop_flag = False
        self._worker: Optional[threading.Thread] = None

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 8))
        ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text=subtitle,
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w", pady=(4, 0))

        form = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=16)
        form.pack(fill="x", padx=28, pady=12)
        form_inner = ctk.CTkFrame(form, fg_color="transparent")
        form_inner.pack(fill="x", padx=20, pady=20)

        self.keyword_entry = ctk.CTkEntry(
            form_inner,
            placeholder_text="검색할 키워드를 입력하세요",
            height=44,
            font=ctk.CTkFont(size=14),
            border_color=COLORS["border"],
            fg_color=COLORS["bg"],
        )
        self.keyword_entry.pack(fill="x", pady=(0, 12))

        opts = ctk.CTkFrame(form_inner, fg_color="transparent")
        opts.pack(fill="x")
        ctk.CTkLabel(
            opts,
            text="조회 개수",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_dim"],
        ).pack(side="left")
        self.count_entry = ctk.CTkEntry(
            opts,
            width=120,
            height=36,
            font=ctk.CTkFont(size=13),
            border_color=COLORS["border"],
            fg_color=COLORS["bg"],
        )
        self.count_entry.pack(side="left", padx=(10, 0))
        self.count_entry.insert(0, "10")
        ctk.CTkLabel(
            opts,
            text="(0 = 전체/무제한)",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
        ).pack(side="left", padx=(8, 0))

        btn_row = ctk.CTkFrame(form_inner, fg_color="transparent")
        btn_row.pack(fill="x", pady=(16, 0))

        self.run_btn = ctk.CTkButton(
            btn_row,
            text="조회 시작",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["gold"],
            hover_color=COLORS["gold_hover"],
            text_color="#1a1408",
            command=self._on_run_clicked,
        )
        self.run_btn.pack(side="left")

        self.stop_btn = ctk.CTkButton(
            btn_row,
            text="중지",
            height=42,
            width=90,
            font=ctk.CTkFont(size=14),
            fg_color=COLORS["card_hover"],
            hover_color=COLORS["border"],
            text_color=COLORS["text"],
            state="disabled",
            command=self._request_stop,
        )
        self.stop_btn.pack(side="left", padx=(10, 0))

        self.open_btn = ctk.CTkButton(
            btn_row,
            text="저장 폴더 열기",
            height=42,
            width=130,
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
            hover_color=COLORS["card_hover"],
            text_color=COLORS["text_dim"],
            command=lambda: open_path(get_output_dir()),
        )
        self.open_btn.pack(side="right")

        self.progress = ctk.CTkProgressBar(
            form_inner,
            height=6,
            fg_color=COLORS["bg"],
            progress_color=COLORS["gold"],
        )
        self.progress.pack(fill="x", pady=(14, 0))
        self.progress.set(0)

        self.status_label = ctk.CTkLabel(
            form_inner,
            text="대기 중",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
        )
        self.status_label.pack(anchor="w", pady=(8, 0))

        table_card = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=16)
        table_card.pack(fill="both", expand=True, padx=28, pady=(0, 24))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Gold.Treeview",
            background=COLORS["bg"],
            foreground=COLORS["text"],
            fieldbackground=COLORS["bg"],
            borderwidth=0,
            rowheight=30,
            font=("Apple SD Gothic Neo", 12) if sys.platform == "darwin" else ("Malgun Gothic", 11),
        )
        style.configure(
            "Gold.Treeview.Heading",
            background=COLORS["sidebar"],
            foreground=COLORS["gold"],
            borderwidth=0,
            font=("Apple SD Gothic Neo", 12, "bold") if sys.platform == "darwin" else ("Malgun Gothic", 11, "bold"),
        )
        style.map(
            "Gold.Treeview",
            background=[("selected", COLORS["gold_dim"])],
            foreground=[("selected", COLORS["text"])],
        )

        table_wrap = tk.Frame(table_card, bg=COLORS["card"])
        table_wrap.pack(fill="both", expand=True, padx=12, pady=12)

        self.tree = ttk.Treeview(
            table_wrap,
            columns=columns,
            show="headings",
            style="Gold.Treeview",
        )
        for col, width in zip(columns, self.column_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor="center" if col != columns[0] else "w")

        scroll_y = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(table_wrap, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        table_wrap.grid_rowconfigure(0, weight=1)
        table_wrap.grid_columnconfigure(0, weight=1)

        self._run_handler: Optional[Callable[[], None]] = None

    def set_run_handler(self, handler: Callable[[], None]) -> None:
        self._run_handler = handler

    def _parse_count(self) -> int:
        text = self.count_entry.get().strip()
        if not text.isdigit():
            raise ValueError("조회 개수는 0 이상의 숫자여야 합니다.")
        return int(text)

    def _on_run_clicked(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        if self._run_handler:
            self._run_handler()

    def _request_stop(self) -> None:
        self._stop_flag = True
        self.set_status("중지 요청됨…", COLORS["danger"])

    def should_stop(self) -> bool:
        return self._stop_flag

    def reset_run_state(self) -> None:
        self._stop_flag = False

    def set_running(self, running: bool) -> None:
        self.run_btn.configure(state="disabled" if running else "normal")
        self.stop_btn.configure(state="normal" if running else "disabled")
        self.keyword_entry.configure(state="disabled" if running else "normal")
        self.count_entry.configure(state="disabled" if running else "normal")
        if running:
            self.progress.start()
        else:
            self.progress.stop()
            self.progress.set(0)

    def set_status(self, text: str, color: Optional[str] = None) -> None:
        self.status_label.configure(text=text, text_color=color or COLORS["text_dim"])

    def clear_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

    def add_row(self, values: Tuple) -> None:
        self.tree.insert("", "end", values=values)

    def start_worker(self, target: Callable[[], None]) -> None:
        self.reset_run_state()
        self.clear_table()
        self.set_running(True)

        def wrapper() -> None:
            try:
                target()
            finally:
                self.after(0, lambda: self.set_running(False))

        self._worker = threading.Thread(target=wrapper, daemon=True)
        self._worker.start()

    def get_keyword(self) -> str:
        keyword = self.keyword_entry.get().strip()
        if not keyword:
            raise ValueError("키워드를 입력해 주세요.")
        return keyword


class GoldenKeywordApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title(APP_NAME)
        self.geometry("1080x720")
        self.minsize(960, 640)
        self.configure(fg_color=COLORS["bg"])

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_pages()
        self.show_page("monthly")

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, width=220, fg_color=COLORS["sidebar"], corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=20, pady=(28, 32))
        ctk.CTkLabel(
            brand,
            text="✦",
            font=ctk.CTkFont(size=28),
            text_color=COLORS["gold"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand,
            text=APP_NAME,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand,
            text=f"v{APP_VERSION}",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w", pady=(2, 0))

        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        nav_items = [
            ("monthly", "월간 검색량"),
            ("related", "연관 키워드"),
            ("document", "문서수 조회"),
        ]
        for key, label in nav_items:
            btn = ctk.CTkButton(
                sidebar,
                text=label,
                height=44,
                anchor="w",
                font=ctk.CTkFont(size=14),
                fg_color="transparent",
                hover_color=COLORS["card_hover"],
                text_color=COLORS["text_dim"],
                command=lambda k=key: self.show_page(k),
            )
            btn.pack(fill="x", padx=14, pady=4)
            self.nav_buttons[key] = btn

        ctk.CTkLabel(
            sidebar,
            text="네이버 키워드 분석 도구",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"],
        ).pack(side="bottom", pady=20)

    def _build_pages(self) -> None:
        self.content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.pages: dict[str, ToolPage] = {}

        monthly = ToolPage(
            self.content,
            "월간 검색량",
            "연관 키워드를 확장 조회하며 PC·모바일 검색량, 문서수, 경쟁율을 수집합니다.",
            ("키워드", "PC검색량", "모바일검색량", "월간총검색량", "문서수", "경쟁율"),
            (140, 100, 110, 120, 100, 80),
        )
        monthly.set_run_handler(lambda: self._run_monthly(monthly))
        self.pages["monthly"] = monthly

        related = ToolPage(
            self.content,
            "연관 키워드",
            "키워드 도구 연관 키워드 목록을 조회하고 엑셀로 저장합니다.",
            ("키워드", "PC검색량", "모바일검색량", "월간총검색량", "경쟁정도"),
            (160, 110, 120, 130, 90),
        )
        related.set_run_handler(lambda: self._run_related(related))
        self.pages["related"] = related

        document = ToolPage(
            self.content,
            "문서수 조회",
            "네이버 블로그 검색 결과 문서 수를 조회합니다.",
            ("키워드", "문서수"),
            (200, 160),
        )
        document.count_entry.pack_forget()
        document.set_run_handler(lambda: self._run_document(document))
        self.pages["document"] = document

    def show_page(self, key: str) -> None:
        for page in self.pages.values():
            page.grid_forget()
        self.pages[key].grid(row=0, column=0, sticky="nsew")
        for nav_key, btn in self.nav_buttons.items():
            active = nav_key == key
            btn.configure(
                fg_color=COLORS["card"] if active else "transparent",
                text_color=COLORS["gold"] if active else COLORS["text_dim"],
            )

    def _run_monthly(self, page: ToolPage) -> None:
        try:
            keyword = page.get_keyword()
            max_count = page._parse_count()
        except ValueError as e:
            messagebox.showwarning("입력 오류", str(e))
            return

        def task() -> None:
            page.set_status(f"'{keyword}' 조회 중…", COLORS["gold"])

            def on_row(row: Tuple[str, str, str, str, str, float]) -> None:
                kw, pc, mobile, total, docs, comp = row
                comp_text = f"{comp:.2f}" if comp else "-"
                values = (kw, pc, mobile, total, docs, comp_text)
                page.after(0, lambda v=values: page.add_row(v))
                page.after(
                    0,
                    lambda: page.set_status(f"{len(page.tree.get_children())}개 수집됨", COLORS["gold"]),
                )

            def on_log(msg: str) -> None:
                page.after(0, lambda: page.set_status(msg, COLORS["text_dim"]))

            try:
                records = 월간검색량.crawl_keywords(
                    keyword,
                    max_count,
                    on_row=on_row,
                    on_log=on_log,
                    should_stop=page.should_stop,
                )
            except Exception as e:
                page.after(0, lambda: messagebox.showerror("조회 실패", str(e)))
                page.after(0, lambda: page.set_status("조회 실패", COLORS["danger"]))
                return

            if not records:
                page.after(0, lambda: page.set_status("결과 없음", COLORS["text_dim"]))
                return

            out_dir = get_output_dir()
            excel_path = os.path.join(out_dir, f"{월간검색량.sanitize_filename(keyword)}.xlsx")
            월간검색량.save_to_excel(excel_path, records)
            page.after(
                0,
                lambda: page.set_status(
                    f"완료 · {len(records)}개 · {os.path.basename(excel_path)}",
                    COLORS["success"],
                ),
            )
            page.after(
                0,
                lambda: messagebox.showinfo(
                    "저장 완료",
                    f"총 {len(records)}개 키워드를 저장했습니다.\n\n{excel_path}",
                ),
            )

        page.start_worker(task)

    def _run_related(self, page: ToolPage) -> None:
        try:
            keyword = page.get_keyword()
            max_count = page._parse_count()
        except ValueError as e:
            messagebox.showwarning("입력 오류", str(e))
            return

        def task() -> None:
            page.set_status(f"'{keyword}' 연관 키워드 조회 중…", COLORS["gold"])
            try:
                keyword_list = 연관키워드검색.get_related_keywords(keyword)
            except Exception as e:
                page.after(0, lambda: messagebox.showerror("조회 실패", str(e)))
                page.after(0, lambda: page.set_status("조회 실패", COLORS["danger"]))
                return

            if not keyword_list:
                page.after(0, lambda: page.set_status("결과 없음", COLORS["text_dim"]))
                return

            rows = [연관키워드검색.extract_row(item) for item in keyword_list]
            if max_count > 0:
                rows = rows[:max_count]

            for row in rows:
                if page.should_stop():
                    break
                kw, pc, mobile, total, *_rest, comp = row
                page.after(0, lambda r=(kw, pc, mobile, total, comp): page.add_row(r))

            out_dir = get_output_dir()
            excel_path = os.path.join(
                out_dir,
                f"{연관키워드검색.sanitize_filename(keyword)}_연관키워드.xlsx",
            )
            연관키워드검색.save_to_excel(excel_path, rows)
            page.after(
                0,
                lambda: page.set_status(
                    f"완료 · {len(rows)}개 · {os.path.basename(excel_path)}",
                    COLORS["success"],
                ),
            )
            page.after(
                0,
                lambda: messagebox.showinfo(
                    "저장 완료",
                    f"총 {len(rows)}개 연관 키워드를 저장했습니다.\n\n{excel_path}",
                ),
            )

        page.start_worker(task)

    def _run_document(self, page: ToolPage) -> None:
        try:
            keyword = page.get_keyword()
        except ValueError as e:
            messagebox.showwarning("입력 오류", str(e))
            return

        def task() -> None:
            page.set_status(f"'{keyword}' 문서수 조회 중…", COLORS["gold"])
            try:
                total = 문서수정.get_blog_document_count(keyword)
            except Exception as e:
                page.after(0, lambda: messagebox.showerror("조회 실패", str(e)))
                page.after(0, lambda: page.set_status("조회 실패", COLORS["danger"]))
                return

            text = f"{total:,}"
            page.after(0, lambda: page.add_row((keyword, text)))
            page.after(0, lambda: page.set_status(f"문서수: {text}", COLORS["success"]))

        page.start_worker(task)


def main() -> None:
    app = GoldenKeywordApp()
    app.mainloop()


if __name__ == "__main__":
    main()

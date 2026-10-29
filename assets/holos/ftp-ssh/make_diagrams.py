#!/usr/bin/env python3
"""HOLOS — FTP·SFTP / Telnet·SSH 설명 그림 생성 스크립트.

실행:  python3 make_diagrams.py [출력폴더]
결과:  <출력폴더>/svg/*.svg (원본, 1200×675)  <출력폴더>/png/*.png (가로 2400px)

PNG 변환에는 cairosvg가 필요합니다 (pip install cairosvg).
글꼴은 Noto Sans CJK KR / Noto Sans Mono CJK KR (없으면 시스템 기본 산세리프).
"""
import os
import sys
from xml.sax.saxutils import escape

W, H = 1200, 675
FONT = "Noto Sans CJK KR, Noto Sans KR, Apple SD Gothic Neo, Malgun Gothic, sans-serif"
MONO = "Noto Sans Mono CJK KR, D2Coding, Menlo, Consolas, DejaVu Sans Mono, monospace"

C = {
    "ink": "#1F2937",
    "navy": "#1F3A5F",
    "blue": "#2B4C7E",
    "light": "#E8F0F8",
    "pale": "#F6F8FB",
    "grey": "#6B7280",
    "line": "#9CA3AF",
    "red": "#B91C1C",
    "redbg": "#FDEDED",
    "green": "#1E6B4A",
    "greenbg": "#E7F4EC",
    "amber": "#B45309",
    "amberbg": "#FFF4E0",
    "white": "#FFFFFF",
    "term": "#111827",
    "termbar": "#374151",
    "termtext": "#E5E7EB",
    "termgreen": "#86EFAC",
    "termyellow": "#FDE68A",
}


class SVG:
    def __init__(self, title):
        self.parts = []
        self.title = title

    def add(self, s):
        self.parts.append(s)

    # --- primitives -----------------------------------------------------
    def rect(self, x, y, w, h, fill=C["white"], stroke=C["blue"], sw=2.5, rx=14, dash=None, opacity=1):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="{sw}"{d} opacity="{opacity}"/>')

    def text(self, x, y, s, size=20, weight=400, anchor="middle", fill=C["ink"], family=FONT, italic=False):
        st = ' font-style="italic"' if italic else ""
        # SVG는 연속 공백을 하나로 줄이므로, 들여쓰기·간격용 공백은 줄바꿈 없는 공백(U+00A0)으로 바꾼다.
        lead = len(s) - len(s.lstrip(" "))
        s = " " * lead + s.lstrip(" ")
        while "  " in s:
            s = s.replace("  ", "  ")
        self.add(f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
                 f'text-anchor="{anchor}" fill="{fill}"{st}>{escape(s)}</text>')

    def lines(self, x, y, items, size=18, step=30, family=FONT, fill=C["ink"], anchor="start", weight=400):
        for i, s in enumerate(items):
            self.text(x, y + i * step, s, size=size, family=family, fill=fill, anchor=anchor, weight=weight)

    def line(self, x1, y1, x2, y2, stroke=C["line"], sw=2.5, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"{d} '
                 f'stroke-linecap="round"/>')

    def arrow(self, x1, y1, x2, y2, stroke=C["blue"], sw=3.5, head=14):
        """선 + 화살촉 (마커를 쓰지 않고 직접 그림: 렌더러 호환성)."""
        import math
        ang = math.atan2(y2 - y1, x2 - x1)
        bx = x2 - head * math.cos(ang)
        by = y2 - head * math.sin(ang)
        self.line(x1, y1, bx, by, stroke=stroke, sw=sw)
        px = x2 - head * math.cos(ang) + (head * 0.55) * math.sin(ang)
        py = y2 - head * math.sin(ang) - (head * 0.55) * math.cos(ang)
        qx = x2 - head * math.cos(ang) - (head * 0.55) * math.sin(ang)
        qy = y2 - head * math.sin(ang) + (head * 0.55) * math.cos(ang)
        self.add(f'<polygon points="{x2},{y2} {px:.1f},{py:.1f} {qx:.1f},{qy:.1f}" fill="{stroke}"/>')

    def circle(self, cx, cy, r, fill=C["white"], stroke=C["blue"], sw=2.5):
        self.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def ellipse(self, cx, cy, rx, ry, fill=C["white"], stroke=C["blue"], sw=2.5):
        self.add(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def poly(self, pts, fill=C["white"], stroke=C["blue"], sw=2.5):
        p = " ".join(f"{x},{y}" for x, y in pts)
        self.add(f'<polygon points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/>')

    def path(self, d, fill="none", stroke=C["blue"], sw=2.5):
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round"/>')

    # --- composite icons ------------------------------------------------
    def eye(self, cx, cy, color):
        self.path(f"M {cx-34} {cy} Q {cx} {cy-32} {cx+34} {cy} Q {cx} {cy+32} {cx-34} {cy} Z", fill=C["white"], stroke=color, sw=3)
        self.circle(cx, cy, 11, fill=color, stroke=color)
        self.circle(cx + 3, cy - 3, 3.5, fill=C["white"], stroke=C["white"])

    def key(self, x, y, color=C["amber"], scale=1.0):
        """열쇠: 머리(원) 왼쪽, 날 오른쪽. (x, y)는 머리 중심."""
        s = scale
        self.circle(x, y, 16 * s, fill=C["white"], stroke=color, sw=4 * s)
        self.circle(x, y, 5 * s, fill=color, stroke=color)
        self.line(x + 16 * s, y, x + 72 * s, y, stroke=color, sw=6 * s)
        self.line(x + 58 * s, y, x + 58 * s, y + 14 * s, stroke=color, sw=6 * s)
        self.line(x + 70 * s, y, x + 70 * s, y + 18 * s, stroke=color, sw=6 * s)

    def padlock(self, x, y, color=C["blue"], scale=1.0, fill=None):
        """자물쇠: (x, y)는 몸통 왼쪽 위."""
        s = scale
        self.path(f"M {x+10*s} {y} V {y-16*s} A {16*s} {16*s} 0 0 1 {x+42*s} {y-16*s} V {y}", stroke=color, sw=5 * s)
        self.rect(x, y, 52 * s, 40 * s, fill=fill or C["white"], stroke=color, sw=4 * s, rx=6 * s)
        self.circle(x + 26 * s, y + 18 * s, 5 * s, fill=color, stroke=color)
        self.line(x + 26 * s, y + 20 * s, x + 26 * s, y + 30 * s, stroke=color, sw=4 * s)

    def door(self, x, y, w, h, label, sub=None):
        """문: 위에 문 번호, 아래에 작은 글자(예: SSH). 손잡이는 아래쪽 모서리에."""
        self.rect(x, y, w, h, fill=C["navy"], stroke=C["navy"], rx=6)
        self.circle(x + w - 8, y + h - 12, 3, fill=C["white"], stroke=C["white"])
        if sub:
            self.text(x + w / 2, y + h / 2 + 2, label, size=22, weight=700, fill=C["white"])
            self.text(x + w / 2, y + h / 2 + 22, sub, size=12, weight=700, fill=C["white"])
        else:
            self.text(x + w / 2, y + h / 2 + 8, label, size=22, weight=700, fill=C["white"])

    def cloud(self, cx, cy, label):
        for dx, dy, r in [(-46, 6, 30), (-14, -14, 38), (24, -4, 34), (50, 10, 26), (0, 14, 32)]:
            self.circle(cx + dx, cy + dy, r, fill="#F3F4F6", stroke="#F3F4F6")
        for dx, dy, r in [(-46, 6, 30), (-14, -14, 38), (24, -4, 34), (50, 10, 26), (0, 14, 32)]:
            self.add(f'<circle cx="{cx+dx}" cy="{cy+dy}" r="{r}" fill="none" stroke="{C["line"]}" stroke-width="2"/>')
        self.rect(cx - 80, cy - 28, 160, 68, fill="#F3F4F6", stroke="#F3F4F6", rx=20)
        self.text(cx, cy + 6, label, size=17, fill=C["grey"], weight=700)

    # --- output --------------------------------------------------------
    def render(self):
        body = "\n".join(self.parts)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
                f'<title>{escape(self.title)}</title>\n'
                f'<rect x="0" y="0" width="{W}" height="{H}" fill="{C["white"]}"/>\n'
                f'{body}\n</svg>\n')


def title(svg, s, size=30):
    svg.text(W / 2, 54, s, size=size, weight=700, fill=C["navy"])
    svg.line(W / 2 - 60, 72, W / 2 + 60, 72, stroke=C["blue"], sw=3)


# ----------------------------------------------------------------------
# 1. 파일 전송 프로그램이 하는 일
# ----------------------------------------------------------------------
def d_ftp_transfer():
    s = SVG("파일 전송 프로그램이 하는 일")
    title(s, "파일 전송 프로그램이 하는 일")

    # 내 컴퓨터
    s.rect(60, 110, 310, 330, fill=C["pale"])
    s.text(215, 152, "내 컴퓨터", size=24, weight=700)
    s.text(215, 180, "(노트북, 또는 Replit에서 받은 ZIP을 푼 곳)", size=14, fill=C["grey"])
    s.rect(90, 200, 250, 215, fill=C["white"], stroke=C["line"], sw=1.5, rx=8)
    s.lines(108, 236, ["my-site/", "    index.html", "    style.css", "    visitor.js", "    images/", "        logo.png"],
            size=18, step=29, family=MONO)

    # 서버
    s.rect(830, 110, 310, 330, fill=C["pale"])
    s.text(985, 152, "서버", size=24, weight=700)
    s.text(985, 180, "(호스팅 회사의 컴퓨터, 늘 켜져 있음)", size=14, fill=C["grey"])
    s.rect(860, 200, 250, 215, fill=C["white"], stroke=C["line"], sw=1.5, rx=8)
    s.lines(878, 236, ["public_html/", "    holos202599999/", "        index.html", "        style.css", "        visitor.js", "        images/"],
            size=18, step=29, family=MONO)
    s.text(985, 463, "방문자가 보는 주소  https://holos202599999.epiph.net", size=13, fill=C["grey"])

    # 가운데: 전송 프로그램
    s.rect(430, 215, 340, 120, fill=C["light"], stroke=C["blue"], sw=2.5)
    s.text(600, 258, "파일 전송 프로그램", size=22, weight=700, fill=C["navy"])
    s.text(600, 287, "FileZilla · WinSCP · 호스팅 회사의 웹 파일 관리자", size=15, fill=C["grey"])
    s.text(600, 314, "서버와 대화하는 약속: FTP 또는 SFTP", size=16, fill=C["blue"], weight=700)

    # 화살표
    s.arrow(372, 178, 826, 178, stroke=C["blue"])
    s.text(600, 165, "업로드 (올리기)", size=18, weight=700, fill=C["blue"])
    s.arrow(826, 385, 372, 385, stroke=C["grey"])
    s.text(600, 415, "다운로드 (내려받기)", size=18, weight=700, fill=C["grey"])

    # 아래: 접속 정보
    s.rect(60, 488, 1080, 150, fill=C["amberbg"], stroke="#F3D7A3", sw=2)
    s.text(600, 522, "접속할 때 입력하는 네 가지", size=20, weight=700, fill=C["amber"])
    cols = [(195, "호스트 (서버 주소)", "예: ftp.example.com 또는 123.45.67.89"),
            (465, "사용자 이름", "예: 202599999"),
            (735, "비밀번호 (또는 키)", "안내문에서 확인"),
            (1005, "포트 (문 번호)", "FTP 21 · SFTP 22")]
    for x, a, b in cols:
        s.text(x, 568, a, size=19, weight=700)
        s.text(x, 600, b, size=14, fill=C["grey"])
    return s


# ----------------------------------------------------------------------
# 2. 평문과 암호화 — 엽서와 봉인 편지
# ----------------------------------------------------------------------
def d_postcard():
    s = SVG("평문과 암호화 — 엽서와 봉인 편지")
    title(s, "평문과 암호화 — 엽서와 봉인 편지")

    def row(y, label, color, bg, secure):
        s.text(60, y - 48, label, size=20, weight=700, fill=color, anchor="start")
        s.rect(60, y - 50 + 24, 200, 100, fill=C["pale"])
        s.text(160, y + 32, "내 컴퓨터", size=22, weight=700)
        s.rect(940, y - 50 + 24, 200, 100, fill=C["pale"])
        s.text(1040, y + 32, "서버", size=22, weight=700)
        # 경로
        s.arrow(262, y + 24, 505, y + 24, stroke=C["line"], sw=2.5)
        s.arrow(695, y + 24, 936, y + 24, stroke=C["line"], sw=2.5)
        s.cloud(600, y + 24, "인터넷 · 공용 와이파이")
        # 엿보는 사람
        s.eye(600, y - 48, color)
        # 메시지
        mx, my = 300, y - 30
        if not secure:
            s.rect(mx, my, 200, 108, fill=C["white"], stroke=color, sw=2.5, rx=6)
            s.rect(mx + 160, my + 10, 28, 28, fill=bg, stroke=color, sw=1.5, rx=3)
            s.lines(mx + 14, my + 34, ["사용자: siwoo", "비밀번호: 1234", "index.html 내용…"], size=15, step=26, family=MONO, fill=color)
            s.text(mx + 100, my + 128, "엽서: 지나가는 누구나 읽는다", size=14, fill=color)
        else:
            # 봉투
            s.rect(mx, my + 6, 200, 96, fill=C["white"], stroke=color, sw=2.5, rx=6)
            s.poly([(mx, my + 6), (mx + 100, my + 62), (mx + 200, my + 6)], fill=bg, stroke=color, sw=2.5)
            s.circle(mx + 100, my + 62, 16, fill=color, stroke=color)
            s.text(mx + 100, my + 68, "S", size=17, weight=700, fill=C["white"])
            s.text(mx + 100, my + 92, "x7Q!…9f#kL2…", size=14, family=MONO, fill=C["grey"])
            s.text(mx + 100, my + 128, "봉인된 편지: 받는 쪽만 연다", size=14, fill=color)
        # 서버 앞 결과
        rx = 700
        if not secure:
            s.text(rx + 100, y + 2, "중간에서 본 사람도", size=14, fill=color)
            s.text(rx + 100, y + 22, "비밀번호를 그대로 안다", size=14, fill=color, weight=700)
        else:
            s.text(rx + 100, y + 2, "중간에서 본 사람은", size=14, fill=color)
            s.text(rx + 100, y + 22, "뜻 모를 글자만 본다", size=14, fill=color, weight=700)

    row(185, "FTP · Telnet — 평문 (21번 · 23번 문)", C["red"], C["redbg"], secure=False)
    row(455, "SFTP · SSH — 암호화 (22번 문)", C["green"], C["greenbg"], secure=True)

    s.text(600, 625, "같은 길(인터넷)을 지나도, 봉투가 있느냐 없느냐가 다릅니다.", size=18, weight=700, fill=C["navy"])
    s.text(600, 652, "FTP와 Telnet은 1970년대 '믿을 수 있는 연구망' 시절에 만들어져 봉투를 쓰지 않습니다.", size=14, fill=C["grey"])
    return s


# ----------------------------------------------------------------------
# 3. 이름은 비슷해도 가족이 다르다
# ----------------------------------------------------------------------
def d_family():
    s = SVG("이름은 비슷해도 가족이 다르다")
    title(s, "이름은 비슷해도 가족이 다르다 — FTPS와 SFTP")

    def column(cx, parent, psub, child, csub, arrow_label, color, fill):
        bw = 320
        s.rect(cx - bw / 2, 120, bw, 86, fill=C["pale"], stroke=color)
        s.text(cx, 156, parent, size=26, weight=700, fill=color)
        s.text(cx, 186, psub, size=15, fill=C["grey"])
        s.arrow(cx, 210, cx, 300, stroke=color)
        s.text(cx + 14, 262, arrow_label, size=15, fill=color, anchor="start", weight=700)
        s.rect(cx - bw / 2, 304, bw, 96, fill=fill, stroke=color)
        s.text(cx, 342, child, size=24, weight=700, fill=color)
        s.text(cx, 376, csub, size=15, fill=C["ink"])

    column(220, "HTTP", "웹 페이지를 받는 약속 (1991)", "HTTPS", "HTTP + TLS (주소창의 자물쇠)", "+ TLS", C["grey"], C["white"])
    column(600, "FTP", "파일 전송 약속 (1971)", "FTPS", "FTP + TLS — S가 뒤에 붙음", "+ TLS", C["blue"], C["light"])
    column(980, "SSH", "안전한 원격 접속 약속 (1995)", "SFTP", "SSH의 파일 전송 기능 — S가 앞에 붙음", "+ 파일 전송 기능", C["green"], C["greenbg"])

    # FTPS ≠ SFTP
    s.line(762, 352, 818, 352, stroke=C["red"], sw=3, dash="8,7")
    s.line(780, 340, 800, 364, stroke=C["red"], sw=4)
    s.line(800, 340, 780, 364, stroke=C["red"], sw=4)
    s.text(790, 430, "FTPS와 SFTP는 이름만 닮았을 뿐, 서로 다른 약속이라 통하지 않습니다.", size=15, fill=C["red"], weight=700)
    s.text(220, 430, "익숙한 예: 같은 방식으로 보안을 덧댄 것", size=15, fill=C["grey"])

    # 아래 요약
    s.rect(60, 480, 520, 160, fill=C["light"], stroke=C["blue"])
    s.text(320, 516, "FTP 가족 (FTP, FTPS)", size=20, weight=700, fill=C["blue"])
    s.lines(90, 552, ["21번 문 (FTPS는 21 또는 990)", "명령 연결과 데이터 연결이 따로 — 방화벽에서 까다로움", "비밀번호 로그인"], size=16, step=28)
    s.rect(620, 480, 520, 160, fill=C["greenbg"], stroke=C["green"])
    s.text(880, 516, "SSH 가족 (SSH, SFTP, scp)", size=20, weight=700, fill=C["green"])
    s.lines(650, 552, ["22번 문 하나", "연결 하나로 터미널도, 파일 전송도", "비밀번호 또는 키(열쇠)로 로그인"], size=16, step=28)
    return s


# ----------------------------------------------------------------------
# 4. 원격 접속 — 터미널과 셸
# ----------------------------------------------------------------------
def d_terminal():
    s = SVG("원격 접속 — 내 터미널이 멀리 있는 컴퓨터의 셸에 연결된다")
    title(s, "원격 접속 — 내 터미널이 멀리 있는 컴퓨터의 셸에 연결됩니다", size=27)

    # 터미널 창
    s.rect(60, 110, 480, 300, fill=C["term"], stroke=C["term"], rx=12)
    s.rect(60, 110, 480, 40, fill=C["termbar"], stroke=C["termbar"], rx=12)
    s.rect(60, 130, 480, 20, fill=C["termbar"], stroke=C["termbar"], rx=0)
    for i, col in enumerate(["#F87171", "#FBBF24", "#34D399"]):
        s.circle(84 + i * 22, 130, 7, fill=col, stroke=col)
    s.text(300, 137, "터미널 (내 컴퓨터)", size=16, fill=C["termtext"], weight=700)
    tl = [("$ ssh siwoo@my-server", C["termtext"]),
          ("siwoo@my-server's password:", C["termyellow"]),
          ("siwoo@my-server:~$ ls", C["termgreen"]),
          ("app.zip   public   deploy.log", C["termtext"]),
          ("siwoo@my-server:~$ exit", C["termgreen"]),
          ("Connection to my-server closed.", C["termtext"])]
    for i, (t, col) in enumerate(tl):
        s.text(84, 190 + i * 34, t, size=17, family=MONO, fill=col, anchor="start")

    # 서버
    s.rect(780, 110, 360, 300, fill=C["pale"])
    s.text(960, 150, "서버 (데이터센터 어딘가)", size=21, weight=700)
    s.text(960, 176, "모니터도 키보드도 붙어 있지 않다", size=14, fill=C["grey"])
    s.rect(820, 200, 280, 86, fill=C["light"], stroke=C["blue"])
    s.text(960, 236, "셸 (bash)", size=22, weight=700, fill=C["navy"])
    s.text(960, 264, "받은 글자를 명령으로 해석해 실행", size=14, fill=C["grey"])
    s.text(960, 320, "ls → 파일 목록을 글자로 만들어 돌려보냄", size=15, fill=C["ink"])
    s.text(960, 352, "app.zip · public · deploy.log", size=15, family=MONO, fill=C["grey"])
    s.door(760, 218, 44, 90, "22", sub="SSH")

    # 화살표
    s.arrow(544, 236, 756, 236, stroke=C["blue"])
    s.text(650, 220, "내가 친 글자 (명령)", size=16, weight=700, fill=C["blue"])
    s.arrow(756, 292, 544, 292, stroke=C["grey"])
    s.text(650, 324, "서버가 돌려준 글자 (결과)", size=16, weight=700, fill=C["grey"])

    # 아래 세 칸
    boxes = [(60, "터미널 (terminal)", ["글자로 명령을 입력하고", "글자로 결과를 보는 창", "Replit의 Shell 탭도 터미널"]),
             (430, "셸 (shell)", ["그 글자를 명령으로 해석해", "실행하는 프로그램", "bash, zsh, PowerShell 등"]),
             (800, "원격 접속", ["내 터미널과 멀리 있는 셸을", "네트워크로 잇는 것", "Telnet(23번) → SSH(22번)"])]
    for x, head, body in boxes:
        s.rect(x, 460, 340, 170, fill=C["pale"], stroke=C["line"], sw=1.5)
        s.text(x + 170, 496, head, size=20, weight=700, fill=C["navy"])
        s.lines(x + 170, 532, body, size=15, step=28, anchor="middle")
    return s


# ----------------------------------------------------------------------
# 5. SSH 키 쌍
# ----------------------------------------------------------------------
def d_keypair():
    s = SVG("SSH 키 쌍 — 자물쇠는 서버에, 열쇠는 내 컴퓨터에")
    title(s, "SSH 키 쌍 — 자물쇠는 서버에, 열쇠는 내 컴퓨터에")

    # 내 컴퓨터
    s.rect(60, 100, 460, 270, fill=C["pale"])
    s.text(290, 138, "내 컴퓨터", size=22, weight=700)
    s.text(290, 162, "ssh-keygen 명령 한 번으로 두 파일이 생긴다", size=14, fill=C["grey"])
    # 개인키
    s.key(110, 215, color=C["amber"])
    s.text(200, 206, "개인키 (private key)", size=18, weight=700, anchor="start", fill=C["amber"])
    s.text(200, 230, "id_ed25519", size=15, family=MONO, anchor="start", fill=C["grey"])
    s.text(200, 254, "열쇠 — 절대 밖으로 내보내지 않는다", size=15, anchor="start", fill=C["red"], weight=700)
    # 공개키
    s.padlock(90, 300, color=C["blue"])
    s.text(200, 300, "공개키 (public key)", size=18, weight=700, anchor="start", fill=C["blue"])
    s.text(200, 324, "id_ed25519.pub", size=15, family=MONO, anchor="start", fill=C["grey"])
    s.text(200, 348, "자물쇠 — 누가 봐도 괜찮다, 서버에 복사한다", size=15, anchor="start", fill=C["ink"])

    # 서버
    s.rect(680, 100, 460, 270, fill=C["pale"])
    s.text(910, 138, "서버", size=22, weight=700)
    s.text(910, 162, "~/.ssh/authorized_keys — 등록된 자물쇠 목록", size=14, fill=C["grey"], family=MONO)
    s.rect(720, 190, 380, 150, fill=C["white"], stroke=C["line"], sw=1.5, rx=8)
    for i, (who, col) in enumerate([("siwoo의 노트북", C["blue"]), ("siwoo의 연구실 PC", C["grey"]), ("배포용 GitHub Actions", C["grey"])]):
        y = 200 + i * 46
        s.padlock(740, y + 14, color=col, scale=0.55)
        s.text(800, y + 34, who, size=16, anchor="start", fill=col, weight=700 if i == 0 else 400)

    # 복사 화살표
    s.arrow(525, 322, 716, 234, stroke=C["blue"])
    s.text(600, 212, "공개키만 서버에 등록", size=15, weight=700, fill=C["blue"])
    s.text(600, 234, "(ssh-copy-id, 또는 복사·붙여넣기)", size=13, fill=C["grey"])

    # 로그인 절차
    s.rect(60, 410, 1080, 228, fill=C["light"], stroke=C["blue"])
    s.text(600, 446, "로그인할 때 일어나는 일 — 비밀번호도 개인키도 네트워크를 지나지 않습니다", size=19, weight=700, fill=C["navy"])
    steps = [(240, "1", "서버가 문제를 낸다", ["\"이 자물쇠를 열 수 있는지", "증명해 봐\" — 수학 문제 하나"]),
             (600, "2", "내 컴퓨터가 개인키로 푼다", ["개인키 자체는 보내지 않고", "답(서명)만 보낸다"]),
             (960, "3", "서버가 공개키로 확인한다", ["답이 맞으면 통과,", "틀리면 거절 — 그걸로 끝"])]
    for x, n, head, body in steps:
        s.circle(x - 150, 520, 20, fill=C["navy"], stroke=C["navy"])
        s.text(x - 150, 528, n, size=20, weight=700, fill=C["white"])
        s.text(x + 20, 512, head, size=18, weight=700, fill=C["ink"])
        s.lines(x + 20, 548, body, size=14, step=24, anchor="middle", fill=C["grey"])
    s.arrow(400, 520, 428, 520, stroke=C["line"], sw=2.5)
    s.arrow(760, 520, 788, 520, stroke=C["line"], sw=2.5)
    s.text(600, 620, "같은 방식이 GitHub, Replit, 클라우드 서버 어디서나 쓰입니다.", size=15, fill=C["grey"])
    return s


# ----------------------------------------------------------------------
# 6. 22번 문 하나로
# ----------------------------------------------------------------------
def d_one_door():
    s = SVG("22번 문 하나로 — SSH 위에서 도는 것들")
    title(s, "22번 문 하나로 — SSH 위에서 도는 것들")

    # 서버
    s.rect(800, 100, 340, 450, fill=C["pale"])
    s.text(970, 140, "서버", size=24, weight=700)
    s.door(785, 290, 44, 90, "22", sub="SSH")
    s.rect(860, 285, 250, 100, fill=C["light"], stroke=C["blue"])
    s.text(985, 322, "SSH 서버 (sshd)", size=20, weight=700, fill=C["navy"])
    s.text(985, 348, "암호화 · 신원 확인 · 로그인을", size=14, fill=C["grey"])
    s.text(985, 368, "한 번에 처리", size=14, fill=C["grey"])
    s.text(970, 430, "문은 22번 하나만 열어 두면 된다", size=16, weight=700, fill=C["ink"])
    s.text(970, 458, "→ 방화벽 설정이 단순해지고", size=14, fill=C["grey"])
    s.text(970, 480, "   지켜야 할 곳도 하나뿐", size=14, fill=C["grey"])

    items = [("원격 셸 (터미널)", "명령을 내리고 결과를 본다"),
             ("SFTP", "파일 올리고 내리기 — FileZilla의 SFTP가 이것"),
             ("scp", "파일 한 개를 명령 한 줄로 복사"),
             ("Git", "git@github.com — 키로 push · pull"),
             ("포트 포워딩 (터널)", "서버 안에서만 열린 DB를 내 컴퓨터에서 안전하게")]
    for i, (head, sub) in enumerate(items):
        y = 110 + i * 86
        s.rect(60, y, 440, 68, fill=C["white"], stroke=C["blue"], sw=2)
        s.text(80, y + 30, head, size=19, weight=700, anchor="start", fill=C["navy"])
        s.text(80, y + 54, sub, size=14, anchor="start", fill=C["grey"])
        s.arrow(504, y + 34, 782, 335, stroke=C["blue"], sw=2.5, head=11)

    s.rect(60, 572, 1080, 70, fill=C["amberbg"], stroke="#F3D7A3", sw=2)
    s.text(600, 600, "옛날에는 문이 따로따로였습니다: Telnet 23번, FTP 21번(+데이터 연결마다 또 하나)…", size=16, fill=C["amber"], weight=700)
    s.text(600, 626, "문이 많으면 방화벽에서 지켜야 할 곳도 많고, 그 문들은 모두 암호화도 없었습니다.", size=14, fill=C["amber"])
    return s


DIAGRAMS = [
    ("ftp-01-transfer", d_ftp_transfer),
    ("ftp-02-postcard", d_postcard),
    ("ftp-03-family", d_family),
    ("ssh-01-terminal", d_terminal),
    ("ssh-02-keypair", d_keypair),
    ("ssh-03-one-door", d_one_door),
]


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    svg_dir = os.path.join(out, "svg")
    png_dir = os.path.join(out, "png")
    os.makedirs(svg_dir, exist_ok=True)
    os.makedirs(png_dir, exist_ok=True)
    try:
        import cairosvg
    except ImportError:
        cairosvg = None
        print("cairosvg가 없어 SVG만 만듭니다. (pip install cairosvg)")
    for name, fn in DIAGRAMS:
        svg = fn().render()
        p = os.path.join(svg_dir, name + ".svg")
        with open(p, "w", encoding="utf-8") as f:
            f.write(svg)
        if cairosvg:
            cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=os.path.join(png_dir, name + ".png"), output_width=2400)
        print("만듦:", name)


if __name__ == "__main__":
    main()

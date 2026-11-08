# -*- coding: utf-8 -*-
"""
SCX NEXT v1.4.3 - 구역별 위험작업 집중도(위험지수) 현장배치도
- 원본 배치도 레이아웃을 재구성하되 점선 원(TC 작업반경)·동선 화살표는 제거
- 각 세부구역 박스: 위험지수(0~100) + 아차 / 경보 / 혼재슬롯 / 미조치
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib import font_manager as fm
import matplotlib.colors as mcolors

U = "/home/user/uploaded_files/"
OUT = "/home/user/webapp/output/"
import os
os.makedirs(OUT, exist_ok=True)

# ---------- 폰트 ----------
for fp in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
           "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"]:
    if os.path.exists(fp):
        fm.fontManager.addfont(fp)
plt.rcParams["font.family"] = "NanumBarunGothic"
plt.rcParams["axes.unicode_minus"] = False

# ---------- 데이터 ----------
cam = pd.read_csv(U + "04_camera_object_log.csv", encoding="utf-8-sig")
nm = pd.read_csv(U + "10_near_miss_reports.csv", encoding="utf-8-sig")
ins = pd.read_csv(U + "09_inspection_action_log.csv", encoding="utf-8-sig")

# 중복 제거(품질 이슈 대비)
cam = cam.drop_duplicates(subset=["Camera_ID", "Slot_Start"])
nm = nm.drop_duplicates(subset=["NearMiss_ID"])
ins = ins.drop_duplicates(subset=["Inspection_ID"])

# 혼재슬롯: 동일 1시간 슬롯에 작업자(People>0)와 장비/차량/양중이 동시에 존재
cam["mixed"] = ((cam.People_Count > 0) &
                ((cam.Forklift_Count + cam.Excavator_Count + cam.Truck_Count > 0) |
                 (cam.Crane_Active == 1))).astype(int)

subzones = ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "C1", "C2", "C3", "D1", "D2", "D3"]
m = pd.DataFrame(index=subzones)
m["nearmiss"] = nm.groupby("Subzone").size()
m["alert"] = cam.groupby("Subzone")["Proximity_Alert_Count"].sum()
m["mixed"] = cam.groupby("Subzone")["mixed"].sum()
m["open"] = ins[ins.Status != "Closed"].groupby("Subzone").size()   # Open + In Progress
m = m.fillna(0).astype(int)

# ---------- 위험지수 (0~100) ----------
# 각 지표를 전 구역 최대값 기준 0~1 정규화 후 가중합 (가정: 가중치 아래와 같음)
W = {"nearmiss": 0.30, "alert": 0.25, "mixed": 0.25, "open": 0.20}
norm = m / m.max()
m["risk_index"] = (sum(norm[k] * w for k, w in W.items()) * 100).round(0).astype(int)

def level(v):
    return "매우높음" if v >= 60 else "높음" if v >= 40 else "보통" if v >= 20 else "낮음"
m["level"] = m.risk_index.map(level)
m = m.sort_values("risk_index", ascending=False)
m.to_csv(OUT + "zone_risk_index.csv", encoding="utf-8-sig")
print(m)

# ---------- 레이아웃 ----------
names = {
    "A1": "1동 코어·벽체", "A2": "슬래브·타설 작업면", "A3": "양중·호이스트 거점", "A4": "펌프카 거치·레미콘 연결",
    "B1": "메인게이트", "B2": "일반자재 하역장", "B3": "자재 적치장",
    "C1": "포디움 외장", "C2": "커튼월 적치·TC-02 양중", "C3": "이동식크레인(MC-01)",
    "D1": "지하램프(진입부)", "D2": "설비(지하2층)", "D3": "토목·방수(지하3층)",
}
# (x, y, w, h) : 좌표계 0~100 x 0~72
boxes = {
    "B1": (41, 61.5, 18, 6.5),
    "A3": (3, 46, 17, 10), "A4": (22, 46, 18, 10), "B2": (42, 46, 17, 10), "B3": (61, 46, 17, 10),
    "A1": (3, 20, 17, 23), "A2": (22, 20, 18, 23), "C1": (42, 20, 17, 23), "C2": (61, 20, 17, 23), "C3": (81, 20, 16, 23),
    "D1": (42, 5, 17, 11), "D2": (61, 5, 17, 11), "D3": (81, 5, 16, 11),
}

cmap = mcolors.LinearSegmentedColormap.from_list(
    "risk", ["#ffffff", "#fff3c4", "#fdbf6f", "#f4743b", "#c0182b"])
normc = mcolors.Normalize(vmin=0, vmax=100)

fig = plt.figure(figsize=(16, 11.5), dpi=150)
ax = fig.add_axes([0.02, 0.02, 0.96, 0.96])
ax.set_xlim(0, 100); ax.set_ylim(-6, 84); ax.axis("off")

# 제목
ax.text(50, 82.5, "SCX NEXT 가상 도심지 복합시설 건설현장 – 구역별 위험작업 집중도 지도 (v1.4.3 데이터 기준)",
        ha="center", va="center", fontsize=15, fontweight="bold")
# 북측 도로 밴드
ax.add_patch(Rectangle((0, 75), 100, 5, fc="#e6e6e6", ec="none"))
ax.text(50, 77.5, "북측 도시도로 / 상가 전면", ha="center", va="center", fontsize=12, fontweight="bold")
# 외곽 경계
ax.add_patch(Rectangle((0.5, 1), 99, 73, fc="white", ec="black", lw=2))
# 보행통로
ax.add_patch(Rectangle((1, 70.5), 98, 3, fc="#dff0d8", ec="#5a9a4a", lw=1))
ax.text(97.5, 72, "외부 보호보행통로(상시 개방)", ha="right", va="center", fontsize=9, color="#2d6a2d")
# 현장 내 통로 영역(연한 회색)
ax.add_patch(Rectangle((1.5, 2), 97, 66.5, fc="#f7f7f7", ec="#bbbbbb", lw=0.8, ls="-"))
ax.text(2.5, 67, "현장 내 통로", fontsize=8, color="#777777", va="center")
# 지하층 구획 안내
ax.add_patch(Rectangle((41, 3.5), 57, 14, fc="none", ec="#8c8c8c", lw=0.8, ls=(0, (3, 2))))
ax.text(41.5, 17.9, "지하층(D) – 램프 진입부·B2F·B3F", fontsize=8, color="#666666", va="bottom")

def badge_color(v):
    return "#c0182b" if v >= 60 else "#f4743b" if v >= 40 else "#e0a800" if v >= 20 else "#5a9a4a"

for sz, (x, y, w, h) in boxes.items():
    r = m.loc[sz]
    fc = cmap(normc(r.risk_index))
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.6",
                                fc=fc, ec="#444444", lw=1.3))
    big = h >= 15
    txt_color = "white" if r.risk_index >= 55 else "#222222"
    sub_color = "white" if r.risk_index >= 55 else "#333333"

    # 구역명
    ax.text(x + w / 2, y + h - (2.0 if big else 1.6), f"{sz} {names[sz]}",
            ha="center", va="center", fontsize=10.5 if big else 9.5, fontweight="bold", color=txt_color)

    # 위험지수 배지
    by = y + h / 2 + (2.2 if big else 0.6)
    bw, bh = (12.5, 4.2) if big else (10.5, 3.2)
    ax.add_patch(FancyBboxPatch((x + w / 2 - bw / 2, by - bh / 2), bw, bh,
                                boxstyle="round,pad=0,rounding_size=0.8",
                                fc=badge_color(r.risk_index), ec="white", lw=1.2))
    ax.text(x + w / 2, by, f"위험지수 {r.risk_index}  ·  {r.level}",
            ha="center", va="center", fontsize=10 if big else 8.5, fontweight="bold", color="white")

    # 4개 지표
    if big:
        ax.plot([x + 1.5, x + w - 1.5], [y + h / 2 - 1.2] * 2, color=sub_color, lw=0.6, alpha=0.6)
        items = [("아차", r.nearmiss, "건"), ("경보", r.alert, "건"),
                 ("혼재슬롯", r.mixed, "슬롯"), ("미조치", r.open, "건")]
        for i, (lab, val, unit) in enumerate(items):
            cx = x + w * (i + 0.5) / 4
            ax.text(cx, y + h / 2 - 3.2, lab, ha="center", va="center", fontsize=8.5, color=sub_color)
            ax.text(cx, y + h / 2 - 6.0, f"{val}", ha="center", va="center", fontsize=13,
                    fontweight="bold", color=txt_color)
            ax.text(cx, y + h / 2 - 8.2, unit, ha="center", va="center", fontsize=7, color=sub_color)
    else:
        ax.text(x + w / 2, y + (1.9 if h > 7 else 1.3),
                f"아차 {r.nearmiss} · 경보 {r.alert} · 혼재슬롯 {r.mixed} · 미조치 {r.open}",
                ha="center", va="center", fontsize=8.3 if w >= 17 else 7.8, color=sub_color)

# TC 위치 마커(반경 원은 제거, 위치만 표기)
ax.plot(31, 44.6, marker="^", color="#c0182b", ms=9, mec="white"); ax.text(32.3, 44.6, "TC-01", fontsize=8, color="#c0182b", va="center")
ax.plot(69, 30, marker="^", color="#6a3fa0", ms=9, mec="white"); ax.text(70.3, 30, "TC-02", fontsize=8, color="#6a3fa0", va="center")

# 컬러바
cax = fig.add_axes([0.075, 0.165, 0.22, 0.016])
cb = matplotlib.colorbar.ColorbarBase(cax, cmap=cmap, norm=normc, orientation="horizontal")
cb.set_ticks([0, 20, 40, 60, 80, 100]); cb.ax.tick_params(labelsize=8)
cb.set_label("위험지수 (0~100)", fontsize=8.5, fontweight="bold")
ax.text(3.5, 16.2, "범례 : 박스 색상 = 위험지수  /  배지 색 : 낮음 <20 · 보통 20~39 · 높음 40~59 · 매우높음 ≥60", fontsize=8, color="#333333", va="center")
ax.text(3.5, 14.4, "박스 하단 4개 지표 = 아차(아차사고 건수) · 경보(근접경보 건수) · 혼재슬롯(인력·장비 동시검출 1시간 슬롯 수) · 미조치(미완료 지적 건수)", fontsize=7.6, color="#555555", va="center")

# 상위 3 구역 요약
top = m.head(3)
summary = "  |  ".join(f"{i}위 {sz} ({int(r.risk_index)})" for i, (sz, r) in enumerate(top.iterrows(), 1))
ax.text(2, -0.8, f"■ 위험작업 집중 상위 구역 : {summary}", fontsize=10, fontweight="bold", color="#8a1a1a", va="center")

# 각주
foot = (
    "지표 정의 (분석기간 2026-10-05~10-31, 분석용 CSV 기준)  아차: 10_near_miss_reports 건수 | 경보: 04_camera_object_log Proximity_Alert_Count 합계(교육용 가상 근접 이벤트) | "
    "혼재슬롯: 04 로그에서 작업자(People>0)와 지게차·굴착기·차량 또는 양중(Crane_Active)이\n같은 1시간 슬롯에 동시 검출된 슬롯 수 | 미조치: 09_inspection_action_log 중 Status가 Open·In Progress인 지적 건수(10/31 기준)\n"
    "위험지수(가정): 각 지표를 전 구역 최대값으로 0~1 정규화 후 가중합(아차 0.30·경보 0.25·혼재슬롯 0.25·미조치 0.20)×100. 교육용 가상 데이터이며 정답값이 아님. "
    "축척 없는 개념배치도로 구역 간 관계 이해용이며, 원본의 TC 작업반경 원·동선 화살표는 가독성을 위해 제거함."
)
ax.text(2, -3.9, foot, fontsize=7.2, color="#444444", va="center", linespacing=1.5)

fig.savefig(OUT + "zone_risk_map.png", dpi=150, facecolor="white")
print("saved", OUT + "zone_risk_map.png")

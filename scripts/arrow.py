from typing import List, Optional
import json
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.ticker as mticker
import numpy as np
from datetime import datetime, timedelta
from glob import glob
from os import path


class PositionData:
    def __init__(
        self, fromName: str, lat: float, lon: float, unixTime: int, imageLength: int
    ):
        self.fromName = fromName
        self.lat = lat
        self.lon = lon
        self.unixTime = unixTime
        self.imageLength = imageLength


class EventData:
    def __init__(self, fromName: str, toName: str, unixTime: int, eventType: str):
        self.fromName = fromName
        self.toName = toName
        self.unixTime = unixTime
        self.eventType = eventType

    def toString(self) -> str:
        return f"{self.fromName} -> {self.toName} : {self.eventType} : {self.unixTime}"


class Arrow:
    def __init__(self, fromName: str, toName: str):
        self.fromName = fromName
        self.toName = toName


class Point:
    def __init__(self, name: str, lat: float, lon: float, color: str):
        self.name = name
        self.lat = lat
        self.lon = lon
        self.color = color


class Log:
    def __init__(
        self, name: str, positions: List[PositionData], events: List[EventData]
    ):
        self.name = name
        self.events = events
        self.positions = positions

    def getPoint(self, frameTime: int) -> Optional[Point]:
        pos = [p for p in self.positions if p.unixTime <= frameTime]
        if not pos:  # データが無い場合はNone
            return None
        eve = [e for e in self.events if e.unixTime <= frameTime]
        if not eve or eve[-1].eventType == "stopSearch":
            return Point(pos[-1].fromName, pos[-1].lat, pos[-1].lon, "gray")
        if eve[-1].eventType == "startSearch":
            return Point(pos[-1].fromName, pos[-1].lat, pos[-1].lon, "blue")
        else:
            return Point(pos[-1].fromName, pos[-1].lat, pos[-1].lon, "red")

    def getArrows(self, frameTime: int) -> list[Arrow]:
        arrows: list[Arrow] = []
        receiveEvents = [
            event for event in self.events if event.eventType == "imageReceived"
        ]
        if receiveEvents:
            minEvent = min(receiveEvents, key=lambda x: abs(x.unixTime - frameTime))
            if abs(minEvent.unixTime - frameTime) < 30000:
                arrows.append(Arrow(minEvent.fromName, minEvent.toName))
        return arrows

    def minLon(self) -> float:
        return min([p.lon for p in self.positions])

    def maxLon(self) -> float:
        return max([p.lon for p in self.positions])

    def minLat(self) -> float:
        return min([p.lat for p in self.positions])

    def maxLat(self) -> float:
        return max([p.lat for p in self.positions])


class Logs:
    def __init__(self, logs: List[Log]) -> None:
        self.logs = logs

    def minTime(self) -> int:
        return min([log.positions[0].unixTime for log in self.logs])

    def maxTime(self) -> int:
        return max([log.positions[-1].unixTime for log in self.logs])

    def minLat(self) -> float:
        return min([log.minLat() for log in self.logs])

    def maxLat(self) -> float:
        return max([log.maxLat() for log in self.logs])

    def minLon(self) -> float:
        return min([log.minLon() for log in self.logs])

    def maxLon(self) -> float:
        return max([log.maxLon() for log in self.logs])


class Frame:
    def __init__(self, unixtime: int, points: List[Point], arrows: List[Arrow]) -> None:
        self.unixtime = unixtime
        self.points = points
        self.arrows = arrows


class TA:
    def __init__(self, centerLon: float, centerLat: float, size: float):
        self.minLat = centerLat - size
        self.maxLat = centerLat + size
        self.minLon = centerLon - size
        self.maxLon = centerLon + size
        self.size = size

    def squareX(self) -> List[float]:
        return [self.maxLon, self.minLon, self.minLon, self.maxLon, self.maxLon]

    def squareY(self) -> List[float]:
        return [self.maxLat, self.maxLat, self.minLat, self.minLat, self.maxLat]

    def xLim(self) -> tuple[float, float]:
        return (self.minLon - self.size / 4, self.maxLon + self.size / 4)

    def yLim(self) -> tuple[float, float]:
        return (self.minLat - self.size / 4, self.maxLat + self.size / 4)


def parseLogData(name: str, logData: dict) -> Log:
    positions = []
    events = []
    for record in logData:
        if "latitude" in record:
            positions.append(
                PositionData(
                    name,
                    float(record["latitude"]),
                    float(record["longitude"]),
                    int(record["unixTime"]),
                    int(record["imageLength"]),
                )
            )
        else:
            events.append(
                EventData(
                    record["from"],
                    record.get("to", ""),
                    int(record["unixTime"]),
                    record["event"],
                )
            )
    return Log(name, positions, events)


def makeFrameTimes(minTime: int, maxTime: int) -> list:
    frameTimes = []
    current = minTime
    while current <= maxTime:
        frameTimes.append(current)
        current += 10000
    return frameTimes


def loadData(filePath: str) -> dict:
    with open(filePath, "r") as f:
        return json.load(f)


def getLogs(data_dir: str) -> Logs:
    json_files = glob(path.join(data_dir, "*.json"))
    logs: list[Log] = []
    for json_file in json_files:
        logData = loadData(json_file)
        name = path.basename(json_file).replace(".json", "")
        logs.append(parseLogData(name, logData))
    return Logs(logs)


def main():
    data_dir = "C:\\Users\\showe\\Desktop\\experiment\\clean\\2025_02_06"
    font_size = 17
    plt.rcParams["font.size"] = 15
    plt.rcParams["font.family"] = "HackGen Console NF"

    logs = getLogs(data_dir)

    frameTimes = makeFrameTimes(logs.minTime(), logs.maxTime())

    frames: list[Frame] = []
    for frameTime in frameTimes:
        points: list[Point] = []
        arrows: list[Arrow] = []
        for log in logs.logs:
            point = log.getPoint(frameTime)
            arrows += log.getArrows(frameTime)
            if point is not None:
                points.append(point)

        frames.append(Frame(frameTime, points, arrows))

    fig, ax = plt.subplots(figsize=(11, 7))
    point = ax.scatter([], [], c="r", s=100, edgecolors="k", zorder=3)

    # TA
    ta = TA(138.9392, 37.86678, 0.001)
    ax.set_xlim(ta.xLim())
    ax.set_ylim(ta.yLim())
    ax.plot(ta.squareX(), ta.squareY(), "r-", alpha=0.5)
    building = TA(138.9392, 37.86678, 0.0004)
    ax.plot(building.squareX(), building.squareY(), "k--", alpha=0.5)

    # 軸の設定
    ax.xaxis.set_major_locator(mticker.MultipleLocator(0.001))
    ax.yaxis.set_major_locator(mticker.MultipleLocator(0.001))
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.4f"))
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.4f"))
    ax.set_xlabel("経度", fontsize=font_size)  # x軸のラベルのフォントサイズを変更
    ax.set_ylabel("緯度", fontsize=font_size)  # y軸のラベルのフォントサイズを変更
    ax.tick_params(axis="both", labelsize=font_size)

    arrow_lines = []

    def update(frame):
        if frame >= len(frames):
            return (point,)  # もうデータがない場合

        current: Frame = frames[frame]  # 現在のフレームのデータを取得
        # すべての点の座標と色をリストで取得
        lons = [p.lon for p in current.points]
        lats = [p.lat for p in current.points]
        colors = [p.color for p in current.points]
        arrows = current.arrows

        # 全ての点をまとめて更新
        point.set_offsets(np.c_[lons, lats])
        point.set_color(colors)
        # 前のフレームで描画した矢印を削除
        for line in arrow_lines:
            line.remove()
        arrow_lines.clear()

        # 矢印情報をもとに点同士を線で繋ぐ
        for arrow in current.arrows:
            # 対応する点を名前で検索（各 Point インスタンスは name 属性を持つと仮定）
            sender = next((p for p in current.points if p.name == arrow.fromName), None)
            receiver = next((p for p in current.points if p.name == arrow.toName), None)
            if sender and receiver:
                ann = ax.annotate(
                    "",
                    xy=(receiver.lon, receiver.lat),
                    xytext=(sender.lon, sender.lat),
                    arrowprops=dict(arrowstyle="->", color="grey", lw=6),
                )
                arrow_lines.append(ann)

        # タイトルを更新
        dt = datetime.fromtimestamp(current.unixtime / 1000)
        formatted = dt.strftime("%Y-%m-%d %H:%M:%S")
        ax.set_title(f"{formatted}\n")

        return (point, *arrow_lines)

    ani = animation.FuncAnimation(
        fig, update, frames=len(frames), interval=200, blit=False
    )

    # アニメーションを保存
    ani.save("anim6.mp4", writer="ffmpeg")


main()

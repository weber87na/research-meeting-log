# 研究 meeting 紀錄與字幕工具

各次 meeting 資料夾只保留最終字幕 `.srt` 與會議摘要 `.md`。影片、原始辨識、分段檔、校對中間檔及上傳紀錄不納入版本控制。

## 影片轉字幕

`transcribe_meeting.py` 使用完整 Whisper `large-v3`，自動選擇 CUDA（可用時）或 CPU，每 15 分鐘保存進度。需要已安裝 `openai-whisper`、PyTorch 與 FFmpeg 的 Python 環境；GPU 執行需要支援 CUDA 的 PyTorch。

```powershell
python transcribe_meeting.py "meeting資料夾/影片.mp4"
```

若 FFmpeg 不在 PATH，可加 `--ffmpeg-bin "FFmpeg的bin資料夾"`；另支援 `--output-dir` 及 `--model-dir`。模型預設保存在專案 `.models/`，不推送到 GitHub。重新執行同一影片會沿用相同設定的已完成分段。字幕仍需要人工或 agent 依上下文校對，尤其是人名、外文名稱及靜音區間的異常文字。

## 字幕簡轉繁

使用 `uv` 管理 Python 環境，透過 [OpenCC](https://github.com/BYVoid/OpenCC) 的 `s2twp` 規則，將簡體中文轉為台灣繁體中文及常見詞彙，例如「软件 → 軟體」、「鼠标 → 滑鼠」。首次執行會自動建立 `.venv` 並安裝依賴。

在本專案目錄執行（路徑請換成實際字幕檔）：

```powershell
uv run python convert_subtitles.py "第四次-meeting-2026-09-08/字幕.srt"
```

預設在同一資料夾產生 `字幕_zh_tw.srt`，保留原檔。也可以指定輸出位置（資料夾需已存在）：

```powershell
uv run python convert_subtitles.py "簡體字幕.srt" -o "繁體字幕.srt"
```

支援 UTF-8 編碼的 SRT，保留 BOM、換行格式、字幕編號、時間軸與字幕標籤。若輸出檔已存在會停止，避免覆蓋。

這是字詞轉換，不會重新潤稿或修正語音辨識錯字；人名、專有名詞與需要語境判斷的用語，仍建議人工確認。

完成轉繁與校對後，只將最終字幕及摘要留在 meeting 資料夾。`convert_subtitles.py`、`transcribe_meeting.py`、依賴設定與測試集中在專案根目錄；本機環境與模型不提交。

執行測試：

```powershell
uv run python -m unittest discover -s tests
```

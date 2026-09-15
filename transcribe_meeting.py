"""Transcribe a meeting with Whisper large-v3; keep checkpoints beside the video."""
import argparse
import json
import os
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('video', type=Path)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--model-dir', type=Path, default=Path(__file__).resolve().parent / '.models')
    parser.add_argument('--ffmpeg-bin', type=Path, help='Directory containing ffmpeg.exe, if absent from PATH')
    args = parser.parse_args()
    video = args.video.resolve()
    if not video.is_file():
        parser.error(f'Video does not exist: {video}')
    if args.ffmpeg_bin:
        os.environ['PATH'] = str(args.ffmpeg_bin.resolve()) + os.pathsep + os.environ['PATH']
    if not shutil.which('ffmpeg'):
        parser.error('Install FFmpeg or supply --ffmpeg-bin')

    import torch
    import whisper
    from whisper.utils import get_writer

    root = (args.output_dir or video.parent).resolve()
    root.mkdir(parents=True, exist_ok=True)
    parts = root / f'{video.stem}_whisper_parts'
    parts.mkdir(exist_ok=True)
    # Refuse to reuse checkpoints from another input or an older configuration.
    settings = {'video': str(video), 'size': video.stat().st_size,
                'mtime_ns': video.stat().st_mtime_ns, 'model': 'large-v3',
                'chunk_seconds': 900, 'language': 'zh', 'beam_size': 5,
                'best_of': 5, 'condition_on_previous_text': False, 'initial_prompt': None}
    marker = parts / 'settings.json'
    if marker.exists() and json.loads(marker.read_text(encoding='utf-8')) != settings:
        parser.error('Checkpoint settings differ; choose another --output-dir')
    marker.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding='utf-8')

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f'Loading large-v3 on {device}', flush=True)
    model = whisper.load_model('large-v3', device='cpu', download_root=str(args.model_dir))
    if device == 'cuda':
        model = model.half().to(device)
        # Whisper LayerNorm calculates in float32 even with half-precision weights.
        for module in model.modules():
            if isinstance(module, torch.nn.LayerNorm):
                module.float()
    audio = whisper.load_audio(str(video))
    segments = []
    for i, start in enumerate(range(0, len(audio), 900 * 16000), 1):
        checkpoint = parts / f'part_{i:02d}.json'
        if checkpoint.exists():
            result = json.loads(checkpoint.read_text(encoding='utf-8'))
        else:
            print(f'Transcribing part {i}', flush=True)
            result = model.transcribe(audio[start:start + 900 * 16000],
                language='zh', task='transcribe', fp16=device == 'cuda',
                beam_size=5, best_of=5, temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
                condition_on_previous_text=False, verbose=False)
            for segment in result['segments']:
                segment['start'] += start / 16000
                segment['end'] += start / 16000
            temporary = checkpoint.with_suffix('.json.tmp')
            temporary.write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
            temporary.replace(checkpoint)
        get_writer('srt', str(parts))(result, f'part_{i:02d}')
        segments.extend(result['segments'])
    for i, segment in enumerate(segments):
        segment['id'] = i
    combined = {'language': 'zh', 'segments': segments,
                'text': ''.join(segment['text'] for segment in segments)}
    stem = f'{video.stem}_whisper'
    (root / f'{stem}.json').write_text(json.dumps(combined, ensure_ascii=False), encoding='utf-8')
    get_writer('srt', str(root))(combined, stem)
    print(f'Completed: {root / (stem + ".srt")}')


if __name__ == '__main__':
    main()

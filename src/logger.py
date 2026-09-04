import logging
import sys
from pathlib import Path


def setup_logger(log_dir: Path | None = None) -> logging.Logger:
    """コンソールおよびファイル出力用ロガーをセットアップする。

    - コンソール: 重要な進捗とエラー（見やすい要約）
    - ファイル (logs/app.log): 詳細なデバッグ情報、スタックトレース (UTF-8)
    """
    if log_dir is None:
        log_dir = Path("./logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "app.log"

    logger = logging.getLogger("movie_auto_cutter")
    logger.setLevel(logging.DEBUG)

    # 既存のハンドラーがあればクリア（重複防止）
    if logger.hasHandlers():
        logger.handlers.clear()

    # ファイルハンドラー (詳細ログ・スタックトレース記録)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # コンソールハンドラー (ユーザー向け進捗)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger

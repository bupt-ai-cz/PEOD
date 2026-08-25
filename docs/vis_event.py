#!/usr/bin/env python3
"""
Batch processing of event camera data to red-blue images.
Processes multiple .dat files with corresponding timestamp CSVs,
generating red-blue event images with a 33ms time window.
Supports multi-threaded acceleration.
"""

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
import cv2
import os
import argparse
import time
import tqdm
from typing import Tuple, List, Optional
import glob
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from src.io import psee_loader
    from src.io import npy_events_tools
    from numpy.lib import recfunctions as rfn
    PSEE_AVAILABLE = True
except ImportError:
    try:
        import psee_loader
        import npy_events_tools
        from numpy.lib import recfunctions as rfn
        PSEE_AVAILABLE = True
    except ImportError:
        print("Warning: PSEE tools not found, using fallback simulation mode.")
        PSEE_AVAILABLE = False


def generate_red_blue_frame(events, shape, background_white=True):
    """
    Generate a red-blue event image.

    Args:
        events: N x 4 tensor with columns [x, y, t, polarity]
        shape: [H, W] image size
        background_white: whether to use a white background

    Returns:
        RGB image tensor (3, H, W); positive events = red, negative events = blue
    """
    H, W = shape

    if len(events) == 0:
        if background_white:
            return torch.ones((3, H, W), dtype=torch.float32) * 255
        else:
            return torch.zeros((3, H, W), dtype=torch.float32)

    x, y, t, p = events.unbind(-1)
    x, y, p = x.long(), y.long(), p.long()

    valid_mask = (x >= 0) & (x < W) & (y >= 0) & (y < H)
    x = x[valid_mask]
    y = y[valid_mask]
    p = p[valid_mask]

    if len(x) == 0:
        if background_white:
            return torch.ones((3, H, W), dtype=torch.float32) * 255
        else:
            return torch.zeros((3, H, W), dtype=torch.float32)

    if background_white:
        img = torch.ones((3, H, W), dtype=torch.float32, device=x.device) * 255
    else:
        img = torch.zeros((3, H, W), dtype=torch.float32, device=x.device)

    indices = y * W + x

    pos_mask = p == 1
    if torch.any(pos_mask):
        pos_indices = indices[pos_mask]
        img[2].view(-1).index_fill_(0, pos_indices, 255)
        if background_white:
            img[0].view(-1).index_fill_(0, pos_indices, 0)
            img[1].view(-1).index_fill_(0, pos_indices, 0)

    neg_mask = p == 0
    if torch.any(neg_mask):
        neg_indices = indices[neg_mask]
        img[0].view(-1).index_fill_(0, neg_indices, 255)
        if background_white:
            img[1].view(-1).index_fill_(0, neg_indices, 0)
            img[2].view(-1).index_fill_(0, neg_indices, 0)

    return img


class ThreadSafeProgressBar:
    """Thread-safe progress bar wrapper."""

    def __init__(self, total, desc="Processing"):
        self.total = total
        self.desc = desc
        self.current = 0
        self.lock = threading.Lock()
        self.pbar = tqdm.tqdm(total=total, desc=desc, position=0, leave=True)

    def update(self, n=1):
        with self.lock:
            self.current += n
            self.pbar.update(n)

    def close(self):
        self.pbar.close()


class BatchEventProcessor:
    """Batch event file processor with multi-threading and multi-level directory support."""

    def __init__(self, dat_root: str, csv_root: str, output_root: str, num_threads: int = 4, splits=None):
        """
        Args:
            dat_root: root directory of .dat files (contains train/val/test)
            csv_root: root directory of timestamp CSVs (contains train/val/test)
            output_root: root output directory (contains train/val/test)
            num_threads: number of worker threads
            splits: list of splits to process
        """
        self.dat_root = dat_root
        self.csv_root = csv_root
        self.output_root = output_root
        self.shape = [720, 1280]
        self.num_threads = num_threads
        self.splits = splits if splits else ["train", "val", "test"]
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Device: {self.device}")
        print(f"Threads: {self.num_threads}")
        os.makedirs(self.output_root, exist_ok=True)
        self.print_lock = threading.Lock()

    def find_file_pairs(self) -> List[Tuple[str, str, str]]:
        """
        Recursively find all dat files and their matching CSVs under each split.

        Returns:
            List of (dat_file_path, csv_file_path, output_subdir)
        """
        file_pairs = []
        for split in self.splits:
            dat_split_dir = os.path.join(self.dat_root, split)
            csv_split_dir = os.path.join(self.csv_root, split)
            output_split_dir = os.path.join(self.output_root, split)
            for root, _, files in os.walk(dat_split_dir):
                for file in files:
                    if file.endswith('.dat'):
                        dat_file = os.path.join(root, file)
                        rel_path = os.path.relpath(dat_file, dat_split_dir)
                        rel_dir = os.path.dirname(rel_path)
                        csv_file = os.path.join(csv_split_dir, rel_dir, os.path.splitext(file)[0] + '.csv')
                        output_dir = os.path.join(output_split_dir, rel_dir, os.path.splitext(file)[0])
                        if os.path.exists(csv_file):
                            file_pairs.append((dat_file, csv_file, output_dir))
                            with self.print_lock:
                                print(f"Found pair: {dat_file} <-> {csv_file}")
                        else:
                            with self.print_lock:
                                print(f"Warning: no matching CSV found: {csv_file}")
        with self.print_lock:
            print(f"\nTotal file pairs found: {len(file_pairs)}")
        return file_pairs

    def load_timestamps(self, csv_file: str) -> List[int]:
        """Load trigger timestamps from a CSV file."""
        try:
            df = pd.read_csv(csv_file, header=None)
            timestamps = df.iloc[:, 1].tolist()
            return timestamps
        except Exception as e:
            with self.print_lock:
                print(f"Failed to load timestamps from {csv_file}: {e}")
            return []

    def load_events_in_window(self, dat_file: str, center_time_us: int, window_us: int = 33000) -> torch.Tensor:
        """
        Load events within a given time window.

        Args:
            dat_file: path to the .dat file
            center_time_us: window start time in microseconds
            window_us: window duration in microseconds

        Returns:
            Event tensor (N, 4) with columns [x, y, t, p]
        """
        if not PSEE_AVAILABLE:
            n_events = np.random.randint(1000, 10000)
            events_data = np.zeros((n_events, 4))
            events_data[:, 0] = np.random.randint(0, self.shape[1], n_events)
            events_data[:, 1] = np.random.randint(0, self.shape[0], n_events)
            events_data[:, 2] = np.linspace(center_time_us, center_time_us + window_us, n_events)
            events_data[:, 3] = np.random.choice([0, 1], n_events)
            return torch.from_numpy(events_data).float().to(self.device)

        try:
            f_event = psee_loader.PSEELoader(dat_file)
            end_time = center_time_us + window_us
            end_count = f_event.seek_time(end_time)

            if end_count is None:
                return torch.empty((0, 4)).to(self.device)

            start_time = center_time_us
            start_count = f_event.seek_time(start_time)

            if start_count is None:
                start_count = 0

            f_event.seek_event(start_count)
            events = f_event.load_n_events(int(end_count - start_count))

            if len(events) == 0:
                return torch.empty((0, 4)).to(self.device)

            events_array = rfn.structured_to_unstructured(events)[:, [1, 2, 0, 3]].astype(float)
            events_tensor = torch.from_numpy(events_array).float().to(self.device)

            time_mask = (events_tensor[:, 2] >= center_time_us) & (events_tensor[:, 2] < end_time)
            return events_tensor[time_mask]

        except Exception as e:
            with self.print_lock:
                print(f"Failed to load events: {e}")
            return torch.empty((0, 4)).to(self.device)

    def process_single_timestamp(self, dat_file: str, timestamp: int, output_subdir: str, index: int, base_name: str):
        """Process a single timestamp (thread-safe)."""
        try:
            events = self.load_events_in_window(dat_file, timestamp, window_us=33000)
            red_blue_img = generate_red_blue_frame(events, self.shape, background_white=True)
            img_np = red_blue_img.cpu().numpy().transpose(1, 2, 0).astype(np.uint8)
            output_path = os.path.join(output_subdir, f"redblue_{index+1:04d}_{timestamp}.png")
            cv2.imwrite(output_path, img_np)
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            return True
        except Exception as e:
            with self.print_lock:
                print(f"Error processing timestamp {timestamp}: {e}")
            return False

    def process_single_file_pair(self, dat_file: str, csv_file: str, output_subdir: str, progress_bar: Optional[ThreadSafeProgressBar] = None):
        """Process a single file pair with multi-threading support."""
        os.makedirs(output_subdir, exist_ok=True)
        dat_basename = os.path.basename(dat_file)
        base_name = os.path.splitext(dat_basename)[0]
        with self.print_lock:
            print(f"\nProcessing: {base_name}")
            print(f"  DAT: {dat_file}")
            print(f"  CSV: {csv_file}")
            print(f"  Output: {output_subdir}")
        timestamps = self.load_timestamps(csv_file)
        if not timestamps:
            with self.print_lock:
                print(f"Could not load timestamps, skipping: {csv_file}")
            return
        with self.print_lock:
            print(f"  Loaded {len(timestamps)} timestamps")
        if progress_bar is None:
            progress_bar = ThreadSafeProgressBar(len(timestamps), f"Processing {base_name}")
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            future_to_index = {}
            for i, timestamp in enumerate(timestamps):
                future = executor.submit(
                    self.process_single_timestamp,
                    dat_file, timestamp, output_subdir, i, base_name
                )
                future_to_index[future] = i
            completed = 0
            for future in as_completed(future_to_index):
                try:
                    success = future.result()
                    if success:
                        completed += 1
                    progress_bar.update(1)
                except Exception as e:
                    with self.print_lock:
                        print(f"Task failed: {e}")
                    progress_bar.update(1)
        progress_bar.close()
        with self.print_lock:
            print(f"Done: {base_name} ({completed}/{len(timestamps)} succeeded)")

    def process_all_files(self):
        """Process all file pairs using multiple threads."""
        file_pairs = self.find_file_pairs()
        if not file_pairs:
            print("No file pairs found.")
            return
        print(f"\nStarting batch processing of {len(file_pairs)} file pairs...")
        total_progress = ThreadSafeProgressBar(len(file_pairs), "Overall progress")
        with ThreadPoolExecutor(max_workers=min(self.num_threads, len(file_pairs))) as executor:
            future_to_file = {}
            for i, (dat_file, csv_file, output_dir) in enumerate(file_pairs):
                future = executor.submit(self.process_single_file_pair, dat_file, csv_file, output_dir)
                future_to_file[future] = (dat_file, csv_file)
            for future in as_completed(future_to_file):
                try:
                    future.result()
                    total_progress.update(1)
                except Exception as e:
                    dat_file, csv_file = future_to_file[future]
                    with self.print_lock:
                        print(f"Failed to process file pair {dat_file}: {e}")
                    total_progress.update(1)
        total_progress.close()
        print(f"\nBatch processing complete.")
        print(f"Output root: {self.output_root}")


def process_single_dat_csv(dat_file: str, csv_file: str, output_dir: str, shape=(720, 1280), device=None, num_threads=2):
    """Process a single dat/csv file pair and write outputs to the specified directory."""
    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    os.makedirs(output_dir, exist_ok=True)
    print(f"\nSingle file mode")
    print(f"  DAT: {dat_file}")
    print(f"  CSV: {csv_file}")
    print(f"  Output: {output_dir}")
    try:
        import pandas as pd
        df = pd.read_csv(csv_file, header=None)
        timestamps = df.iloc[:, 1].tolist()
    except Exception as e:
        print(f"Failed to load timestamps: {e}")
        return
    print(f"  Loaded {len(timestamps)} timestamps")
    from tqdm import tqdm
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def process_one(i, timestamp):
        try:
            if not PSEE_AVAILABLE:
                n_events = np.random.randint(1000, 10000)
                events_data = np.zeros((n_events, 4))
                events_data[:, 0] = np.random.randint(0, shape[1], n_events)
                events_data[:, 1] = np.random.randint(0, shape[0], n_events)
                events_data[:, 2] = np.linspace(timestamp, timestamp + 33000, n_events)
                events_data[:, 3] = np.random.choice([0, 1], n_events)
                events = torch.from_numpy(events_data).float().to(device)
            else:
                f_event = psee_loader.PSEELoader(dat_file)
                end_time = timestamp + 33000
                end_count = f_event.seek_time(end_time)
                if end_count is None:
                    return False
                start_count = f_event.seek_time(timestamp)
                if start_count is None:
                    start_count = 0
                f_event.seek_event(start_count)
                events_arr = f_event.load_n_events(int(end_count - start_count))
                if len(events_arr) == 0:
                    return False
                events_array = rfn.structured_to_unstructured(events_arr)[:, [1, 2, 0, 3]].astype(float)
                events = torch.from_numpy(events_array).float().to(device)
                time_mask = (events[:, 2] >= timestamp) & (events[:, 2] < end_time)
                events = events[time_mask]
            red_blue_img = generate_red_blue_frame(events, shape, background_white=True)
            img_np = red_blue_img.cpu().numpy().transpose(1, 2, 0).astype(np.uint8)
            output_path = os.path.join(output_dir, f"redblue_{i+1:04d}_{timestamp}.png")
            cv2.imwrite(output_path, img_np)
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            return True
        except Exception as e:
            print(f"Error processing timestamp {timestamp}: {e}")
            return False

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {executor.submit(process_one, i, ts): i for i, ts in enumerate(timestamps)}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Progress"):
            future.result()
    print(f"Single file processing complete. Output: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description='Batch event data to red-blue image conversion (multi-threaded)')
    parser.add_argument('--dat_root', type=str,
                        default='/home/DATA/usr/liuhanqing/C_dataset/Event_dat',
                        help='Root directory of .dat files (containing train/val/test)')
    parser.add_argument('--csv_root', type=str,
                        default='/home/DATA/usr/liuhanqing/C_dataset/timestamp_last',
                        help='Root directory of timestamp CSVs (containing train/val/test)')
    parser.add_argument('--output_root', type=str,
                        default='/home/DATA/usr/liuhanqing/C_dataset/Event_image_33',
                        help='Root output directory (containing train/val/test)')
    parser.add_argument('--num_threads', type=int, default=4,
                        help='Number of worker threads (default: 4)')
    parser.add_argument('--splits', type=str, nargs='*', default=['train', 'val', 'test'],
                        help='Dataset splits to process')
    parser.add_argument('--single_dat', type=str, default=None, help='Single dat file to process')
    parser.add_argument('--single_csv', type=str, default=None, help='Single csv file to process')
    parser.add_argument('--single_output_dir', type=str, default=None, help='Output directory for single file mode')
    args = parser.parse_args()

    if not os.path.exists(args.dat_root):
        print(f"Error: DAT root directory does not exist: {args.dat_root}")
        return
    if not os.path.exists(args.csv_root):
        print(f"Error: CSV root directory does not exist: {args.csv_root}")
        return

    if args.single_dat and args.single_csv and args.single_output_dir:
        process_single_dat_csv(args.single_dat, args.single_csv, args.single_output_dir, num_threads=args.num_threads)
        return

    print("Batch Event Processor - Multi-threaded")
    print("=" * 60)
    print(f"DAT root:    {args.dat_root}")
    print(f"CSV root:    {args.csv_root}")
    print(f"Output root: {args.output_root}")
    print(f"Threads:     {args.num_threads}")
    print(f"Splits:      {args.splits}")
    print("=" * 60)

    processor = BatchEventProcessor(args.dat_root, args.csv_root, args.output_root, args.num_threads, args.splits)
    start_time = time.time()
    processor.process_all_files()
    end_time = time.time()
    print(f"\nTotal time: {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    main()

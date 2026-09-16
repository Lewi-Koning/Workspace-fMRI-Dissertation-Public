from pathlib import Path
import time

import cv2
import deepgaze_pytorch
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from scipy.special import logsumexp


# --------------------------------------------------
# Folder settings
# --------------------------------------------------

VIDEO_FOLDER = Path(
    r"C:\Users\LewiK\OneDrive\Desktop\MRI_Dissertation\260707_fixedVids"
)

OUTPUT_FOLDER = Path(
    r"C:\Users\LewiK\OneDrive\Desktop\MRI_Dissertation"
    r"\Saliency_Analysis\results\video_saliency_maps"
)

OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# Processing settings
# --------------------------------------------------

DEVICE = "cpu"

# During the first test, leave this as 1.
# Once the test succeeds, change it to None.
MAX_VIDEOS = None

# Skip videos whose .npy output already exists.
# This is useful if processing is interrupted.
SKIP_EXISTING = True


# --------------------------------------------------
# Find the videos
# --------------------------------------------------

video_files = sorted(VIDEO_FOLDER.glob("*.mp4"))

if not video_files:
    raise FileNotFoundError(
        f"No MP4 files were found in:\n{VIDEO_FOLDER}"
    )

if MAX_VIDEOS is not None:
    video_files = video_files[:MAX_VIDEOS]

print(f"Videos to process: {len(video_files)}")


# --------------------------------------------------
# Load DeepGaze only once
# --------------------------------------------------

print("Loading DeepGaze IIE...")

model = deepgaze_pytorch.DeepGazeIIE(
    pretrained=True
).to(DEVICE)

model.eval()

print("DeepGaze IIE loaded successfully.")


# A dictionary lets us reuse a centre-bias tensor
# if all videos have the same frame dimensions.
centerbias_cache = {}

summary_rows = []


# --------------------------------------------------
# Process each video
# --------------------------------------------------

for video_number, video_path in enumerate(video_files, start=1):

    print()
    print("=" * 70)
    print(
        f"Video {video_number} of {len(video_files)}: "
        f"{video_path.name}"
    )

    npy_output_path = (
        OUTPUT_FOLDER
        / f"{video_path.stem}_mean_saliency.npy"
    )

    png_output_path = (
        OUTPUT_FOLDER
        / f"{video_path.stem}_mean_saliency.png"
    )

    overlay_output_path = (
        OUTPUT_FOLDER
        / f"{video_path.stem}_saliency_overlay.png"
    )

    if SKIP_EXISTING and npy_output_path.exists():

        print("Output already exists. Skipping this video.")

        summary_rows.append(
            {
                "video": video_path.name,
                "status": "skipped_existing",
                "decoded_frames": np.nan,
                "processing_seconds": np.nan,
                "npy_output": str(npy_output_path),
            }
        )

        continue

    video_start_time = time.perf_counter()

    capture = cv2.VideoCapture(str(video_path))

    if not capture.isOpened():

        print("ERROR: Could not open video.")

        summary_rows.append(
            {
                "video": video_path.name,
                "status": "open_failed",
                "decoded_frames": 0,
                "processing_seconds": 0,
                "npy_output": "",
            }
        )

        continue

    metadata_frame_count = int(
        capture.get(cv2.CAP_PROP_FRAME_COUNT)
    )

    fps = capture.get(cv2.CAP_PROP_FPS)

    print(f"Metadata frame count: {metadata_frame_count}")
    print(f"FPS: {fps:.2f}")

    decoded_frame_count = 0

    # We will add each frame's prediction into this array.
    saliency_sum = None

    # Save the first frame so that an overlay can be created.
    first_frame_rgb = None


    # --------------------------------------------------
    # Read and analyse every frame
    # --------------------------------------------------

    while True:

        success, frame_bgr = capture.read()

        if not success:
            break

        decoded_frame_count += 1

        frame_rgb = cv2.cvtColor(
            frame_bgr,
            cv2.COLOR_BGR2RGB
        )

        if first_frame_rgb is None:
            first_frame_rgb = frame_rgb.copy()

        height, width, channels = frame_rgb.shape


        # --------------------------------------------------
        # Create or retrieve the uniform centre bias
        # --------------------------------------------------

        frame_shape = (height, width)

        if frame_shape not in centerbias_cache:

            centerbias = np.zeros(
                frame_shape,
                dtype=np.float32
            )

            # Normalise it as a log-density.
            centerbias -= logsumexp(centerbias)

            centerbias_tensor = (
                torch.from_numpy(centerbias)
                .unsqueeze(0)
                .to(DEVICE)
            )

            centerbias_cache[frame_shape] = (
                centerbias_tensor
            )

        centerbias_tensor = centerbias_cache[frame_shape]


        # --------------------------------------------------
        # Convert frame to a PyTorch tensor
        # --------------------------------------------------

        frame_rgb = np.ascontiguousarray(frame_rgb)

        image_tensor = (
            torch.from_numpy(
                frame_rgb.transpose(2, 0, 1)
            )
            .unsqueeze(0)
            .to(DEVICE)
        )


        # --------------------------------------------------
        # Run DeepGaze
        # --------------------------------------------------

        with torch.no_grad():

            log_density_prediction = model(
                image_tensor,
                centerbias_tensor
            )


        # Select the first batch item and output channel.
        log_density = (
            log_density_prediction[0, 0]
            .detach()
            .cpu()
            .numpy()
        )

        # Convert log-density into ordinary density.
        frame_saliency = np.exp(log_density)


        # --------------------------------------------------
        # Add this frame to the running total
        # --------------------------------------------------

        if saliency_sum is None:

            saliency_sum = np.zeros_like(
                frame_saliency,
                dtype=np.float64
            )

        saliency_sum += frame_saliency


        # Display progress occasionally rather than
        # printing a message for every single frame.
        if (
            decoded_frame_count == 1
            or decoded_frame_count % 10 == 0
            or decoded_frame_count == metadata_frame_count
        ):

            print(
                f"Processed frame "
                f"{decoded_frame_count}/"
                f"{metadata_frame_count}"
            )


    capture.release()


    # --------------------------------------------------
    # Check that at least one frame was processed
    # --------------------------------------------------

    if decoded_frame_count == 0:

        print("ERROR: No frames were decoded.")

        summary_rows.append(
            {
                "video": video_path.name,
                "status": "decode_failed",
                "decoded_frames": 0,
                "processing_seconds": (
                    time.perf_counter()
                    - video_start_time
                ),
                "npy_output": "",
            }
        )

        continue


    # --------------------------------------------------
    # Calculate the mean saliency map
    # --------------------------------------------------

    mean_saliency = (
        saliency_sum / decoded_frame_count
    )

    # Because each frame is a probability distribution,
    # this should already be very close to summing to 1.
    # Renormalising protects against small numerical errors.
    mean_saliency /= mean_saliency.sum()

    print(f"Decoded frames: {decoded_frame_count}")
    print(
        "Mean saliency sum: "
        f"{mean_saliency.sum():.6f}"
    )


    # --------------------------------------------------
    # Save the exact numerical result
    # --------------------------------------------------

    np.save(
        npy_output_path,
        mean_saliency.astype(np.float32)
    )


    # --------------------------------------------------
    # Save a viewable saliency-map image
    # --------------------------------------------------

    plt.figure(figsize=(12, 7))

    saliency_image = plt.imshow(
        mean_saliency,
        cmap="inferno"
    )

    plt.title(
        f"Mean DeepGaze IIE saliency\n"
        f"{video_path.name}"
    )

    plt.axis("off")

    plt.colorbar(
        saliency_image,
        label="Mean predicted fixation density"
    )

    plt.tight_layout()

    plt.savefig(
        png_output_path,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close()


    # --------------------------------------------------
    # Save a saliency overlay on the first frame
    # --------------------------------------------------

    plt.figure(figsize=(12, 7))

    plt.imshow(first_frame_rgb)

    plt.imshow(
        mean_saliency,
        cmap="inferno",
        alpha=0.50
    )

    plt.title(
        f"Mean saliency overlay\n"
        f"{video_path.name}"
    )

    plt.axis("off")
    plt.tight_layout()

    plt.savefig(
        overlay_output_path,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close()


    # --------------------------------------------------
    # Record processing information
    # --------------------------------------------------

    elapsed_seconds = (
        time.perf_counter() - video_start_time
    )

    status = "completed"

    if decoded_frame_count != metadata_frame_count:
        status = "completed_frame_count_mismatch"

    summary_rows.append(
        {
            "video": video_path.name,
            "status": status,
            "metadata_frames": metadata_frame_count,
            "decoded_frames": decoded_frame_count,
            "fps": fps,
            "processing_seconds": elapsed_seconds,
            "npy_output": str(npy_output_path),
            "png_output": str(png_output_path),
            "overlay_output": str(
                overlay_output_path
            ),
        }
    )

    print(f"Saved: {npy_output_path.name}")
    print(f"Saved: {png_output_path.name}")
    print(f"Saved: {overlay_output_path.name}")
    print(
        f"Processing time: "
        f"{elapsed_seconds:.1f} seconds"
    )


# --------------------------------------------------
# Save a summary CSV
# --------------------------------------------------

summary_df = pd.DataFrame(summary_rows)

summary_csv_path = (
    OUTPUT_FOLDER / "saliency_processing_summary.csv"
)

summary_df.to_csv(
    summary_csv_path,
    index=False
)

print()
print("=" * 70)
print("Processing finished.")
print(f"Summary saved to:\n{summary_csv_path}")
from PIL import Image
import os, shutil
from pathlib import Path


def compress_image_pillow(
    input_path: Path, output_path: Path, quality=85, optimize=True
):
    """
    使用Pillow压缩图片
    quality: 质量(1-100)
    optimize: 是否优化
    """
    with Image.open(input_path) as img:
        # 转换为RGB模式（如果不是）
        if img.mode in ("RGBA", "LA", "P"):
            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = rgb_img

        # 保存时压缩
        img.save(
            output_path,
            "JPEG" if os.path.splitext(output_path)[1].lower() == ".jpg" else "PNG",
            quality=quality,
            optimize=optimize,
        )

    # 对比大小
    orig_size = os.path.getsize(input_path)
    comp_size = os.path.getsize(output_path)
    print(f"压缩率: {(1-comp_size/orig_size)*100:.1f}%")


# 进阶：调整尺寸并压缩
def resize_and_compress(
    input_path: Path, output_path: Path, max_size=(1920, 1080), quality=80
):
    with Image.open(input_path) as img:
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # 保存为渐进式JPEG（更好的网络加载体验）
        img.save(output_path, "JPEG", quality=quality, optimize=True, progressive=True)


def compress_image(
    input_path: Path,
    output_path: Path,
    temp_path: Path = Path("temp_compressed_image.jpg"),
    max_size=(1920, 1080),
    quality=80,
):
    """
    使用Pillow压缩图片
    quality: 质量(1-100)
    """
    if not temp_path.parent.exists():
        os.makedirs(temp_path.parent, exist_ok=True)
    if not temp_path.exists():
        temp_path.touch()
    with Image.open(input_path) as img:
        if img.mode in ("RGBA", "LA", "P"):
            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = rgb_img
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # 保存为渐进式JPEG（更好的网络加载体验）
        img.save(temp_path, "JPEG", quality=quality, optimize=True, progressive=True)
    shutil.move(temp_path, output_path)


if __name__ == "__main__":
    # 测试代码
    test_image = Path("arona.png")
    compress_image(test_image, test_image)
    print("图片已压缩并调整尺寸。")

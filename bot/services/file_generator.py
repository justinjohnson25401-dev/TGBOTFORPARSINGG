"""
Excel file generation service for pack extraction
"""
import os
import io
import logging
from typing import Optional, Tuple
import openpyxl
from openpyxl import Workbook

from bot.config import TEMP_FILES_DIR, DEMO_FILE_PATH
from bot.services.gdrive import get_file_as_bytes, ensure_temp_dir
from bot.utils.helpers import generate_filename

logger = logging.getLogger(__name__)


async def generate_pack_file(
        gdrive_file_id: str,
        pack_number: int,
        pack_size: int,
        city: str,
        category: str
) -> Optional[Tuple[str, bytes]]:
    """
    Generate pack file by extracting rows from the main database file

    Args:
        gdrive_file_id: Google Drive file ID of the main database
        pack_number: Pack number (1, 2, 3, etc.)
        pack_size: Number of contacts in pack
        city: City key
        category: Category key

    Returns:
        Tuple of (filename, file_bytes) or None if failed
    """
    try:
        logger.info(f"Generating pack {pack_number} ({pack_size} contacts) for {city}/{category}")

        # Download main file from Google Drive
        file_bytes = await get_file_as_bytes(gdrive_file_id)
        if not file_bytes:
            logger.error("Failed to download file from Google Drive")
            return None

        # Load workbook
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes))
        ws = wb.active

        # Calculate row range for this pack
        # Row 1 is header, data starts from row 2
        start_row = (pack_number - 1) * pack_size + 2  # +2 because row 1 is header
        end_row = start_row + pack_size - 1

        logger.info(f"Extracting rows {start_row} to {end_row}")

        # Create new workbook for the pack
        new_wb = Workbook()
        new_ws = new_wb.active

        # Copy header row
        header_row = list(ws.iter_rows(min_row=1, max_row=1, values_only=True))[0]
        for col_idx, value in enumerate(header_row, 1):
            new_ws.cell(row=1, column=col_idx, value=value)

        # Copy data rows
        row_count = 0
        for row_idx, row in enumerate(
                ws.iter_rows(min_row=start_row, max_row=end_row, values_only=True),
                start=2
        ):
            if row and any(row):  # Skip empty rows
                for col_idx, value in enumerate(row, 1):
                    new_ws.cell(row=row_idx, column=col_idx, value=value)
                row_count += 1

        logger.info(f"Extracted {row_count} rows")

        # Generate filename
        filename = generate_filename(city, category, pack_number, pack_size)

        # Save to bytes
        output = io.BytesIO()
        new_wb.save(output)
        output.seek(0)

        return filename, output.read()

    except Exception as e:
        logger.error(f"Error generating pack file: {e}")
        return None


async def generate_pack_file_to_disk(
        gdrive_file_id: str,
        pack_number: int,
        pack_size: int,
        city: str,
        category: str
) -> Optional[str]:
    """
    Generate pack file and save to disk

    Returns:
        Path to generated file or None
    """
    result = await generate_pack_file(gdrive_file_id, pack_number, pack_size, city, category)
    if not result:
        return None

    filename, file_bytes = result

    ensure_temp_dir()
    file_path = os.path.join(TEMP_FILES_DIR, filename)

    with open(file_path, 'wb') as f:
        f.write(file_bytes)

    return file_path


def get_demo_file() -> Optional[Tuple[str, bytes]]:
    """
    Get demo file for preview

    Returns:
        Tuple of (filename, file_bytes) or None
    """
    try:
        if os.path.exists(DEMO_FILE_PATH):
            with open(DEMO_FILE_PATH, 'rb') as f:
                return "Demo_2GIS_Base.xlsx", f.read()

        # Generate a demo file if not exists
        return generate_demo_file()

    except Exception as e:
        logger.error(f"Error getting demo file: {e}")
        return None


def generate_demo_file() -> Optional[Tuple[str, bytes]]:
    """
    Generate a demo file with masked data

    Returns:
        Tuple of (filename, file_bytes) or None
    """
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "Demo"

        # Headers
        headers = [
            "Название", "Телефон", "Telegram", "VK", "WhatsApp",
            "Email", "Сайт", "Адрес", "Рейтинг", "Отзывы"
        ]
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header)

        # Demo data (masked)
        demo_data = [
            ["Салон красоты 'Элегант'", "+79999999999", "@hidden", "vk.com/hidden", "+79999999999",
             "hidden@email.com", "example.com", "г. Москва, ул. Примерная, 1", "4.8", "150"],
            ["Beauty Studio", "+79999999999", "@hidden", "vk.com/hidden", "+79999999999",
             "hidden@email.com", "example.com", "г. Москва, ул. Примерная, 2", "4.5", "89"],
            ["Студия 'Красота'", "+79999999999", "@hidden", "vk.com/hidden", "+79999999999",
             "hidden@email.com", "example.com", "г. Москва, ул. Примерная, 3", "4.9", "234"],
            ["Nail Art Studio", "+79999999999", "@hidden", "vk.com/hidden", "+79999999999",
             "hidden@email.com", "example.com", "г. Москва, ул. Примерная, 4", "4.7", "112"],
            ["Парикмахерская 'Стиль'", "+79999999999", "@hidden", "vk.com/hidden", "+79999999999",
             "hidden@email.com", "example.com", "г. Москва, ул. Примерная, 5", "4.6", "78"],
        ]

        for row_idx, row_data in enumerate(demo_data, 2):
            for col_idx, value in enumerate(row_data, 1):
                ws.cell(row=row_idx, column=col_idx, value=value)

        # Adjust column widths
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            ws.column_dimensions[column].width = min(max_length + 2, 30)

        # Save to bytes
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        # Also save to disk
        ensure_temp_dir()
        os.makedirs(os.path.dirname(DEMO_FILE_PATH), exist_ok=True)
        with open(DEMO_FILE_PATH, 'wb') as f:
            f.write(output.getvalue())

        output.seek(0)
        return "Demo_2GIS_Base.xlsx", output.read()

    except Exception as e:
        logger.error(f"Error generating demo file: {e}")
        return None


async def get_total_rows_in_file(gdrive_file_id: str) -> int:
    """
    Get total number of data rows in a Google Drive Excel file

    Returns:
        Number of rows (excluding header) or 0 if failed
    """
    try:
        file_bytes = await get_file_as_bytes(gdrive_file_id)
        if not file_bytes:
            return 0

        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True)
        ws = wb.active

        # Count non-empty rows (excluding header)
        row_count = 0
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row and any(row):
                row_count += 1

        return row_count

    except Exception as e:
        logger.error(f"Error counting rows: {e}")
        return 0

import hashlib
import os
import tempfile
from typing import Optional

from langchain_community.document_loaders import CSVLoader, PyPDFLoader, TextLoader
from langchain_core.documents import Document


def get_file_md5_hex(filepath: str) -> Optional[str]:
    """
    计算文件的MD5哈希值，返回十六进制字符串
    :param filepath: 文件的绝对/相对路径
    :return: 成功返回32位MD5十六进制字符串，失败返回None
    """
    if not os.path.exists(filepath):
        print(f"错误：文件 {filepath} 不存在")
        return None

    if not os.path.isfile(filepath):
        print(f"错误：{filepath} 不是有效文件")
        return None

    md5_obj = hashlib.md5()

    chunk_size = 4096
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                md5_obj.update(chunk)

        md5_hex = md5_obj.hexdigest()
        return md5_hex

    except PermissionError:
        print(f"错误：无权限读取文件 {filepath}")
        return None
    except Exception as e:
        print(f"计算MD5失败：{str(e)}")
        return None


def listdir_with_allowed_type(path: str, allowed_types: tuple[str]):
    files = []
    if not os.path.isdir(path):
        print(f"错误：{path} 不是有效目录或不存在")
        return tuple(files)

    for f in os.listdir(path):
        if f.endswith(allowed_types):
            files.append(os.path.join(path, f))

    return tuple(files)


def csv_loader(filepath: str, source_column=None, encoding="utf-8", csv_args=None) -> list[Document]:
    loader = CSVLoader(
        filepath,
        source_column=source_column,
        encoding=encoding,
        csv_args=csv_args,
    )
    return loader.load()


def _has_meaningful_text(docs: list[Document]) -> bool:
    merged = "\n".join((d.page_content or "") for d in docs).strip()
    return len(merged) >= 30


def _pdf_ocr_loader(filepath: str) -> list[Document]:
    try:
        import fitz  # PyMuPDF
        from rapidocr_onnxruntime import RapidOCR
    except Exception:
        return []

    try:
        ocr_engine = RapidOCR()
    except Exception:
        return []

    docs: list[Document] = []
    try:
        with fitz.open(filepath) as pdf:
            for page_index in range(len(pdf)):
                page = pdf[page_index]
                pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    tmp.write(pix.tobytes("png"))
                    image_path = tmp.name

                try:
                    result, _ = ocr_engine(image_path)
                    lines: list[str] = []
                    if result:
                        for item in result:
                            if len(item) >= 2 and item[1]:
                                lines.append(str(item[1]).strip())
                    text = "\n".join([line for line in lines if line]).strip()
                finally:
                    if os.path.exists(image_path):
                        os.remove(image_path)

                if not text:
                    continue

                docs.append(
                    Document(
                        page_content=text,
                        metadata={
                            "source": filepath,
                            "page": page_index + 1,
                            "extract_method": "ocr",
                        },
                    )
                )
    except Exception:
        return []

    return docs


def pdf_loader(filepath: str, passwd=None) -> list[Document]:
    docs = PyPDFLoader(filepath, passwd).load()
    if _has_meaningful_text(docs):
        return docs

    ocr_docs = _pdf_ocr_loader(filepath)
    if ocr_docs:
        return ocr_docs
    return docs


def txt_loader(filepath: str) -> list[Document]:
    try:
        return TextLoader(filepath, encoding="utf-8").load()
    except UnicodeDecodeError:
        return TextLoader(filepath, encoding="gbk").load()

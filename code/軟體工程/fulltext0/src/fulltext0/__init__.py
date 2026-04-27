"""fulltext0 - A lightweight full-text search engine with CJK support."""

import ctypes
import os
import sys
import subprocess
import shutil
from pathlib import Path

__version__ = "0.1.0"

_lib = None

def _get_lib_path():
    lib_dir = Path(__file__).parent
    platform = sys.platform

    if platform == 'win32':
        candidates = [
            lib_dir / "libfulltext0.dll",
            lib_dir / "libfulltext0.pyd",
        ]
    elif platform == 'darwin':
        candidates = [
            lib_dir / "libfulltext0.dylib",
            lib_dir / "libfulltext0.so",
        ]
    else:
        candidates = [
            lib_dir / "libfulltext0.so",
            lib_dir / "libfulltext0.dylib",
        ]

    for p in candidates:
        if p.exists():
            return p
    return None

def _load_lib():
    global _lib
    if _lib is not None:
        return _lib

    lib_path = _get_lib_path()
    if lib_path:
        _lib = ctypes.CDLL(str(lib_path))
        _setup_lib_types(_lib)
        return _lib

    build_lib()

    lib_path = _get_lib_path()
    if lib_path:
        _lib = ctypes.CDLL(str(lib_path))
        _setup_lib_types(_lib)
        return _lib

    raise FileNotFoundError(
        f"Could not find libfulltext0. "
        f"Build failed or platform not supported."
    )

def build_lib():
    pkg_dir = Path(__file__).parent
    fulltext0_c = pkg_dir / "fulltext0.c"
    if not fulltext0_c.exists():
        raise FileNotFoundError(f"Source not found: {fulltext0_c}")

    platform = sys.platform
    cflags = []

    if platform == 'win32':
        lib_name = "libfulltext0.dll"
        lib_path = pkg_dir / lib_name
        # MSVC on Windows
        cflags = ['cl', '/LD', '/EHsc', '/O2',
                  f'/I"{pkg_dir}"', '/Fe:' + str(lib_path),
                  str(fulltext0_c), 'user32.lib', 'kernel32.lib']
    elif platform == 'darwin':
        lib_name = "libfulltext0.dylib"
        lib_path = pkg_dir / lib_name
        cflags = ['clang', '-shared', '-fPIC', '-O2',
                  f'-I{pkg_dir}', '-o', str(lib_path), str(fulltext0_c)]
    else:
        lib_name = "libfulltext0.so"
        lib_path = pkg_dir / lib_name
        cflags = ['gcc', '-shared', '-fPIC', '-O2',
                  f'-I{pkg_dir}', '-o', str(lib_path), str(fulltext0_c)]

    # Try to find a working compiler
    compiler = None
    if platform == 'win32':
        for c in ['cl', 'cl.exe', 'clang-cl']:
            if shutil.which(c):
                compiler = c
                break
    else:
        for c in ['clang', 'gcc', 'cc']:
            if shutil.which(c):
                compiler = c
                break

    if not compiler:
        raise RuntimeError("No C compiler found")

    # Build command
    if platform == 'win32':
        cmd = [compiler] + cflags
    else:
        cmd = [compiler] + cflags

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Fallback: try gcc/clang with common flags
        if platform != 'win32':
            for fallback in [['gcc', '-shared', '-fPIC', '-O2',
                              f'-I{pkg_dir}', '-o', str(lib_path), str(fulltext0_c)],
                             ['clang', '-shared', '-fPIC', '-O2',
                              f'-I{pkg_dir}', '-o', str(lib_path), str(fulltext0_c)]]:
                r = subprocess.run(fallback, capture_output=True, text=True)
                if r.returncode == 0:
                    break
            else:
                raise RuntimeError(f"Build failed: {result.stderr or 'unknown error'}")
        else:
            raise RuntimeError(f"Build failed: {result.stderr or 'unknown error'}")

    # Verify the library was built
    if not lib_path.exists():
        raise RuntimeError(f"Build command succeeded but {lib_path} not created")

    _lib = ctypes.CDLL(str(lib_path))
    _setup_lib_types(_lib)

class _IndexStats(ctypes.Structure):
    _fields_ = [("num_terms", ctypes.c_uint32),
                ("num_docs", ctypes.c_uint32)]

class _QueryResult(ctypes.Structure):
    _fields_ = [("doc_ids", ctypes.POINTER(ctypes.c_uint32)),
                ("count", ctypes.c_uint32),
                ("scores", ctypes.c_void_p)]

def _setup_lib_types(lib):
    lib.ft0_index_open.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    lib.ft0_index_open.restype = ctypes.c_void_p

    lib.ft0_index_close.argtypes = [ctypes.c_void_p]
    lib.ft0_index_close.restype = None

    lib.ft0_index_stats.argtypes = [ctypes.c_void_p, ctypes.POINTER(_IndexStats)]
    lib.ft0_index_stats.restype = ctypes.POINTER(_IndexStats)

    lib.ft0_query_exec.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    lib.ft0_query_exec.restype = ctypes.POINTER(_QueryResult)

    lib.ft0_query_result_free.argtypes = [ctypes.c_void_p]
    lib.ft0_query_result_free.restype = None

    lib.ft0_index_build.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
    lib.ft0_index_build.restype = ctypes.c_int

    lib.ft0_tokenize.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_int)]
    lib.ft0_tokenize.restype = ctypes.POINTER(ctypes.c_char_p)

    lib.ft0_tokenize_free.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.ft0_tokenize_free.restype = None

    lib.ft0_get_line.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                                  ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32,
                                  ctypes.POINTER(ctypes.c_int)]
    lib.ft0_get_line.restype = ctypes.POINTER(ctypes.c_char_p)

    lib.ft0_lines_free.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.ft0_lines_free.restype = None

class IndexStats:
    def __init__(self, num_terms, num_docs):
        self.num_terms = num_terms
        self.num_docs = num_docs
    def __repr__(self):
        return f"IndexStats(terms={self.num_terms}, docs={self.num_docs})"

class Index:
    def __init__(self, idx_path="_index/data.idx", off_path="_index/offsets.bin"):
        lib = _load_lib()
        if isinstance(idx_path, str):
            idx_path = idx_path.encode("utf-8")
        if isinstance(off_path, str):
            off_path = off_path.encode("utf-8")
        self._ptr = lib.ft0_index_open(idx_path, off_path)
        if not self._ptr:
            raise RuntimeError("Failed to open index")

    def close(self):
        if self._ptr:
            _load_lib().ft0_index_close(self._ptr)
            self._ptr = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def stats(self):
        lib = _load_lib()
        s = _IndexStats()
        lib.ft0_index_stats(self._ptr, ctypes.byref(s))
        return IndexStats(s.num_terms, s.num_docs)

    def query(self, query_str):
        lib = _load_lib()
        if isinstance(query_str, str):
            query_str = query_str.encode("utf-8")
        res = lib.ft0_query_exec(self._ptr, query_str)
        if not res:
            return []
        doc_ids = [res.contents.doc_ids[i] for i in range(res.contents.count)]
        lib.ft0_query_result_free(res)
        return doc_ids

    def get_lines(self, corpus_path, doc_ids):
        lib = _load_lib()
        if isinstance(corpus_path, str):
            corpus_path = corpus_path.encode("utf-8")
        arr = (ctypes.c_uint32 * len(doc_ids))(*doc_ids)
        count = ctypes.c_int()
        lines_ptr = lib.ft0_get_line(self._ptr, corpus_path, arr, len(doc_ids), ctypes.byref(count))
        if not lines_ptr:
            return []
        lines = [lines_ptr[i].decode("utf-8") for i in range(count.value)]
        lib.ft0_lines_free(lines_ptr, count.value)
        return lines

def tokenize(line):
    lib = _load_lib()
    if isinstance(line, str):
        line = line.encode("utf-8")
    count = ctypes.c_int()
    tokens_ptr = lib.ft0_tokenize(line, ctypes.byref(count))
    if not tokens_ptr:
        return []
    tokens = [tokens_ptr[i].decode("utf-8") for i in range(count.value)]
    lib.ft0_tokenize_free(tokens_ptr, count.value)
    return tokens

def build(corpus_path="_data/corpus.txt",
          idx_path="_index/data.idx",
          off_path="_index/offsets.bin"):
    lib = _load_lib()
    if isinstance(corpus_path, str):
        corpus_path = corpus_path.encode("utf-8")
    if isinstance(idx_path, str):
        idx_path = idx_path.encode("utf-8")
    if isinstance(off_path, str):
        off_path = off_path.encode("utf-8")
    return lib.ft0_index_build(corpus_path, idx_path, off_path)

__all__ = ["Index", "IndexStats", "tokenize", "build", "__version__"]
#include "fulltext0.h"
#include <errno.h>

/* ═══════════════════════════════════════════════════════════════════════════
 * PART 1: TOKENIZE (shared)
 * ═══════════════════════════════════════════════════════════════════════════ */

int tokenize(const char *line, char out[][MAX_TOKEN_LEN], int max_out)
{
    const unsigned char *p = (const unsigned char *)line;
    int n = 0;

    while (*p && n < max_out) {
        uint32_t cp;
        int len = utf8_decode(p, &cp);
        if (len <= 0) { p++; continue; }

        if (is_cjk(cp)) {
            uint32_t cp2;
            int len2 = 0;
            const unsigned char *q = p + len;
            if (*q) len2 = utf8_decode(q, &cp2);

            if (len2 > 0 && is_cjk(cp2) && n < max_out) {
                int blen = len + len2;
                if (blen < MAX_TOKEN_LEN) {
                    memcpy(out[n], p, blen);
                    out[n][blen] = '\0';
                    n++;
                }
            }

            if (n < max_out && len < MAX_TOKEN_LEN) {
                memcpy(out[n], p, len);
                out[n][len] = '\0';
                n++;
            }
            p += len;
        } else if (is_ascii_alnum((char)cp)) {
            char buf[MAX_TOKEN_LEN];
            int bi = 0;
            while (*p && bi < MAX_TOKEN_LEN-1) {
                uint32_t c2; int l2 = utf8_decode(p, &c2);
                if (l2 != 1 || !is_ascii_alnum((char)c2)) break;
                buf[bi++] = ascii_lower((char)c2);
                p += l2;
            }
            buf[bi] = '\0';
            if (bi > 0 && n < max_out) {
                memcpy(out[n], buf, bi+1);
                n++;
            }
        } else {
            p += (len > 0 ? len : 1);
        }
    }
    return n;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * PART 2: BOOLEAN SET OPERATIONS
 * ═══════════════════════════════════════════════════════════════════════════ */

int intersect(const uint32_t *a, int na,
              const uint32_t *b, int nb,
              uint32_t *res, int max_res)
{
    int i=0, j=0, k=0;
    while (i<na && j<nb && k<max_res) {
        if (a[i] < b[j]) i++;
        else if (a[i] > b[j]) j++;
        else { res[k++] = a[i]; i++; j++; }
    }
    return k;
}

int unite(const uint32_t *a, int na,
          const uint32_t *b, int nb,
          uint32_t *res, int max_res)
{
    int i=0, j=0, k=0;
    while ((i<na || j<nb) && k<max_res) {
        uint32_t va = (i<na) ? a[i] : UINT32_MAX;
        uint32_t vb = (j<nb) ? b[j] : UINT32_MAX;
        if (va < vb) { res[k++]=va; i++; }
        else if (va > vb) { res[k++]=vb; j++; }
        else { res[k++]=va; i++; j++; }
    }
    return k;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * PART 3: CROSS-PLATFORM FILE OPERATIONS
 * ═══════════════════════════════════════════════════════════════════════════ */

#ifdef _WIN32
static HANDLE g_mmap_handle = NULL;

static int win_open(const char *path, int oflag)
{
    DWORD dwDesiredAccess = 0;
    DWORD dwCreationDisposition = OPEN_EXISTING;

    if (oflag & O_RDONLY) dwDesiredAccess |= GENERIC_READ;
    if (oflag & O_WRONLY) dwDesiredAccess |= GENERIC_WRITE;
    if (oflag & O_RDWR) dwDesiredAccess |= (GENERIC_READ | GENERIC_WRITE);

    if (oflag & O_CREAT) dwCreationDisposition = OPEN_ALWAYS;
    if (oflag & O_TRUNC) dwCreationDisposition = CREATE_ALWAYS;

    HANDLE h = CreateFileA(path, dwDesiredAccess, FILE_SHARE_READ,
                           NULL, dwCreationDisposition, FILE_ATTRIBUTE_NORMAL, NULL);
    if (h == INVALID_HANDLE_VALUE) return -1;
    return (int)(intptr_t)h;
}

static int win_close(int fd)
{
    return CloseHandle((HANDLE)(intptr_t)fd) ? 0 : -1;
}

static intptr_t win_read(int fd, void *buf, size_t size)
{
    DWORD bytesRead = 0;
    if (!ReadFile((HANDLE)(intptr_t)fd, buf, (DWORD)size, &bytesRead, NULL))
        return -1;
    return (intptr_t)bytesRead;
}

static intptr_t win_pread(int fd, void *buf, size_t size, uint64_t offset)
{
    OVERLAPPED ov = {0};
    ov.Offset = (DWORD)(offset & 0xFFFFFFFF);
    ov.OffsetHigh = (DWORD)(offset >> 32);
    DWORD bytesRead = 0;
    if (!ReadFile((HANDLE)(intptr_t)fd, buf, (DWORD)size, &bytesRead, &ov))
        return -1;
    return (intptr_t)bytesRead;
}

static void *win_mmap(void *addr, size_t len, int prot, int flags, int fd, uint64_t offset)
{
    DWORD dwProt = 0;
    if (prot & PROT_READ) dwProt = FILE_MAP_READ;
    if (prot & PROT_WRITE) dwProt = FILE_MAP_WRITE;

    HANDLE hMap = CreateFileMappingA((HANDLE)(intptr_t)fd, NULL, dwProt, 0, 0, NULL);
    if (!hMap) return NULL;

    g_mmap_handle = hMap;

    void *p = MapViewOfFile(hMap, dwProt, (DWORD)(offset >> 32), (DWORD)(offset & 0xFFFFFFFF), len);
    if (!p) {
        CloseHandle(hMap);
        g_mmap_handle = NULL;
        return NULL;
    }
    return p;
}

static int win_munmap(void *addr, size_t len)
{
    (void)len;
    BOOL ok = UnmapViewOfFile(addr);
    if (g_mmap_handle) {
        CloseHandle(g_mmap_handle);
        g_mmap_handle = NULL;
    }
    return ok ? 0 : -1;
}

static int win_madvise(void *addr, size_t len, int advice)
{
    (void)addr; (void)len; (void)advice;
    return 0;
}

#define PLAT_OPEN win_open
#define PLAT_CLOSE win_close
#define PLAT_READ win_read
#define PLAT_PREAD win_pread
#define PLAT_MMAP win_mmap
#define PLAT_MUNMAP win_munmap
#define PLAT_MADVISE win_madvise

#else
#define PLAT_OPEN open
#define PLAT_CLOSE close
#define PLAT_READ read
#define PLAT_PREAD pread
#define PLAT_MMAP mmap
#define PLAT_MUNMAP munmap
#define PLAT_MADVISE madvise
#endif

/* ═══════════════════════════════════════════════════════════════════════════
 * PART 4: INDEX BUILD
 * ═══════════════════════════════════════════════════════════════════════════ */

static TermEntry g_terms[MAX_TERMS];
static PostingList g_posts[MAX_TERMS];
static int g_num_terms = 0;

#define HASH_SIZE (1<<17)
static int32_t g_hash[HASH_SIZE];

static uint32_t hash_term(const char *s)
{
    uint32_t h = 2166136261u;
    while (*s) { h ^= (unsigned char)*s++; h *= 16777619u; }
    return h;
}

static int find_or_insert(const char *term)
{
    uint32_t h = hash_term(term) & (HASH_SIZE-1);
    for (;;) {
        if (g_hash[h] == -1) {
            if (g_num_terms >= MAX_TERMS) { fprintf(stderr,"Too many terms\n"); exit(1); }
            int idx = g_num_terms++;
            g_hash[h] = idx;
            size_t tl = strlen(term);
            if (tl >= MAX_TOKEN_LEN) tl = MAX_TOKEN_LEN-1;
            memcpy(g_terms[idx].term, term, tl);
            g_terms[idx].term[tl] = '\0';
            g_terms[idx].post_offset = 0;
            g_terms[idx].post_count = 0;
            g_terms[idx].post_byte_len = 0;
            g_posts[idx].doc_ids = NULL;
            g_posts[idx].count = 0;
            g_posts[idx].cap = 0;
            return idx;
        }
        if (strcmp(g_terms[g_hash[h]].term, term) == 0) return g_hash[h];
        h = (h+1) & (HASH_SIZE-1);
    }
}

static void add_posting(int ti, uint32_t doc_id)
{
    PostingList *pl = &g_posts[ti];
    if (pl->count > 0 && pl->doc_ids[pl->count-1] == doc_id) return;
    if (pl->count >= pl->cap) {
        pl->cap = pl->cap ? pl->cap*2 : 8;
        pl->doc_ids = realloc(pl->doc_ids, pl->cap * sizeof(uint32_t));
        if (!pl->doc_ids) { fprintf(stderr,"OOM\n"); exit(1); }
    }
    pl->doc_ids[pl->count++] = doc_id;
}

static size_t encode_postings(unsigned char *out, const uint32_t *ids, uint32_t count)
{
    size_t pos = 0;
    uint32_t prev = 0;
    for (uint32_t i = 0; i < count; i++) {
        uint32_t delta = ids[i] - prev;
        pos += varint_encode(out + pos, delta);
        prev = ids[i];
    }
    return pos;
}

static void write_index(const char *idx_path, const char *off_path,
                        uint32_t num_docs, const uint64_t *doc_offsets)
{
    mkdir("_index", 0755);

    {
        FILE *of = fopen(off_path, "wb");
        if (!of) { perror("fopen offsets.bin"); exit(1); }
        if (fwrite(doc_offsets, sizeof(uint64_t), num_docs, of) != num_docs) {
            fprintf(stderr,"short write offsets\n"); exit(1);
        }
        fclose(of);
        printf("Offsets written: %s (%u entries, %zu bytes)\n",
               off_path, num_docs, (size_t)num_docs * sizeof(uint64_t));
    }

    size_t post_cap = 0;
    for (int i = 0; i < g_num_terms; i++)
        post_cap += g_posts[i].count * VARINT_MAX + 1;

    unsigned char *post_buf = malloc(post_cap);
    if (!post_buf) { fprintf(stderr,"OOM\n"); exit(1); }
    size_t pb_pos = 0;

    size_t term_cap = 0;
    for (int i = 0; i < g_num_terms; i++)
        term_cap += 14 + strlen(g_terms[i].term);

    unsigned char *term_buf = malloc(term_cap + 64);
    if (!term_buf) { fprintf(stderr,"OOM\n"); exit(1); }
    size_t tb_pos = 0;

    for (int i = 0; i < g_num_terms; i++) {
        g_terms[i].post_offset = (uint32_t)pb_pos;
        g_terms[i].post_count = g_posts[i].count;
        size_t blen = encode_postings(post_buf + pb_pos, g_posts[i].doc_ids, g_posts[i].count);
        g_terms[i].post_byte_len = (uint32_t)blen;
        pb_pos += blen;

        uint16_t tlen = (uint16_t)strlen(g_terms[i].term);
        term_buf[tb_pos] = tlen & 0xFF;
        term_buf[tb_pos+1] = (tlen >> 8) & 0xFF;
        tb_pos += 2;
        memcpy(term_buf + tb_pos, g_terms[i].term, tlen);
        tb_pos += tlen;

        uint32_t fields[3] = {
            g_terms[i].post_offset,
            g_terms[i].post_count,
            g_terms[i].post_byte_len
        };
        for (int f = 0; f < 3; f++) {
            term_buf[tb_pos+0] = fields[f] & 0xFF;
            term_buf[tb_pos+1] = (fields[f] >> 8) & 0xFF;
            term_buf[tb_pos+2] = (fields[f] >> 16) & 0xFF;
            term_buf[tb_pos+3] = (fields[f] >> 24) & 0xFF;
            tb_pos += 4;
        }
    }

    uint32_t term_block_start = 1;
    uint32_t term_blocks = (uint32_t)((tb_pos + BLOCK_SIZE-1) / BLOCK_SIZE);
    uint32_t post_block_start = term_block_start + term_blocks;

    FILE *fp = fopen(idx_path, "wb");
    if (!fp) { perror("fopen index"); exit(1); }

    unsigned char hdr[BLOCK_SIZE];
    memset(hdr, 0, BLOCK_SIZE);
    uint32_t magic = IDX_MAGIC, version = IDX_VERSION;
    memcpy(hdr+ 0, &magic, 4);
    memcpy(hdr+ 4, &version, 4);
    memcpy(hdr+ 8, &g_num_terms, 4);
    memcpy(hdr+12, &num_docs, 4);
    memcpy(hdr+16, &term_block_start, 4);
    memcpy(hdr+20, &post_block_start, 4);
    if (fwrite(hdr, 1, BLOCK_SIZE, fp) != BLOCK_SIZE) {
        fprintf(stderr,"short write hdr\n"); exit(1);
    }

    size_t written = 0;
    while (written < tb_pos) {
        unsigned char blk[BLOCK_SIZE];
        size_t chunk = tb_pos - written;
        if (chunk > BLOCK_SIZE) chunk = BLOCK_SIZE;
        memcpy(blk, term_buf + written, chunk);
        if (chunk < BLOCK_SIZE) memset(blk + chunk, 0, BLOCK_SIZE - chunk);
        if (fwrite(blk, 1, BLOCK_SIZE, fp) != BLOCK_SIZE) {
            fprintf(stderr,"short write term\n"); exit(1);
        }
        written += chunk;
    }

    written = 0;
    while (written < pb_pos) {
        unsigned char blk[BLOCK_SIZE];
        size_t chunk = pb_pos - written;
        if (chunk > BLOCK_SIZE) chunk = BLOCK_SIZE;
        memcpy(blk, post_buf + written, chunk);
        if (chunk < BLOCK_SIZE) memset(blk + chunk, 0, BLOCK_SIZE - chunk);
        if (fwrite(blk, 1, BLOCK_SIZE, fp) != BLOCK_SIZE) {
            fprintf(stderr,"short write post\n"); exit(1);
        }
        written += chunk;
    }

    fclose(fp);
    free(term_buf);
    free(post_buf);

    long fsize = 0;
    { FILE *f2 = fopen(idx_path,"rb"); if (f2) { fseek(f2,0,SEEK_END); fsize=ftell(f2); fclose(f2); } }

    size_t raw_post = 0;
    for (int i = 0; i < g_num_terms; i++) raw_post += g_posts[i].count * 4;

    printf("Index written : %s\n", idx_path);
    printf(" docs : %u\n", num_docs);
    printf(" terms : %d\n", g_num_terms);
    printf(" file size : %ld bytes (%ld blocks)\n", fsize, fsize/BLOCK_SIZE);
    printf(" posting raw : %zu bytes\n", raw_post);
    printf(" posting zip : %zu bytes (%.1f%% of raw)\n",
           pb_pos, raw_post ? 100.0*pb_pos/raw_post : 0.0);
}

void ft0_index_reset(void)
{
    memset(g_hash, -1, sizeof(g_hash));
    g_num_terms = 0;
    for (int i = 0; i < MAX_TERMS; i++) {
        g_posts[i].doc_ids = NULL;
        g_posts[i].count = 0;
        g_posts[i].cap = 0;
    }
}

void ft0_index_free(void)
{
    for (int i = 0; i < g_num_terms; i++) free(g_posts[i].doc_ids);
    g_num_terms = 0;
}

int ft0_index_build(const char *corpus_path,
                    const char *idx_path,
                    const char *off_path)
{
    ft0_index_reset();

    FILE *fp = fopen(corpus_path, "r");
    if (!fp) { perror("fopen corpus"); return -1; }

    uint32_t off_cap = 4096;
    uint64_t *doc_offsets = malloc(off_cap * sizeof(uint64_t));
    if (!doc_offsets) { fprintf(stderr,"OOM\n"); fclose(fp); return -1; }

    char line[4096];
    char tokens[MAX_TOKENS][MAX_TOKEN_LEN];
    uint32_t doc_id = 0;

    while (1) {
        int64_t line_offset = (int64_t)ftell(fp);
        if (line_offset < 0) break;

        if (!fgets(line, sizeof(line), fp)) break;

        int ll = (int)strlen(line);
        while (ll > 0 && (line[ll-1]=='\n'||line[ll-1]=='\r')) line[--ll] = '\0';
        if (ll == 0) continue;

        if (doc_id >= off_cap) {
            off_cap *= 2;
            doc_offsets = realloc(doc_offsets, off_cap * sizeof(uint64_t));
            if (!doc_offsets) { fprintf(stderr,"OOM\n"); fclose(fp); return -1; }
        }
        doc_offsets[doc_id] = (uint64_t)line_offset;

        int ntok = tokenize(line, tokens, MAX_TOKENS);
        for (int t = 0; t < ntok; t++) {
            int idx = find_or_insert(tokens[t]);
            add_posting(idx, doc_id);
        }
        doc_id++;

        if (doc_id % 100 == 0)
            fprintf(stderr, "\r Indexed %u docs, %d terms ...", doc_id, g_num_terms);
    }
    fprintf(stderr, "\n");
    fclose(fp);

    write_index(idx_path, off_path, doc_id, doc_offsets);

    free(doc_offsets);
    ft0_index_free();
    return 0;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * PART 5: QUERY ENGINE
 * ═══════════════════════════════════════════════════════════════════════════ */

#define QHASH_SIZE (1<<17)
static int32_t g_qhash[QHASH_SIZE];

static uint32_t hash_str(const char *s)
{
    uint32_t h = 2166136261u;
    while (*s) { h ^= (unsigned char)*s++; h *= 16777619u; }
    return h;
}

static void qhash_build(const TermEntry *terms, uint32_t n)
{
    memset(g_qhash, -1, sizeof(g_qhash));
    for (uint32_t i = 0; i < n; i++) {
        uint32_t h = hash_str(terms[i].term) & (QHASH_SIZE-1);
        while (g_qhash[h] != -1) h = (h+1) & (QHASH_SIZE-1);
        g_qhash[h] = (int32_t)i;
    }
}

static int qhash_lookup(const TermEntry *terms, const char *term)
{
    uint32_t h = hash_str(term) & (QHASH_SIZE-1);
    while (g_qhash[h] != -1) {
        if (strcmp(terms[g_qhash[h]].term, term) == 0) return g_qhash[h];
        h = (h+1) & (QHASH_SIZE-1);
    }
    return -1;
}

typedef struct {
    TermEntry *terms;
    uint32_t num_terms;
    uint32_t num_docs;
    int post_fd;
    unsigned char *post_mmap;
    size_t post_mmap_len;
    uint32_t post_block_start;
    uint64_t *doc_offsets;
} Index;

static int index_open(Index *idx, const char *idx_path, const char *off_path)
{
    memset(idx, 0, sizeof(*idx));

    idx->post_fd = PLAT_OPEN(idx_path, O_RDONLY);
    if (idx->post_fd < 0) { perror("open index"); return -1; }

    unsigned char hdr[BLOCK_SIZE];
    if (PLAT_READ(idx->post_fd, hdr, BLOCK_SIZE) != BLOCK_SIZE) {
        fprintf(stderr,"Short header\n"); PLAT_CLOSE(idx->post_fd); return -1;
    }

    uint32_t magic; memcpy(&magic, hdr, 4);
    if (magic != IDX_MAGIC) {
        fprintf(stderr,"Bad magic 0x%08X (expected 0x%08X)\n", magic, IDX_MAGIC);
        fprintf(stderr,"Please re-run ./index to rebuild with the new format.\n");
        PLAT_CLOSE(idx->post_fd); return -1;
    }

    uint32_t term_block_start;
    memcpy(&idx->num_terms, hdr+ 8, 4);
    memcpy(&idx->num_docs, hdr+12, 4);
    memcpy(&term_block_start, hdr+16, 4);
    memcpy(&idx->post_block_start,hdr+20, 4);

    idx->terms = malloc(idx->num_terms * sizeof(TermEntry));
    if (!idx->terms) { fprintf(stderr,"OOM\n"); PLAT_CLOSE(idx->post_fd); return -1; }

    uint32_t term_bytes = (idx->post_block_start - term_block_start) * BLOCK_SIZE;
    unsigned char *tbuf = malloc(term_bytes);
    if (!tbuf) { fprintf(stderr,"OOM\n"); free(idx->terms); PLAT_CLOSE(idx->post_fd); return -1; }

    off_t toff = (off_t)term_block_start * BLOCK_SIZE;
    if (PLAT_PREAD(idx->post_fd, tbuf, term_bytes, toff) != (ssize_t)term_bytes) {
        fprintf(stderr,"Short term table read\n");
    }

    size_t pos = 0;
    for (uint32_t i = 0; i < idx->num_terms; i++) {
        if (pos + 2 > term_bytes) break;
        uint16_t tlen; memcpy(&tlen, tbuf+pos, 2); pos += 2;
        if (pos + tlen > term_bytes) break;
        memcpy(idx->terms[i].term, tbuf+pos, tlen);
        idx->terms[i].term[tlen] = '\0';
        pos += tlen;
        memcpy(&idx->terms[i].post_offset, tbuf+pos, 4); pos += 4;
        memcpy(&idx->terms[i].post_count, tbuf+pos, 4); pos += 4;
        memcpy(&idx->terms[i].post_byte_len, tbuf+pos, 4); pos += 4;
    }
    free(tbuf);

    qhash_build(idx->terms, idx->num_terms);

    {
#ifdef _WIN32
        LARGE_INTEGER li;
        li.QuadPart = 0;
        SetFilePointerEx((HANDLE)(intptr_t)idx->post_fd, li, NULL, FILE_BEGIN);
        DWORD size = GetFileSize((HANDLE)(intptr_t)idx->post_fd, NULL);
        uint64_t post_start = (uint64_t)idx->post_block_start * BLOCK_SIZE;
        idx->post_mmap_len = (size_t)(size - post_start);
        if (idx->post_mmap_len > 0) {
            idx->post_mmap = PLAT_MMAP(NULL, idx->post_mmap_len, PROT_READ, MAP_PRIVATE, idx->post_fd, post_start);
            if (idx->post_mmap == MAP_FAILED || idx->post_mmap == NULL) {
                fprintf(stderr, "mmap posting failed\n");
                idx->post_mmap = NULL;
            }
        }
#else
        struct stat st;
        if (fstat(idx->post_fd, &st) < 0) { perror("fstat"); return -1; }
        long post_start = (long)idx->post_block_start * BLOCK_SIZE;
        idx->post_mmap_len = (size_t)(st.st_size - post_start);
        if (idx->post_mmap_len > 0) {
            idx->post_mmap = PLAT_MMAP(NULL, idx->post_mmap_len, PROT_READ, MAP_PRIVATE, idx->post_fd, post_start);
            if (idx->post_mmap == MAP_FAILED) {
                perror("mmap posting"); idx->post_mmap = NULL;
            } else {
                PLAT_MADVISE(idx->post_mmap, idx->post_mmap_len, MADV_WILLNEED);
            }
        }
#endif
    }

    {
        FILE *of = fopen(off_path, "rb");
        if (!of) {
            fprintf(stderr,"Warning: cannot open %s – will scan corpus for each result\n", off_path);
            idx->doc_offsets = NULL;
        } else {
            idx->doc_offsets = malloc(idx->num_docs * sizeof(uint64_t));
            if (!idx->doc_offsets) { fprintf(stderr,"OOM\n"); fclose(of); return -1; }
            if (fread(idx->doc_offsets, sizeof(uint64_t), idx->num_docs, of) != idx->num_docs) {
                fprintf(stderr,"Short offsets read\n");
            }
            fclose(of);
        }
    }

    return 0;
}

static void index_close(Index *idx)
{
    if (idx->post_mmap)
        PLAT_MUNMAP(idx->post_mmap, idx->post_mmap_len);
    if (idx->post_fd >= 0) PLAT_CLOSE(idx->post_fd);
    free(idx->terms);
    free(idx->doc_offsets);
}

static uint32_t *decode_posting(Index *idx, int ti, uint32_t *count_out)
{
    uint32_t count = idx->terms[ti].post_count;
    uint32_t offset = idx->terms[ti].post_offset;
    uint32_t blen = idx->terms[ti].post_byte_len;
    *count_out = count;
    if (count == 0 || !idx->post_mmap) return NULL;

    uint32_t *buf = malloc(count * sizeof(uint32_t));
    if (!buf) { fprintf(stderr,"OOM\n"); return NULL; }

    const unsigned char *p = idx->post_mmap + offset;
    const unsigned char *end = p + blen;
    uint32_t prev = 0;
    for (uint32_t i = 0; i < count && p < end; i++) {
        uint32_t delta;
        int n = varint_decode(p, &delta);
        if (n < 0) break;
        prev += delta;
        buf[i] = prev;
        p += n;
    }
    return buf;
}

static void fetch_line(FILE *corp, const Index *idx,
                       uint32_t doc_id, char *line, size_t line_cap)
{
    if (idx->doc_offsets) {
        fseek(corp, (long)idx->doc_offsets[doc_id], SEEK_SET);
        if (fgets(line, (int)line_cap, corp)) {
            int ll = (int)strlen(line);
            while (ll > 0 && (line[ll-1]=='\n'||line[ll-1]=='\r')) line[--ll]='\0';
        }
    } else {
        rewind(corp);
        uint32_t cur = 0;
        while (fgets(line, (int)line_cap, corp)) {
            if (cur++ == doc_id) {
                int ll=(int)strlen(line);
                while(ll>0&&(line[ll-1]=='\n'||line[ll-1]=='\r')) line[--ll]='\0';
                return;
            }
        }
    }
}

int ft0_query_exec_to_file(void *idx_ptr, const char *query_str,
                           const char *corpus_path,
                           FILE *out_fp)
{
    Index *idx = (Index *)idx_ptr;
    char qtoks[MAX_TOKENS][MAX_TOKEN_LEN];
    int nq = tokenize(query_str, qtoks, MAX_TOKENS);
    if (nq == 0) {
        fprintf(out_fp, "No tokens in query.\n");
        return 0;
    }

    char utoks[MAX_TOKENS][MAX_TOKEN_LEN];
    int nu = 0;
    for (int i = 0; i < nq; i++) {
        int dup = 0;
        for (int j = 0; j < nu; j++)
            if (strcmp(utoks[j], qtoks[i])==0) { dup=1; break; }
        if (!dup) { memcpy(utoks[nu++], qtoks[i], MAX_TOKEN_LEN); }
    }

    uint32_t *plists[MAX_TOKENS];
    uint32_t pcount[MAX_TOKENS];
    int valid[MAX_TOKENS];
    int nvalid = 0;

    for (int i = 0; i < nu; i++) {
        int ti = qhash_lookup(idx->terms, utoks[i]);
        if (ti < 0) {
            fprintf(stderr, "Term not found: '%s'\n", utoks[i]);
            plists[i] = NULL; pcount[i] = 0;
        } else {
            plists[i] = decode_posting(idx, ti, &pcount[i]);
            valid[nvalid++] = i;
        }
    }

    if (nvalid == 0) {
        fprintf(out_fp, "No matching documents.\n");
        return 0;
    }

    for (int a = 0; a < nvalid-1; a++)
        for (int b = a+1; b < nvalid; b++)
            if (pcount[valid[a]] > pcount[valid[b]]) {
                int tmp = valid[a]; valid[a] = valid[b]; valid[b] = tmp;
            }

#define MAX_RESULT 65536
    uint32_t *result = malloc(MAX_RESULT * sizeof(uint32_t));
    if (!result) { fprintf(stderr,"OOM\n"); return -1; }

    int first = valid[0];
    uint32_t rcount = pcount[first] < MAX_RESULT ? pcount[first] : MAX_RESULT;
    memcpy(result, plists[first], rcount * sizeof(uint32_t));

    for (int k = 1; k < nvalid && rcount > 0; k++) {
        int vi = valid[k];
        uint32_t *tmp = malloc(rcount * sizeof(uint32_t));
        if (!tmp) { fprintf(stderr,"OOM\n"); break; }
        rcount = (uint32_t)intersect(result, (int)rcount,
                                     plists[vi], (int)pcount[vi],
                                     tmp, (int)rcount);
        memcpy(result, tmp, rcount * sizeof(uint32_t));
        free(tmp);
    }

    FILE *corp = fopen(corpus_path, "r");
    if (!corp) { perror("fopen corpus"); free(result); return -1; }

    char line[4096], lower_line[4096];
    int found = 0;

    fprintf(out_fp, "Results for query: \"%s\"\n", query_str);
    fprintf(out_fp, "────────────────────────────────────────\n");

    for (uint32_t ri = 0; ri < rcount; ri++) {
        uint32_t doc_id = result[ri];
        fetch_line(corp, idx, doc_id, line, sizeof(line));

        int pass = 1;
        int ll = (int)strlen(line);
        for (int j = 0; j < ll; j++) lower_line[j] = ascii_lower(line[j]);
        lower_line[ll] = '\0';

        for (int i = 0; i < nu && pass; i++) {
            const char *tok = utoks[i];
            uint32_t cp0 = 0;
            utf8_decode((const unsigned char*)tok, &cp0);
            if (cp0 < 0x80) {
                if (!strstr(lower_line, tok)) pass = 0;
            } else {
                if (!strstr(line, tok)) pass = 0;
            }
        }

        if (pass) {
            fprintf(out_fp, "[%u] %s\n", doc_id+1, line);
            found++;
        }
    }
    fclose(corp);

    fprintf(out_fp, "────────────────────────────────────────\n");
    fprintf(out_fp, "Found %d document(s).\n", found);

    free(result);
    for (int i = 0; i < nu; i++) free(plists[i]);
    return found;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * PART 6: PYTHON CTYPES API
 * ═══════════════════════════════════════════════════════════════════════════ */

void *ft0_index_open(const char *idx_path, const char *off_path)
{
    Index *idx = malloc(sizeof(Index));
    if (!idx) return NULL;
    if (index_open(idx, idx_path, off_path) != 0) {
        free(idx);
        return NULL;
    }
    return idx;
}

void ft0_index_close(void *idx_ptr)
{
    if (idx_ptr) {
        index_close((Index *)idx_ptr);
        free(idx_ptr);
    }
}

IndexStats *ft0_index_stats(void *idx_ptr, IndexStats *out)
{
    Index *idx = (Index *)idx_ptr;
    if (!idx || !out) return NULL;
    out->num_terms = idx->num_terms;
    out->num_docs = idx->num_docs;
    return out;
}

QueryResult *ft0_query_exec(void *idx_ptr, const char *query_str)
{
    Index *idx = (Index *)idx_ptr;
    if (!idx) return NULL;

    char qtoks[MAX_TOKENS][MAX_TOKEN_LEN];
    int nq = tokenize(query_str, qtoks, MAX_TOKENS);
    if (nq == 0) return NULL;

    char utoks[MAX_TOKENS][MAX_TOKEN_LEN];
    int nu = 0;
    for (int i = 0; i < nq; i++) {
        int dup = 0;
        for (int j = 0; j < nu; j++)
            if (strcmp(utoks[j], qtoks[i])==0) { dup=1; break; }
        if (!dup) { memcpy(utoks[nu++], qtoks[i], MAX_TOKEN_LEN); }
    }

    uint32_t *plists[MAX_TOKENS];
    uint32_t pcount[MAX_TOKENS];
    int valid[MAX_TOKENS];
    int nvalid = 0;

    for (int i = 0; i < nu; i++) {
        int ti = qhash_lookup(idx->terms, utoks[i]);
        if (ti < 0) {
            plists[i] = NULL; pcount[i] = 0;
        } else {
            plists[i] = decode_posting(idx, ti, &pcount[i]);
            valid[nvalid++] = i;
        }
    }

    if (nvalid == 0) {
        QueryResult *res = malloc(sizeof(QueryResult));
        if (res) { res->doc_ids = NULL; res->count = 0; res->scores = NULL; }
        return res;
    }

    for (int a = 0; a < nvalid-1; a++)
        for (int b = a+1; b < nvalid; b++)
            if (pcount[valid[a]] > pcount[valid[b]]) {
                int tmp = valid[a]; valid[a] = valid[b]; valid[b] = tmp;
            }

#define MAX_RESULT 65536
    uint32_t *result = malloc(MAX_RESULT * sizeof(uint32_t));
    if (!result) return NULL;

    int first = valid[0];
    uint32_t rcount = pcount[first] < MAX_RESULT ? pcount[first] : MAX_RESULT;
    memcpy(result, plists[first], rcount * sizeof(uint32_t));

    for (int k = 1; k < nvalid && rcount > 0; k++) {
        int vi = valid[k];
        uint32_t *tmp = malloc(rcount * sizeof(uint32_t));
        if (!tmp) break;
        rcount = (uint32_t)intersect(result, (int)rcount,
                                     plists[vi], (int)pcount[vi],
                                     tmp, (int)rcount);
        memcpy(result, tmp, rcount * sizeof(uint32_t));
        free(tmp);
    }

    for (int i = 0; i < nu; i++) free(plists[i]);

    QueryResult *res = malloc(sizeof(QueryResult));
    if (res) {
        res->doc_ids = result;
        res->count = rcount;
        res->scores = NULL;
    } else {
        free(result);
    }
    return res;
}

void ft0_query_result_free(QueryResult *res)
{
    if (res) {
        free(res->doc_ids);
        free(res->scores);
        free(res);
    }
}

char **ft0_tokenize(const char *line, int *out_count)
{
    char tokens[MAX_TOKENS][MAX_TOKEN_LEN];
    int n = tokenize(line, tokens, MAX_TOKENS);
    char **result = malloc(n * sizeof(char *));
    if (!result) { *out_count = 0; return NULL; }
    for (int i = 0; i < n; i++) {
        result[i] = strdup(tokens[i]);
    }
    *out_count = n;
    return result;
}

void ft0_tokenize_free(char **tokens, int count)
{
    for (int i = 0; i < count; i++) free(tokens[i]);
    free(tokens);
}

char **ft0_get_line(void *idx_ptr, const char *corpus_path,
                    uint32_t *doc_ids, uint32_t count,
                    int *out_count)
{
    Index *idx = (Index *)idx_ptr;
    if (!idx || !doc_ids) { *out_count = 0; return NULL; }

    char **lines = malloc(count * sizeof(char *));
    if (!lines) { *out_count = 0; return NULL; }

    FILE *corp = fopen(corpus_path, "r");
    if (!corp) {
        free(lines);
        *out_count = 0;
        return NULL;
    }

    char line[4096];
    for (uint32_t i = 0; i < count; i++) {
        fetch_line(corp, idx, doc_ids[i], line, sizeof(line));
        lines[i] = strdup(line);
    }

    fclose(corp);
    *out_count = (int)count;
    return lines;
}

void ft0_lines_free(char **lines, int count)
{
    for (int i = 0; i < count; i++) free(lines[i]);
    free(lines);
}
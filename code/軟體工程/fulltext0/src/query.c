#include "fulltext0.h"

int main(int argc, char *argv[])
{
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <query> [corpus] [index] [offsets]\n", argv[0]);
        return 1;
    }
    const char *query_str = argv[1];
    const char *corpus = (argc>=3) ? argv[2] : CORPUS_PATH;
    const char *idx_path = (argc>=4) ? argv[3] : INDEX_PATH;
    const char *off_path = (argc>=5) ? argv[4] : OFFSET_PATH;

    void *idx = ft0_index_open(idx_path, off_path);
    if (!idx) {
        fprintf(stderr, "Failed to open index: %s\n", idx_path);
        return 1;
    }

    int result = ft0_query_exec_to_file(idx, query_str, corpus, stdout);

    ft0_index_close(idx);
    return (result < 0) ? 1 : 0;
}
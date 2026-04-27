#include "fulltext0.h"

int main(int argc, char *argv[])
{
    const char *corpus = (argc >= 2) ? argv[1] : CORPUS_PATH;
    const char *idx_path = (argc >= 3) ? argv[2] : INDEX_PATH;
    const char *off_path = (argc >= 4) ? argv[3] : OFFSET_PATH;

    return ft0_index_build(corpus, idx_path, off_path);
}
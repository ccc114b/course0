import fulltext0
fulltext0.build("_data/corpus.txt")
with fulltext0.Index() as idx:
    doc_ids = idx.query("框架")
    lines = idx.get_lines("_data/corpus.txt", doc_ids)
for line in lines:
    print(line)
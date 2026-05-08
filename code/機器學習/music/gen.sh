set -x

# 確保 music 資料夾存在，若不存在則建立
if [ ! -d "music" ]; then
    mkdir music
    echo "已建立 music/ 資料夾"
fi

# 迴圈產生 100 首歌
for i in {1..100}
do
    echo "正在產生第 $i 首歌..."
    python musicgen.py > "music/$i.txt"
done

echo "完成！已成功產生 100 首歌，存放在 music/ 資料夾中。"